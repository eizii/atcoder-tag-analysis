# アルゴリズムの階層クラスタリング

対象は898問に対する266タグの0/1行列です。入力は「検証後のタグ付け修正案」（validation\revised、1740付与組）です。問題方向を特徴として転置し、タグをクラスタリングしました。使用されている115タグを全体版、該当問題が3問以上の67タグを少数例の影響を減らす補助版としています。未使用の151タグは分類する材料がなく、excluded_tags.csvに記録しました。

修正案には未点検の付与も含まれます。全問の意味的な正しさを検証済みという意味ではありません。初期表示は使用済みの全タグです。

## 結果の確認

[操作できるレポート](report.html)をブラウザーで開くと、対象と距離の閾値を変えてクラスタ一覧を確認できます。インターネット接続は不要です。図とCSVは以下にあります。

- [全115タグのデンドログラム](dendrogram_all.svg) / [PNG](dendrogram_all.png) / [クラスタ一覧](clusters_all.csv)
- [3問以上の67タグのデンドログラム](dendrogram_min3.svg) / [PNG](dendrogram_min3.png) / [クラスタ一覧](clusters_min3.csv)
- [要確認の付与を除いたデンドログラム](dendrogram_review_excluded.svg) / [クラスタ一覧](clusters_review_excluded.csv)
- [全タグ対の関連度と共通問題](tag_pairs.csv)、[類似度行列](tag_similarity.csv)、[距離行列](tag_distance.csv)
- [閾値別の評価](cut_metrics.csv)、[要確認の付与を除いたときの変化](review_sensitivity.csv)、[集計JSON](summary.json)

初期表示の距離閾値は0.7です。全115タグでは101クラスタ（複数タグのグループ11、単独タグ90）、3問以上の67タグでは64クラスタ（複数タグのグループ3、単独タグ61）になりました。これは探索用の例で、最適なクラスタ数や正式な分類体系を決めたものではありません。

## 距離と階層の作り方

タグAに付いた問題集合をP(A)として、類似度は共通問題数を和集合の問題数で割ります。

```text
Jaccard similarity(A, B) = |P(A) ∩ P(B)| / |P(A) ∪ P(B)|
distance(A, B) = 1 - similarity(A, B)
```

例えば幅優先探索と深さ優先探索の該当問題数はそれぞれ86問・111問、共通問題は45問で、類似度は0.2961です。両方とも付いていない問題は類似度に寄与しません。[SciPyのJaccard距離の定義](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.jaccard.html)に基づきます。

クラスタ間の距離には、その2クラスタに属する全タグ対の距離の平均を使います。SciPyのaverage linkage（UPGMA）を使いました。Jaccard距離でWard法は使用していません。[連結法の定義](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html)

デンドログラムの横軸は結合した時点の距離です。左側で結合するほど問題集合が近くなります。平均連結なので、同じクラスタに入った全タグ対の距離が閾値以下とは限りません。距離1付近での結合は、共通問題がほとんどないグループ間の結合です。左右・上下の表示順やクラスタ番号自体に意味はありません。同じ距離の結合順は実装・入力順に依存する場合があります。

## 3問以上のタグで得られたグループ

距離閾値0.7で、2タグ以上になったグループを掲載します。単独タグもCSVと操作レポートに残しています。件数は各タグの該当問題数で、平均類似度はクラスタ内の全タグ対のJaccard類似度の平均です。

| クラスタ | タグ（該当問題数） | 平均類似度 |
| --- | --- | --- |
| C024 | ミニマックス法（4問）、後退解析（4問） | 0.333 |
| C026 | トポロジカルソート（5問）、閉路検出（3問） | 0.333 |
| C035 | Suffix Array（4問）、Rolling Hash（3問） | 0.400 |

## 関連度の高いタグ対

| タグA | タグB | 類似度 | 共通問題数 | 各タグの問題数 | 例数 |
| --- | --- | --- | --- | --- | --- |
| Grundy数 / Sprague-Grundy | Nim | 1.000 | 2 | 2 / 2 | 1–2問のみ |
| 畳み込み | FFT | 1.000 | 2 | 2 / 2 | 1–2問のみ |
| きたまさ法 | Stars and Bars | 1.000 | 1 | 1 / 1 | 1–2問のみ |
| 二部マッチング | 最大流 | 1.000 | 1 | 1 / 1 | 1–2問のみ |
| 凸包 | 線分交差判定 | 1.000 | 1 | 1 / 1 | 1–2問のみ |
| 凸包 | 三角形の符号付き面積 | 1.000 | 1 | 1 / 1 | 1–2問のみ |
| 線分交差判定 | 三角形の符号付き面積 | 1.000 | 1 | 1 / 1 | 1–2問のみ |
| Z-Algorithm | Rolling Hash | 0.667 | 2 | 2 / 3 | 1–2問のみ |
| Suffix Array | Z-Algorithm | 0.500 | 2 | 4 / 2 | 1–2問のみ |
| 重心分解 | 畳み込み | 0.500 | 1 | 1 / 2 | 1–2問のみ |
| 重心分解 | FFT | 0.500 | 1 | 1 / 2 | 1–2問のみ |
| 乱択アルゴリズム | Color Coding | 0.500 | 1 | 2 / 1 | 1–2問のみ |

Grundy数とNimの類似度1は、このデータで同じ2問に付いたことを意味します。アルゴリズムが同じであるという証明ではありません。全体版の48タグは1〜2問しか例がなく、高い類似度でも判断材料が少ないことに注意して解釈します。tag_pairs.csvの共通問題IDから元の問題・解説を確認できます。

## 分割の評価

| 対象 | 距離閾値 | クラスタ数 | 複数タグのクラスタ | 単独タグ | シルエット |
| --- | --- | --- | --- | --- | --- |
| All used tags | 0.7 | 101 | 11 | 90 | 0.1366 |
| All used tags | 0.8 | 93 | 19 | 74 | 0.1526 |
| All used tags | 0.85 | 85 | 25 | 60 | 0.1647 |
| All used tags | 0.9 | 72 | 29 | 43 | 0.1604 |
| All used tags | 0.95 | 57 | 33 | 24 | 0.1657 |
| All used tags | 0.975 | 51 | 31 | 20 | 0.1611 |
| All used tags | 0.99 | 37 | 23 | 14 | 0.1330 |
| Tags with at least 3 problems | 0.7 | 64 | 3 | 61 | 0.0301 |
| Tags with at least 3 problems | 0.8 | 56 | 11 | 45 | 0.0584 |
| Tags with at least 3 problems | 0.85 | 52 | 14 | 38 | 0.0702 |
| Tags with at least 3 problems | 0.9 | 47 | 15 | 32 | 0.0787 |
| Tags with at least 3 problems | 0.95 | 36 | 19 | 17 | 0.0802 |
| Tags with at least 3 problems | 0.975 | 25 | 17 | 8 | 0.0715 |
| Tags with at least 3 problems | 0.99 | 16 | 11 | 5 | 0.0593 |
| Review-flagged assignments excluded | 0.7 | 100 | 12 | 88 | 0.1425 |
| Review-flagged assignments excluded | 0.8 | 91 | 20 | 71 | 0.1616 |
| Review-flagged assignments excluded | 0.85 | 83 | 26 | 57 | 0.1736 |
| Review-flagged assignments excluded | 0.9 | 70 | 30 | 40 | 0.1687 |
| Review-flagged assignments excluded | 0.95 | 57 | 32 | 25 | 0.1698 |
| Review-flagged assignments excluded | 0.975 | 50 | 30 | 20 | 0.1653 |
| Review-flagged assignments excluded | 0.99 | 38 | 23 | 15 | 0.1388 |

3問以上のタグで初期閾値0.7のシルエットは0.030115227503287205です。観測した結合高さと比較用の閾値で最大だったシルエットは0.0848（距離閾値0.939394、37クラスタ）です。この値は低く、現在の0/1タグ付けでは明確なクラスタ境界が弱いと読み取れます。シルエットだけでクラスタ数を確定せず、結合高さ・問題例・グループの解釈を合わせて検討してください。単独タグのシルエットは0として平均しています。[シルエットの定義](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html)

デンドログラムが元のタグ間距離をどの程度保っているかを表すcophenetic correlationは全体版0.9669、3問以上版0.8788でした。これは階層への距離の保存度で、クラスタの意味や正しさを保証する指標ではありません。[SciPyの定義](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.cophenet.html)

## 要確認の付与を除いた場合

all_problems_tagged.csvのneeds_review=1である77組だけを除き、距離と階層を作り直しました。needs_review=0もすべて検証済みという意味ではありません。除外後は115タグに問題例が残ります。この比較用入力では44問のタグが0件になり、Jaccard距離への寄与もなくなります。例がなくなったタグはexcluded_tags.csvに別の理由として記録しました。

同じ距離閾値0.7で共通の115タグを比較すると、同じクラスタになるタグ対の関係が1組変わり、2タグの同クラスタの相手が変わりました。Adjusted Rand Indexは0.9714です。クラスタ番号は対象ごとに振り直すため、番号の一致・不一致を直接比較していません。

## この結果で分かることと次の改善

今回の関連スコアは「付与された問題集合の重なり」です。FBにある「その問題に対してアルゴリズムを選んだ場合の最適度」は測定していません。行列の0は未付与であり、適用できないという判定ではありません。

同じ問題に登場する補助データ構造と主アルゴリズム、または別解が近くなるため、Dijkstra法とHeapのような組合せもまとまります。同義語を自動で統合する根拠としては使えません。一方、タグ付け時に基礎DPを個別DPへ置き換えるなど、広いタグと細かいタグを併記していない場合があります。概念上の親子関係でも共起がなく、離れることがあります。問題集合は元CSVの範囲に限られ、未使用タグの関連性は評価できません。

分類体系を整える次の作業としては、共通問題を確認し、主解・別解・補助の役割を区別して関連スコアを付けること、未使用タグに代表問題を追加すること、タグの親子関係を別途記録することが有効です。現在の階層はその検討に使える初期結果として保存しました。

## 再実行

作業フォルダーで以下を実行します。Python 3.9以上を想定し、今回の実行環境はPython 3.9.13です。

```powershell
py -m venv .venv-clustering
.\.venv-clustering\Scripts\python.exe -m pip install -r requirements-clustering.txt
.\.venv-clustering\Scripts\python.exe hierarchical_clustering.py
.\.venv-clustering\Scripts\python.exe hierarchical_clustering.py --input-dir validation\revised --threshold 0.85 --output clustering_085
```

既定の入力先はvalidation/revisedです。検証前のデータを使う場合は --input-dir . を指定します。

閾値の変更は出力先を指定しなければ同じclusteringフォルダーを更新します。デンドログラム・クラスタCSV・レポートはその閾値で再生成されます。操作レポートのスライダーはクラスタ一覧・統計を切り替えます。埋め込みの図は生成時の閾値のままであることを表示しています。

linkage CSVの葉ノードはleaves CSVの0始まりのID、結合ノードはタグ数+merge_indexです。左右ノード・結合距離・葉数を保存しており、別のツールでも階層を再構成できます。使用パッケージの版と入力ファイルのSHA-256はsummary.jsonに記録しました。

## 検証

898問題IDの一致、266タグとカタログ件数の一致、0/1入力、1740付与組との完全一致、タグ対距離の全件再計算、距離の対称性・範囲、階層の妥当性・結合高さの単調性を実行時に検証しました。小さな既知の行列でJaccard距離、平均連結の高さ、距離による分割を独立に検証しています。これらは計算・データの整合性の検証で、元のタグ付けの正しさを証明するものではありません。

生成処理ではタグ対距離と入力の整合性を毎回検証します。HTMLの分割計算は別途SciPyとの照合対象とし、画面操作や画像の目視確認の状況は生成時の検証記録に残します。
