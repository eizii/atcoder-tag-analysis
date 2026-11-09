# distance cut 0.8・0.9のデンドログラム

2026-11-05の固定データから保存済みの平均連結法の樹形を読み込み、カット位置と色分けを変更した。元のcut=0.7のファイルは変更していない。

| 対象 | cut | 元タグ数 | クラスタ数 | PNG | SVG |
|---|---:|---:|---:|---|---|
| 全難易度（難易度不明を含む） | 0.8 | 157 | 135 | [画像](all_difficulties_cut_0.8_dendrogram.png) | [拡大用](all_difficulties_cut_0.8_dendrogram.svg) |
| 全難易度（難易度不明を含む） | 0.9 | 157 | 102 | [画像](all_difficulties_cut_0.9_dendrogram.png) | [拡大用](all_difficulties_cut_0.9_dendrogram.svg) |
| 2000未満 | 0.8 | 139 | 113 | [画像](under_2000_cut_0.8_dendrogram.png) | [拡大用](under_2000_cut_0.8_dendrogram.svg) |
| 2000未満 | 0.9 | 139 | 89 | [画像](under_2000_cut_0.9_dendrogram.png) | [拡大用](under_2000_cut_0.9_dendrogram.svg) |

- Jaccard距離・平均連結法。結合距離がcut以下なら同一クラスタとする。
- 1タグのみ、1問のみのクラスタも含める。問題数による除外は行っていない。
- 各データ内で樹形と葉の順序は共通。cutの変更で樹形そのものは変わらない。
- nは各タグに付与された問題数。枝色に分野名の意味はない。色は繰り返される。
- タグ付与は自動付与の比較用データであり、全件の独立した人手検証は未実施。
- manifest.jsonに入力ハッシュと検証項目を記録。
