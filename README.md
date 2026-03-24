# Wind-JS

ライブ[デモ](http://esri.github.io/wind-js/)をご覧ください

![Wind JS](https://f.cloud.github.com/assets/351164/2349895/36ba1c9a-a569-11e3-859d-5d753ea0898c.jpeg)


このプロジェクトは、クライアントサイドでのデータ処理と可視化の実験です。このプロジェクトのコードの大部分は https://github.com/cambecc/earth から取得したもので、さまざまなマッピングAPIやフレームワークへの適用を容易にするために再構成されています。

## 仕組み

このプロジェクトのコードは、HTML5 Canvas要素と純粋なJavascriptのみを使用しています。データは、連続的なグローバルグリッドデータセットとして多種多様なデータセットを生成するGlobal Forecast System（全球予報システム）から取得されます（詳細は下記参照）。データは`Windy`というJSクラスに渡され、地図の境界、データ、Canvas要素を受け取り、[双線形補間](http://en.wikipedia.org/wiki/Bilinear_interpolation)を適用して滑らかなサーフェスを生成します。サーフェスが生成されると、関数がランダムなx/y座標にCanvas上へ「パーティクル」をランダムに配置します。各パーティクルは補間されたサーフェスによって決定される方向と速度で移動し、「進化」していきます。

## データ

[GFSデータ](http://nomads.ncdc.noaa.gov/data.php?name=access#hires_weather_datasets)をこのコードで使用する前に、JSONに変換する必要があります。そのために、[@cambecc](https://github.com/cambecc)氏による[`grib2json`](https://github.com/cambecc/grib2json)という素晴らしいプロジェクトを使用しました。このツールはGRIB2ファイル形式のデータを、グリッドを配列として表現したJSON構造に変換します。このツールの出力例は`gfs.json`ファイルで確認できます。

## リソース

* https://github.com/cambecc/earth
* http://earth.nullschool.net/
* [http://nomads.ncdc.noaa.gov/data.php...](http://nomads.ncdc.noaa.gov/data.php?name=access#hires_weather_datasets)
* http://developers.arcgis.com
* [twitter@esri](http://twitter.com/esri)

## 問題の報告

バグを発見した場合や新機能のリクエストがある場合は、Issueを作成してお知らせください。

## コントリビューション

Esriはどなたからのコントリビューションも歓迎します。[コントリビューションガイドライン](https://github.com/esri/contributing)をご参照ください。

## クレジット

この成果のすべての功績は、[cambecc/earth](https://github.com/cambecc/earth)を作成した[@cambecc](https://github.com/cambecc)氏に帰属します。このコードの大部分はそのプロジェクトから直接取得したものであり、非常に素晴らしい作品です。

## ライセンス

このプロジェクトは、コードの95%が[cambecc/earth](https://github.com/cambecc/earth)からコピーされているため、同プロジェクトのMITライセンスを継承しています。

ライセンスのコピーはリポジトリの[license.txt]( https://raw.github.com/Esri/wind-js/master/license.txt)ファイルにあります。
