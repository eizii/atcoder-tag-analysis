# Shard 1 review checkpoint

対象は manifest の 0 始まり index 750..1499。750..1499 の全750問を個別に点検し、`shard_1.tsv` へ保存済みです。担当範囲の未確認は0件です。未確認行を生成・full扱いにしていません。

`verify_shard_1.py` はIDの連続性、重複、原文引用、266タグID、役割を検証し、`shard_1_checkpoint.json` を更新します。現在の範囲・ハッシュはJSONを正としてください。

判定の留意点:

- 主解・実行可能な別解・補助を含め、証明だけの概念はanalysis_conceptへ分離。
- 基本算術、条件分岐、貪欲法などが現行語彙に合わなければ、無理にシミュレーションやDPを付けない。
- 既存タグを継承するだけではなく、出典中の主解と制約から採否を判定。説明や比較表に出る名前は主手法にしない。
- 一部の別解は原文の状態や制約から構成したもの（例: Fenwick/セグ木への置換、通常の桁DP、同じ分布の期待値/確率別表現）。reasonへ具体的な状態・操作・計算量を記録。
- これはAIによる個別レビューで、人手による独立正解集合や全体精度推定ではない。

重要な修正事例:

- ABC170 D: 配列名dpは倍数のマーキング。T022を除去。
- ABC173 F: DSUを使うO(N²)シミュレーションは満点不可。頂点・辺の寄与のO(N)解法へ。
- ABC184 D: 公式のf(a,b,c)は期待残り回数。期待値DPをprimary、到達確率DPをalternativeへ。
- ABC188 E: SCCは一般有向グラフへの発展節。元のDAG問題では不要。
- ABC198 F: Burnside/PolyaのT179が漏れていた。
- ABC201 C: 暗証番号全列挙が主解。一般化解説のFPSは導出概念へ分離。
- ABC202 E: LCAは部分木区間性の証明だけ、括弧列は比喩、DFS時刻は自然に昇順なので独立ソートも不要。
- ABC208 D: Floyd-WarshallのT208が漏れていた。
- ABC208 F: 比較表のFibonacciと二項係数を主解扱いしない。実際は多項式補間。
- ABC211 F: 平面走査T266が漏れていた。
- ABC219 G: 高次数/低次数を分ける次数平方分割T084が漏れていた。
- ABC219 H: 訪問区間と端点・残り取得本数の区間DP。
- ABC220 F: 全方位木DPが漏れていた。
- ABC222 H: 公式本文はO(N log N)のNewton/FFT系解法もTL不可と明記。Lagrange反転＋微分からの線形漸化式O(N)を主解にし、二項和/P-recursiveの実行可能別解を分離。

担当750件は完了し、checkpoint の complete=true、next_index=1500 です。各追記スクリプトは author_shard_1.E/save を使います。再実行しても問題IDごとに上書きするため重複は発生しません。

追加の重要な修正事例:

- ABC229 H: Grundy/XOR/mexは「直接関係がない」と明記された比較説明。列ごとのpartisan game値を合計する解法。
- ABC234 H: 出力順任意。独立したソートは不要。
- ABC236 G: min-max半環の行列累乗。XORは一般化例。
- ABC238 D: Nimは類題名から混入。AND/XOR恒等式で判定。
- ABC242 H: 被覆集合数DPから期待値を式で求める。確率DP状態ではない。
- ABC247 C: Fibonacci/Map/区間・桁DPは再帰の説明例で列生成の手法ではない。
- ABC250 H: 完全家グラフのKruskal/Primは適用困難と明記。多始点Dijkstra+DSU、またはBoruvka MSTが実行可能。
- ABC258 H: 公式本文のT所属/非所属表記に反転がある。禁止位置を選ばない正しい2状態遷移を記録。
- ABC261 G: 同一文字の無操作基底は0費用。原文dp=1は誤記。
- ABC262 H: 同終端の制約の左端は最大を取る。原文の最小は誤記。
- ABC263 E: 期待値DPに加え、公式editorial4566の前向き到達確率imos別解を確認してT029 alternativeを採用。
- ABC270 A: 実際はORでありXORではない。

確率/期待値の全採用一覧と理由は `shard_1_probability_expectation_audit.json`。T029は5問、T026は10問。V3.2のtag_idsから両タグを除外した問題は担当内0件です。
