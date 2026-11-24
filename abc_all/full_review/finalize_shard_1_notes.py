from pathlib import Path
p=Path('abc_all/full_review/shard_1_notes.md')
s=p.read_text(encoding='utf-8-sig')
s=s.replace('現在、750..1109 の360問を個別に点検し、`shard_1.tsv` へ保存済みです。残りは index 1110..1499 の390問です。','750..1499 の全750問を個別に点検し、`shard_1.tsv` へ保存済みです。担当範囲の未確認は0件です。')
s=s.replace('次の対象は index 1110 です。','担当750件は完了し、checkpoint の complete=true、next_index=1500 です。')
s+='\n追加の重要な修正事例:\n\n- ABC229 H: Grundy/XOR/mexは「直接関係がない」と明記された比較説明。列ごとのpartisan game値を合計する解法。\n- ABC234 H: 出力順任意。独立したソートは不要。\n- ABC236 G: min-max半環の行列累乗。XORは一般化例。\n- ABC238 D: Nimは類題名から混入。AND/XOR恒等式で判定。\n- ABC242 H: 被覆集合数DPから期待値を式で求める。確率DP状態ではない。\n- ABC247 C: Fibonacci/Map/区間・桁DPは再帰の説明例で列生成の手法ではない。\n- ABC250 H: 完全家グラフのKruskal/Primは適用困難と明記。多始点Dijkstra+DSU、またはBoruvka MSTが実行可能。\n- ABC258 H: 公式本文のT所属/非所属表記に反転がある。禁止位置を選ばない正しい2状態遷移を記録。\n- ABC261 G: 同一文字の無操作基底は0費用。原文dp=1は誤記。\n- ABC262 H: 同終端の制約の左端は最大を取る。原文の最小は誤記。\n- ABC263 E: 期待値DPに加え、公式editorial4566の前向き到達確率imos別解を確認してT029 alternativeを採用。\n- ABC270 A: 実際はORでありXORではない。\n\n確率/期待値の全採用一覧と理由は `shard_1_probability_expectation_audit.json`。T029は5問、T026は10問。V3.2のtag_idsから両タグを除外した問題は担当内0件です。\n'
p.write_text(s,encoding='utf-8')
