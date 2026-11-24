# SVD 8・16・64次元のデンドログラム

2026-11-19作成。既存のSVD実験の保存済みlinkageから描画。再学習・タグ付与変更なし。制約なしの通常の平均連結法。

全難易度は156タグ、2000未満は138タグが比較対象。文字列処理1タグは別枠。各画像の赤破線がcut、枝色はcutで分けた群の目印。色は分野を表さず、別の図の同じ色と対応しません。

次元数を変えると距離空間も変わります。同じcutが同じ学習粒度を意味するわけではありません。タグ名は左側、距離は右へ増加します。

| データ | SVD次元 | cut=0.7 | cut=0.8 | cut=0.9 |
|---|---:|---|---|---|
| 全難易度 | 8 | 9群：[PNG](all_difficulties/svd_8/dendrogram_cut_0.7.png)・[SVG](all_difficulties/svd_8/dendrogram_cut_0.7.svg) | 5群：[PNG](all_difficulties/svd_8/dendrogram_cut_0.8.png)・[SVG](all_difficulties/svd_8/dendrogram_cut_0.8.svg) | 3群：[PNG](all_difficulties/svd_8/dendrogram_cut_0.9.png)・[SVG](all_difficulties/svd_8/dendrogram_cut_0.9.svg) |
| 全難易度 | 16 | 15群：[PNG](all_difficulties/svd_16/dendrogram_cut_0.7.png)・[SVG](all_difficulties/svd_16/dendrogram_cut_0.7.svg) | 14群：[PNG](all_difficulties/svd_16/dendrogram_cut_0.8.png)・[SVG](all_difficulties/svd_16/dendrogram_cut_0.8.svg) | 8群：[PNG](all_difficulties/svd_16/dendrogram_cut_0.9.png)・[SVG](all_difficulties/svd_16/dendrogram_cut_0.9.svg) |
| 全難易度 | 64 | 60群：[PNG](all_difficulties/svd_64/dendrogram_cut_0.7.png)・[SVG](all_difficulties/svd_64/dendrogram_cut_0.7.svg) | 53群：[PNG](all_difficulties/svd_64/dendrogram_cut_0.8.png)・[SVG](all_difficulties/svd_64/dendrogram_cut_0.8.svg) | 37群：[PNG](all_difficulties/svd_64/dendrogram_cut_0.9.png)・[SVG](all_difficulties/svd_64/dendrogram_cut_0.9.svg) |
| 2000未満 | 8 | 7群：[PNG](under_2000/svd_8/dendrogram_cut_0.7.png)・[SVG](under_2000/svd_8/dendrogram_cut_0.7.svg) | 6群：[PNG](under_2000/svd_8/dendrogram_cut_0.8.png)・[SVG](under_2000/svd_8/dendrogram_cut_0.8.svg) | 3群：[PNG](under_2000/svd_8/dendrogram_cut_0.9.png)・[SVG](under_2000/svd_8/dendrogram_cut_0.9.svg) |
| 2000未満 | 16 | 15群：[PNG](under_2000/svd_16/dendrogram_cut_0.7.png)・[SVG](under_2000/svd_16/dendrogram_cut_0.7.svg) | 13群：[PNG](under_2000/svd_16/dendrogram_cut_0.8.png)・[SVG](under_2000/svd_16/dendrogram_cut_0.8.svg) | 8群：[PNG](under_2000/svd_16/dendrogram_cut_0.9.png)・[SVG](under_2000/svd_16/dendrogram_cut_0.9.svg) |
| 2000未満 | 64 | 64群：[PNG](under_2000/svd_64/dendrogram_cut_0.7.png)・[SVG](under_2000/svd_64/dendrogram_cut_0.7.svg) | 54群：[PNG](under_2000/svd_64/dendrogram_cut_0.8.png)・[SVG](under_2000/svd_64/dendrogram_cut_0.8.svg) | 41群：[PNG](under_2000/svd_64/dendrogram_cut_0.9.png)・[SVG](under_2000/svd_64/dendrogram_cut_0.9.svg) |
