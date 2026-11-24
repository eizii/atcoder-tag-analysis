# タグ妥当性の再検証 V3.2

2026-11-23。従来と同じABC 3,012問・266タグ。前回保留した44問は、参考解法の状態値・遷移・全制約での計算量まで確認しました。解説側からも候補を追加し、今回の判断記録は49問です。**全266タグの意味的な検証完了や、正解率・再現率の保証ではありません。**

## 今回の結果

| 項目 | V3.1 | V3.2 |
|---|---:|---:|
| 確率DP T029（補助を含む確認済み対応） | 20 | 25 |
| 期待値DP T026（別解・補助を含む確認済み対応） | 22 | 25 |
| 問題–タグ対応 | 5,143 | 5,158 |
| タグあり | 2,256 | 2,257 |
| 正のタグ対応について個別確認した問題 | 174 | 183 |

タグ対応は8問に15件追加、削除0件です。これに加えABC313 F等の役割を補正しました。主解・別解・補助・証明の概念を同じ件数として混同しないため、役割別の一覧と行列も出しています。

| タグ | 主解 | 別解 | 補助 |
|---|---:|---:|---:|
| 確率DP | 17 | 0 | 8 |
| 期待値DP | 16 | 3 | 6 |

**25問ずつは、現在根拠を確認して付与した集合の大きさです。真の適用可能問題数とは断定しません。** 前回の候補98問は43問でいずれかのDPを確認、55問では確認した解法を別手法として記録。追加5問を含む103問では45問がDP確認・58問が参考解法の別手法の判断です。別手法という記録は、他のDP別解が存在しないという負例ではありません。

## 追加したDPと判断の境界

| 問題 | 追加 | 状態・計算方法 |
|---|---|---|
| [ABC301 F](https://atcoder.jp/contests/abc301/editorial/6331) | 確率DP・文字列DP | 接頭辞の29状態の確率。問題文が数え上げなので前回の問題文検索では候補から漏れていた |
| [ABC345 G](https://atcoder.jp/contests/abc345/editorial/9549) | 確率DP（補助） | 位置分布をF(x)^tで伝播し、未到達確率を分割統治・反転公式で抽出 |
| [ABC439 G](https://atcoder.jp/contests/abc439/editorial/14995) | 確率DP（補助） | 同じ確率遷移をpower projectionで一括計算 |
| [ABC473 G](https://atcoder.jp/contests/abc473/editorial/24872) | 確率DP（補助） | 余分な操作回数の分布を確率母関数の積で併合 |
| [ABC481 G](https://atcoder.jp/contests/abc481/editorial/27925) | 確率DP（補助） | パンケーキの順位分布と重み付き和を区間で併合しFFTで高速化 |
| [ABC238 H](https://atcoder.jp/contests/abc238/editorial/3361) | 期待値DP（補助）・区間DP | 区間の手順数と非正規化コスト一次モーメントを同時に伝播 |
| [ABC249 H](https://atcoder.jp/contests/abc249/editorial/3842) | 期待値DP（補助） | 期待時間を色個数別ポテンシャルへ分解し、三角化した再帰を計算 |
| [ABC224 F](https://atcoder.jp/contests/abc224/editorial/2830) | 期待値DP（別解） | 公式別解の線形状態(s,x)を確率平均へ変換。E[s′]=E[s]+E[x]/2、E[x′]=5E[x]+d |

高速化された確率遷移はV3.1と同じ方針で含めています。ただし、素朴な分布DPが時間制限内に収まるとはしていません。ABC345 G・439 G・473 G・481 Gは中心の手法が多項式・畳み込みであり、専門DPタグは補助として分離しています。

期待値DPでは条件付き期待値に加え、確率的な過程の一次モーメントや、期待値方程式を順次計算する変換状態を補助として含めています。ABC238 Hのcostはそのまま期待値ではなく、ABC249 Hのgは残り期待時間そのものではありません。この違いを状態の説明に残しています。

一方、どんな数え上げDPにも後から分母を付けて確率DPと呼ぶ規則は採りません。ABC216 Hの符号付きLGV行列式DP、ABC242 Hの被覆部分集合数、ABC253 Hの森数、ABC272 Hの包除用個数、ABC321 Gの連結配線数、ABC331 Gの包除・カード部分集合数は、確認した参考解法では数え上げDPとして区別しています。ABC301 Fは公式解説に確率状態と遷移の明示がある点も確認しています。

ABC261 D・313 Fの最大化DP、平均の閉形式、全列挙、期待値の線形性のみの解法も区別しました。ABC313 Fの二項係数は証明用の別の等式なので、T177をanalysis_conceptに変更し、主手法一覧へ混ざらないようにしました。

## 独立した小規模照合

有理数の厳密計算で1,109比較を実行しました。さらにWipeoutの隠れたカード配置5,913通りを全列挙しました。

- Sugoroku：出目列の再帰列挙と、位置分布の母関数から得る初回到達分布を比較。
- Wipeout：実際の未知カード選択のシミュレーションと、各kの確率因子の積を比較。
- Half-Baked：全選択結果のソートと、区間併合の結果を比較。同値のパンケーキを含むケースも確認。
- Removing People：実際の円環から一人ずつ除く確率過程と、区間のコスト一次モーメントを比較。
- Dye Color：N=2,3の全状態の吸収マルコフ方程式と、色個数別ポテンシャルを比較。
- Separate Digits：+の全配置と、二つの期待値状態の更新を比較。
- Anti-DDoS：縮小した大小文字集合の全置換と、同じ状態構造の確率DPを比較。

これらは状態の意味・式変形の検証です。高速FFT実装の全制約テストや、全データの正解率を保証するものではありません。既存の回帰テスト19件と確率監査テスト8件も通過しています。

**出典の内部不一致**：ABC481 Gの保存済み解説本文の「定式化2」のMには選択確率1/2が欠けて見えますが、同じ出典の実装cmには1/2があります。N=1, A=1, B=2で期待値3/2となり、係数を省くと3になります。今回は実装の正規化を採用して全列挙と照合しました。出典本文は書き換えていません。

## 参照ファイルと残る範囲

- [今回49問の判断・原文・理由](followup_decisions.csv)、[タグ追加差分](change_audit.csv)、[役割の変更](role_changes.csv)。
- [確率DPの全25問](probability_dp_problems.csv)、[期待値DPの全25問](expectation_dp_problems.csv)。各行に状態・遷移と原文を記録。
- [103問の候補監査](probability_candidate_audit.csv)。未付与を適用不可能の意味で扱わないでください。
- [全問の状態](problems.csv)、[全対応](all_problems_tagged.csv)、[全行列](problem_tag_matrix.csv)。自動候補を含むためvalidation_statusを参照。
- [確認した主解・別解のみ](reviewed_core_assignments.csv)、[その行列](reviewed_core_problem_tag_matrix.csv)。証明・補助は除外。
- [266タグの確認範囲](tag_validation_coverage.csv)、[解説語句の追加スクリーニング](editorial_expansion_screen.csv)。スクリーニングだけの問題は意味的確認済みではありません。
- [整合性検証](followup_verification.json)、[解法照合](followup_solution_witness_verification.json)、[入力ハッシュ](followup_input_manifest.json)。

全3,012問のうち、正の対応を個別確認した問題は183問、記録した解法の全タグを点検した問題は85問です。今回49問の参考解法確認には、専門DPを採用しない理由だけを点検した問題も含むため、この数字と合算しません。自動タグは多数残り、未判定の問題は746問です。無作為標本・独立した正解ラベルによる全体精度の評価はまだ行っていません。

## 再生成

元のV3・V3.1およびクラスタリング結果は保存し、今回の結果はoutput_v3_2に分離しています。既存の入力でオフライン再生成できます。

```powershell
.\.venv-clustering\Scripts\python.exe -X utf8 abc_all/record_validity_followup.py
.\.venv-clustering\Scripts\python.exe -X utf8 abc_all/tag_precision.py --output-dir output_v3_2 --additional-review-file abc_all/probability_reviews.tsv --additional-review-file abc_all/validity_followup_reviews.tsv --baseline-dir output_v3_1 --version abc-all-266-evidence-v3.2-validity-followup
.\.venv-clustering\Scripts\python.exe -X utf8 abc_all/validate_followup_witnesses.py
.\.venv-clustering\Scripts\python.exe -X utf8 abc_all/verify_validity_followup.py
```

## 前回保留44問の判断一覧

| 問題 | 今回の判断 | 計算量 |
|---|---|---|
| [abc008_3](https://atcoder.jp/contests/abc008/tasks/abc008_3) コイン | reference_other_method | O(N^2) |
| [abc028_d](https://atcoder.jp/contests/abc028/tasks/abc028_d) 乱数生成 | reference_other_method | O(1) |
| [arc068_a](https://atcoder.jp/contests/abc053/tasks/arc068_a) X: Yet Another Die Game | deterministic_statement | O(1) |
| [arc085_a](https://atcoder.jp/contests/abc078/tasks/arc085_a) HSI | reference_other_method | O(1) arithmetic |
| [abc118_c](https://atcoder.jp/contests/abc118/tasks/abc118_c) Monsters Battle Royale | deterministic_statement | O(N log max A) |
| [abc126_c](https://atcoder.jp/contests/abc126/tasks/abc126_c) Dice and Coin | reference_other_method | O(N log K) |
| [abc142_a](https://atcoder.jp/contests/abc142/tasks/abc142_a) Odds of Oddness | reference_other_method | O(1) |
| [abc154_d](https://atcoder.jp/contests/abc154/tasks/abc154_d) Dice in Line | reference_other_method | O(N) |
| [abc160_f](https://atcoder.jp/contests/abc160/tasks/abc160_f) Distributing Integers | count_dp_reference | O(N) |
| [abc179_b](https://atcoder.jp/contests/abc179/tasks/abc179_b) Go to Jail | deterministic_statement | O(N) |
| [abc193_d](https://atcoder.jp/contests/abc193/tasks/abc193_d) Poker | reference_other_method | O(9^2) |
| [abc202_a](https://atcoder.jp/contests/abc202/tasks/abc202_a) Three Dice | deterministic_statement | O(1) |
| [abc203_a](https://atcoder.jp/contests/abc203/tasks/abc203_a) Chinchirorin | deterministic_statement | O(1) |
| [abc208_a](https://atcoder.jp/contests/abc208/tasks/abc208_a) Rolling Dice | deterministic_statement | O(1) |
| [abc216_h](https://atcoder.jp/contests/abc216/tasks/abc216_h) Random Robots | count_dp_reference | O(2^K K(N+max x)) |
| [abc238_h](https://atcoder.jp/contests/abc238/tasks/abc238_h) Removing People | confirmed_expectation_moment_dp | O(N^3) |
| [abc242_a](https://atcoder.jp/contests/abc242/tasks/abc242_a) T-shirt | reference_other_method | O(1) |
| [abc242_h](https://atcoder.jp/contests/abc242/tasks/abc242_h) Random Painting | count_dp_reference | O(N M^2) |
| [abc249_h](https://atcoder.jp/contests/abc249/tasks/abc249_h) Dye Color | confirmed_expectation_transformed_dp | O(N^2) or O(N^2 log N) |
| [abc253_h](https://atcoder.jp/contests/abc253/tasks/abc253_h) We Love Forest | count_dp_reference | O(N^3 2^N + N 3^N) |
| [abc257_h](https://atcoder.jp/contests/abc257/tasks/abc257_h) Dice Sum 2 | reference_other_method | O(N^2 log N) |
| [abc261_d](https://atcoder.jp/contests/abc261/tasks/abc261_d) Flipping and Bonus | maximization_dp_reference | O(N^2) |
| [abc272_h](https://atcoder.jp/contests/abc272/tasks/abc272_h) Flipping Coins 2 | count_dp_reference | O(N log^2 N) |
| [abc276_f](https://atcoder.jp/contests/abc276/tasks/abc276_f) Double Chance | reference_other_method | O(N log max A) |
| [abc297_b](https://atcoder.jp/contests/abc297/tasks/abc297_b) chess960 | deterministic_statement | O(|S|) |
| [abc308_c](https://atcoder.jp/contests/abc308/tasks/abc308_c) Standings | reference_other_method | O(N log N) |
| [abc310_g](https://atcoder.jp/contests/abc310/tasks/abc310_g) Takahashi And Pass-The-Ball Game | deterministic_sum_reference | O(N log K) |
| [abc313_f](https://atcoder.jp/contests/abc313/tasks/abc313_f) Flip Machines | maximization_dp_reference | O(M+N 2^{N/2}) |
| [abc321_g](https://atcoder.jp/contests/abc321/tasks/abc321_g) Electric Circuit | count_dp_reference | O(3^N) |
| [abc331_g](https://atcoder.jp/contests/abc331/tasks/abc331_g) Collect Them All | count_dp_reference | O(N log^2 N) with polynomial multiplication |
| [abc334_e](https://atcoder.jp/contests/abc334/tasks/abc334_e) Christmas Color Grid 1 | reference_other_method | O(HW alpha(HW)) |
| [abc345_g](https://atcoder.jp/contests/abc345/tasks/abc345_g) Sugoroku 5 | confirmed_probability_dp_accelerated | O(N^1.5 log N) or O(N log N) |
| [abc392_d](https://atcoder.jp/contests/abc392/tasks/abc392_d) Doubles | reference_other_method | O(N S log S), S=sum K_i |
| [abc407_b](https://atcoder.jp/contests/abc407/tasks/abc407_b) P(X or Y) | reference_other_method | O(6^2) |
| [abc439_g](https://atcoder.jp/contests/abc439/tasks/abc439_g) Sugoroku 6 | confirmed_probability_dp_accelerated | O(N log^2 N + L log L) |
| [abc448_g](https://atcoder.jp/contests/abc448/tasks/abc448_g) Conquest | reference_other_method | O(N log N + S^2) for reference solution |
| [abc456_a](https://atcoder.jp/contests/abc456/tasks/abc456_a) Dice | deterministic_statement | O(1) |
| [abc456_b](https://atcoder.jp/contests/abc456/tasks/abc456_b) 456 | reference_other_method | O(6^3) |
| [abc462_g](https://atcoder.jp/contests/abc462/tasks/abc462_g) Completely Wrong | reference_other_method | O(N log^2 N) |
| [abc463_f](https://atcoder.jp/contests/abc463/tasks/abc463_f) Senshuraku | reference_other_method | O(N + log MOD) |
| [abc463_g](https://atcoder.jp/contests/abc463/tasks/abc463_g) Random Walk Distance | reference_other_method | O(max(N+|X|) sqrt(T)) |
| [abc472_f](https://atcoder.jp/contests/abc472/tasks/abc472_f) Centroid of a Slice | reference_other_method | O(N+Q) or O(N+Q log N) |
| [abc473_g](https://atcoder.jp/contests/abc473/tasks/abc473_g) Wipeout | confirmed_probability_dp_accelerated | O(N log^2 N) |
| [abc481_g](https://atcoder.jp/contests/abc481/tasks/abc481_g) Half-Baked | confirmed_probability_dp_accelerated | O(N log^2 N) |
