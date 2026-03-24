"""Fetch latest GFS wind data from NOAA NOMADS and convert to gfs.json format."""

import json
import sys
import tempfile
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import eccodes
except ImportError:
    sys.exit("eccodes is required: pip install eccodes")

NOMADS_URL = (
    "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_1p00.pl"
    "?file=gfs.t{cycle:02d}z.pgrb2.1p00.f000"
    "&lev_10_m_above_ground=on"
    "&var_UGRD=on&var_VGRD=on"
    "&dir=%2Fgfs.{date}%2F{cycle:02d}%2Fatmos"
)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "gfs.json"


def latest_cycle():
    """Determine the most recent GFS cycle that should be available."""
    now = datetime.now(timezone.utc)
    for hours_back in range(0, 24, 6):
        candidate = now - timedelta(hours=hours_back + 4)
        cycle = (candidate.hour // 6) * 6
        cycle_time = candidate.replace(hour=cycle, minute=0, second=0, microsecond=0)
        if now >= cycle_time + timedelta(hours=4):
            return cycle_time
    return None


def download_grib(cycle_time):
    """Download filtered GRIB2 from NOMADS."""
    url = NOMADS_URL.format(
        date=cycle_time.strftime("%Y%m%d"),
        cycle=cycle_time.hour,
    )
    print(f"Downloading: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "wind-js-updater/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def grib2_to_json(grib_data):
    """Convert GRIB2 binary data to gfs.json format using eccodes."""
    messages = []

    with tempfile.NamedTemporaryFile(suffix=".grib2") as tmp:
        tmp.write(grib_data)
        tmp.flush()

        with open(tmp.name, "rb") as f:
            while True:
                msgid = eccodes.codes_grib_new_from_file(f)
                if msgid is None:
                    break
                try:
                    msg = extract_message(msgid)
                    if msg:
                        messages.append(msg)
                finally:
                    eccodes.codes_release(msgid)

    return messages


def extract_message(msgid):
    """Extract header and data from a single GRIB2 message."""
    param_cat = eccodes.codes_get(msgid, "parameterCategory")
    param_num = eccodes.codes_get(msgid, "parameterNumber")

    # Only U-component (2,2) and V-component (2,3) of wind
    if param_cat != 2 or param_num not in (2, 3):
        return None

    param_names = {
        2: "U-component_of_wind",
        3: "V-component_of_wind",
    }

    nx = eccodes.codes_get(msgid, "Ni")
    ny = eccodes.codes_get(msgid, "Nj")
    ref_time = eccodes.codes_get_string(msgid, "dataDate")
    ref_hour = eccodes.codes_get(msgid, "dataTime") // 100
    forecast_time = eccodes.codes_get(msgid, "forecastTime")

    date_str = (
        f"{ref_time[:4]}-{ref_time[4:6]}-{ref_time[6:8]}"
        f"T{ref_hour:02d}:00:00.000Z"
    )

    surface1_type = eccodes.codes_get(msgid, "typeOfFirstFixedSurface")
    surface1_value = eccodes.codes_get(msgid, "scaledValueOfFirstFixedSurface")

    surface1_names = {
        100: "Isobaric surface",
        103: "Specified height level above ground",
    }

    values = eccodes.codes_get_values(msgid)
    rounded = [round(float(v), 2) for v in values]

    header = {
        "discipline": 0,
        "disciplineName": "Meteorological products",
        "gribEdition": 2,
        "center": eccodes.codes_get(msgid, "centre"),
        "centerName": "US National Weather Service - NCEP(WMC)",
        "subcenter": eccodes.codes_get(msgid, "subCentre"),
        "refTime": date_str,
        "significanceOfRT": 1,
        "significanceOfRTName": "Start of forecast",
        "productStatus": 0,
        "productStatusName": "Operational products",
        "productType": 1,
        "productTypeName": "Forecast products",
        "productDefinitionTemplate": 0,
        "productDefinitionTemplateName": "Analysis/forecast at horizontal level/layer at a point in time",
        "parameterCategory": param_cat,
        "parameterCategoryName": "Momentum",
        "parameterNumber": param_num,
        "parameterNumberName": param_names[param_num],
        "parameterUnit": "m.s-1",
        "genProcessType": eccodes.codes_get(msgid, "typeOfGeneratingProcess"),
        "genProcessTypeName": "Forecast",
        "forecastTime": forecast_time,
        "surface1Type": surface1_type,
        "surface1TypeName": surface1_names.get(surface1_type, "Unknown"),
        "surface1Value": surface1_value,
        "surface2Type": 255,
        "surface2TypeName": "Missing",
        "surface2Value": 0,
        "gridDefinitionTemplate": 0,
        "gridDefinitionTemplateName": "Latitude_Longitude",
        "numberPoints": nx * ny,
        "shape": 6,
        "shapeName": "Earth spherical with radius of 6,371,229.0 m",
        "gridUnits": "degrees",
        "resolution": 48,
        "winds": "true",
        "scanMode": 0,
        "nx": nx,
        "ny": ny,
        "basicAngle": 0,
        "subDivisions": 0,
        "lo1": eccodes.codes_get(msgid, "longitudeOfFirstGridPointInDegrees"),
        "la1": eccodes.codes_get(msgid, "latitudeOfFirstGridPointInDegrees"),
        "lo2": eccodes.codes_get(msgid, "longitudeOfLastGridPointInDegrees"),
        "la2": eccodes.codes_get(msgid, "latitudeOfLastGridPointInDegrees"),
        "dx": eccodes.codes_get(msgid, "iDirectionIncrementInDegrees"),
        "dy": eccodes.codes_get(msgid, "jDirectionIncrementInDegrees"),
    }

    return {"header": header, "data": rounded}


def main():
    cycle_time = latest_cycle()
    if cycle_time is None:
        print("Could not determine latest GFS cycle")
        sys.exit(1)

    print(f"Latest GFS cycle: {cycle_time.isoformat()}")

    try:
        grib_data = download_grib(cycle_time)
    except urllib.error.URLError as e:
        print(f"Download failed: {e}")
        sys.exit(1)

    print(f"Downloaded {len(grib_data)} bytes")

    messages = grib2_to_json(grib_data)
    if len(messages) < 2:
        print(f"Expected 2 messages (U/V), got {len(messages)}")
        sys.exit(1)

    # Sort: U-component first, then V-component
    messages.sort(key=lambda m: m["header"]["parameterNumber"])

    with open(OUTPUT_PATH, "w") as f:
        json.dump(messages, f)

    print(f"Wrote {OUTPUT_PATH} with {len(messages)} records")


if __name__ == "__main__":
    main()
