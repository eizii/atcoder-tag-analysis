# SVD 8・16・32・64次元：まとめ

全難易度・2000未満、cut=0.7・0.8・0.9。制約なしのSVD＋平均連結法。保存済みの計算結果から作成し、再学習・タグ付与変更はしていません。

## 4次元設定を横に並べた比較画像

左から8・16・32・64次元です。画像は横に長いため、拡大して確認してください。タグ名は各パネルの左側です。

| データ | cut=0.7 | cut=0.8 | cut=0.9 |
|---|---|---|---|
| 全難易度 | [PNG](all_difficulties/comparison_8_16_32_64_cut_0.7.png)・[SVG](all_difficulties/comparison_8_16_32_64_cut_0.7.svg) | [PNG](all_difficulties/comparison_8_16_32_64_cut_0.8.png)・[SVG](all_difficulties/comparison_8_16_32_64_cut_0.8.svg) | [PNG](all_difficulties/comparison_8_16_32_64_cut_0.9.png)・[SVG](all_difficulties/comparison_8_16_32_64_cut_0.9.svg) |
| 2000未満 | [PNG](under_2000/comparison_8_16_32_64_cut_0.7.png)・[SVG](under_2000/comparison_8_16_32_64_cut_0.7.svg) | [PNG](under_2000/comparison_8_16_32_64_cut_0.8.png)・[SVG](under_2000/comparison_8_16_32_64_cut_0.8.svg) | [PNG](under_2000/comparison_8_16_32_64_cut_0.9.png)・[SVG](under_2000/comparison_8_16_32_64_cut_0.9.svg) |

## 個別画像

| データ | 次元数 | cut=0.7 | cut=0.8 | cut=0.9 |
|---|---:|---|---|---|
| 全難易度 | 8 | 9群：[PNG](all_difficulties/svd_8/dendrogram_cut_0.7.png)・[SVG](all_difficulties/svd_8/dendrogram_cut_0.7.svg) | 5群：[PNG](all_difficulties/svd_8/dendrogram_cut_0.8.png)・[SVG](all_difficulties/svd_8/dendrogram_cut_0.8.svg) | 3群：[PNG](all_difficulties/svd_8/dendrogram_cut_0.9.png)・[SVG](all_difficulties/svd_8/dendrogram_cut_0.9.svg) |
| 全難易度 | 16 | 15群：[PNG](all_difficulties/svd_16/dendrogram_cut_0.7.png)・[SVG](all_difficulties/svd_16/dendrogram_cut_0.7.svg) | 14群：[PNG](all_difficulties/svd_16/dendrogram_cut_0.8.png)・[SVG](all_difficulties/svd_16/dendrogram_cut_0.8.svg) | 8群：[PNG](all_difficulties/svd_16/dendrogram_cut_0.9.png)・[SVG](all_difficulties/svd_16/dendrogram_cut_0.9.svg) |
| 全難易度 | 32 | 33群：[PNG](all_difficulties/svd_32/dendrogram_cut_0.7.png)・[SVG](all_difficulties/svd_32/dendrogram_cut_0.7.svg) | 30群：[PNG](all_difficulties/svd_32/dendrogram_cut_0.8.png)・[SVG](all_difficulties/svd_32/dendrogram_cut_0.8.svg) | 23群：[PNG](all_difficulties/svd_32/dendrogram_cut_0.9.png)・[SVG](all_difficulties/svd_32/dendrogram_cut_0.9.svg) |
| 全難易度 | 64 | 60群：[PNG](all_difficulties/svd_64/dendrogram_cut_0.7.png)・[SVG](all_difficulties/svd_64/dendrogram_cut_0.7.svg) | 53群：[PNG](all_difficulties/svd_64/dendrogram_cut_0.8.png)・[SVG](all_difficulties/svd_64/dendrogram_cut_0.8.svg) | 37群：[PNG](all_difficulties/svd_64/dendrogram_cut_0.9.png)・[SVG](all_difficulties/svd_64/dendrogram_cut_0.9.svg) |
| 2000未満 | 8 | 7群：[PNG](under_2000/svd_8/dendrogram_cut_0.7.png)・[SVG](under_2000/svd_8/dendrogram_cut_0.7.svg) | 6群：[PNG](under_2000/svd_8/dendrogram_cut_0.8.png)・[SVG](under_2000/svd_8/dendrogram_cut_0.8.svg) | 3群：[PNG](under_2000/svd_8/dendrogram_cut_0.9.png)・[SVG](under_2000/svd_8/dendrogram_cut_0.9.svg) |
| 2000未満 | 16 | 15群：[PNG](under_2000/svd_16/dendrogram_cut_0.7.png)・[SVG](under_2000/svd_16/dendrogram_cut_0.7.svg) | 13群：[PNG](under_2000/svd_16/dendrogram_cut_0.8.png)・[SVG](under_2000/svd_16/dendrogram_cut_0.8.svg) | 8群：[PNG](under_2000/svd_16/dendrogram_cut_0.9.png)・[SVG](under_2000/svd_16/dendrogram_cut_0.9.svg) |
| 2000未満 | 32 | 30群：[PNG](under_2000/svd_32/dendrogram_cut_0.7.png)・[SVG](under_2000/svd_32/dendrogram_cut_0.7.svg) | 28群：[PNG](under_2000/svd_32/dendrogram_cut_0.8.png)・[SVG](under_2000/svd_32/dendrogram_cut_0.8.svg) | 20群：[PNG](under_2000/svd_32/dendrogram_cut_0.9.png)・[SVG](under_2000/svd_32/dendrogram_cut_0.9.svg) |
| 2000未満 | 64 | 64群：[PNG](under_2000/svd_64/dendrogram_cut_0.7.png)・[SVG](under_2000/svd_64/dendrogram_cut_0.7.svg) | 54群：[PNG](under_2000/svd_64/dendrogram_cut_0.8.png)・[SVG](under_2000/svd_64/dendrogram_cut_0.8.svg) | 41群：[PNG](under_2000/svd_64/dendrogram_cut_0.9.png)・[SVG](under_2000/svd_64/dendrogram_cut_0.9.svg) |

nはタグに付与された問題数です。全難易度は156タグ、2000未満は138タグが比較対象で、共起のない文字列処理1タグは別枠です。
