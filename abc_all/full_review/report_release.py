"""Document the full-review release without treating consistency as accuracy."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parent.parent;O=R/'output_v4';W=R/'full_review'
def read(p,delimiter=','):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=delimiter))
s=json.loads((O/'summary.json').read_text(encoding='utf-8'));catalog=read(O/'tag_catalog.csv');cat={r['tag_id']:r for r in catalog};pairs=read(O/'all_problems_tagged.csv');changes=read(O/'change_audit.csv');ledger=read(W/'merged_full_reviews.tsv','\t');by={r['problem_id']:r for r in ledger}
prob=[r for r in pairs if r['tag_id'] in {'T029','T026'}]
with (O/'probability_expectation_reviews.csv').open('w',encoding='utf-8-sig',newline='') as f:
 fields=['problem_id','tag_id','tag','role','url','reason'];writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({**{k:r[k] for k in fields if k!='reason'},'reason':by[r['problem_id']]['reason']} for r in prob)
with (O/'vocabulary_gaps.csv').open('w',encoding='utf-8-sig',newline='') as f:
 fields=['problem_id','out_of_vocabulary','reason'];writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in ledger if r['out_of_vocabulary'])
with (O/'source_and_candidate_notes.csv').open('w',encoding='utf-8-sig',newline='') as f:
 fields=['problem_id','uncertainty','reason'];writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:r.get(k,'') for k in fields} for r in ledger if r.get('uncertainty'))
text=f'''# ABC全3,012問のタグ妥当性確認 V4

2026-11-24に、対象全3,012問について問題文・満点解法とタグの対応を個別に確認しました。対象データは2026-11-05固定、ABC001〜482（316欠番）です。主担当と3エージェントで分担し、保留256問は追加精査後に統合しました。

主解に加え、制約内で成立を確認した別解・補助手法を採用しています。証明、比較例、計算量の説明だけに使う概念は別表です。`full` は記録した実行可能な参考解法のタグ全体を点検したという意味で、あらゆる別解の網羅や266項目それぞれの不適用証明ではありません。

| 項目 | 件数 |
| --- | ---: |
| 個別確認済み | {s['fully_reviewed_problems']:,} / 3,012 |
| 未確認・保留 | 0 |
| 主表にタグがある問題 | {s['tagged_problem_count']:,} |
| 確認後も固定語彙に該当しない問題 | {s['no_matching_tag_after_review_count']:,} |
| 主解・別解・補助の問題タグ対応 | {s['assigned_pairs']:,} |
| 主表で使うタグ種類 | {s['used_tags']} / 266 |
| 別表の概念・証明タグ対応 | {s['analysis_concept_pairs']:,} |
| V3.2からタグ集合が変わった問題 | {s['changed_problems']:,} |
| 対応の追加 / 削除 | {s['added_pairs']:,} / {s['removed_pairs']:,} |
| 維持した対応の役割修正 | {s['role_changes']:,} |

## 確率DP・期待値DP

| タグ | 主解 | 別解 | 補助 | 合計 |
| --- | ---: | ---: | ---: | ---: |
'''
for t in ('T029','T026'):
 r=cat[t];text+=f"| {r['tag']} | {r['primary_count']} | {r['alternative_count']} | {r['supporting_count']} | {r['problem_count']} |\n"
text+='''
[該当全問題と役割・判断理由](probability_expectation_reviews.csv)を確認できます。期待値を問うだけで期待値DPを付けず、DP状態が確率分布か期待報酬かも区別しました。ABC319 Cの512状態確率DPやABC360 Eの期待位置DPも、主解とは別の実行可能な方法として含めています。

## 修正の例

- ABC031 A・ABC092 B・ABC100 Dなど、他問題が混ざるPDFからの誤付与を問題ごとの解法で訂正。
- ABC034 Cの大きい制約では通常の格子DPを外し、二項係数と逆元を採用。
- ABC055 Cの題名にあるScc、ABC170 Dの変数名dpなど、名前だけの一致を除外。
- ABC229 HのGrundy/Nim、ABC382 Gの小規模検算用0-1 BFSを主表から除外。
- ABC198 FのBurnside、ABC220 Fの全方位木DP、ABC340 Gのvirtual tree＋木DPなど、手順として必要な専門タグを補完。
- ABC184 Dは残り期待回数DPを主解、前向き到達確率DPを別解として区別。
- ABC405 GはMo＋平方分割を採用し、速度不足の導入例である通常セグ木版を別表へ分離。

## データ

| ファイル | 内容 |
| --- | --- |
| [全問題一覧](problems.csv) | 3,012問、主表タグと判断状態、語彙外手法 |
| [問題タグ対応](all_problems_tagged.csv) | 主解・別解・補助、根拠URL付き |
| [問題×266タグ行列](problem_tag_matrix.csv) | 主表3役割のみ |
| [役割別件数](tag_catalog.csv) | 266タグすべて、役割別件数 |
| [概念・証明の別表](analysis_concept_assignments.csv) | 主表に混ぜない説明上の概念 |
| [全役割の対応](all_role_assignments.csv) | 主表と別表を合わせたもの |
| [全役割の行列](all_roles_problem_tag_matrix.csv) | 概念まで含む場合に使用 |
| [判断台帳](../full_review/merged_full_reviews.tsv) | 全件の採否、引用箇所、解法・計算量の理由 |
| [詳細JSONL](problems_tagged.jsonl) | 問題文・解説・役割・引用・判断理由 |
| [V3.2との差分](change_audit.csv) | 追加・削除・役割変更 |
| [語彙外手法](vocabulary_gaps.csv) | 現行266語にない手法。近い別タグへ無理に置換しない |
| [出典・不採用候補の注意](source_and_candidate_notes.csv) | 解説の誤植、未確認の追加候補など |
| [集計・入力ハッシュ](summary.json) | 再現対象と件数 |
| [整合性検査](full_review_verification.json) | 台帳・CSV・行列・役割分離の照合 |

`primary` は主解、`alternative` は採用した別解、`supporting` は採用解法で実際に使う補助です。`concept` と `analysis_concept` は主表に含めません。0は採用した参考解法に対応タグがないことを示し、どんな別解にも使えないという独立した負例ラベルではありません。タグなしの初歩的計算等も一覧から除外していません。

## 検証と再生成

3,012件の一意なID、元本文と引用の一致、タグIDと役割、判断理由、保留ゼロを照合しました。CSV・JSONL・行列・件数も相互照合しています。既存の出典抽出・確率監査の回帰テスト27件が通過しました。新しい別解はABC396 G、ABC390 E、ABC412 Dで小規模全探索と計6,686ケースを比較し一致しています。ABC319 Cほかの確率DPの照合記録も [作業記録](../full_review/) に保存しています。

これらは意味の確認とデータの整合性確認であり、独立した人間による正解ラベルとの精度推定ではありません。精度100%の保証値は出していません。追加の別解が未検証のものは採用せず、確認済みの解法について判断を確定しています。

ワークスペース直下から再生成できます。外部LLM APIは呼びません。

```powershell
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/full_review/verify_progress.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/full_review/build_release.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/full_review/verify_release.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/full_review/report_release.py
```

過去のV3.2やクラスタリング実験は保存されています。今回の行列でクラスタリングを再計算する作業は含みません。
'''
(O/'README.md').write_text(text,encoding='utf-8-sig')
head=f'''# 2026-11-24 全3,012問の妥当性確認 V4

[全件確認の結果・修正版](output_v4/README.md)。対象全3,012問の参考解法とタグを個別確認し、保留を解消しました。主解・制約内の別解・補助を収録し、証明上の概念を別表に分けています。確率DP{cat['T029']['problem_count']}問、期待値DP{cat['T026']['problem_count']}問。独立した正解ラベルによる精度推定ではありません。

以下は過去の版・実験の記録です。

'''
p=R/'README.md';prior=p.read_text(encoding='utf-8-sig')
if not prior.startswith('# 2026-11-24 全3,012問'):p.write_text(head+prior,encoding='utf-8-sig')
print('release documentation written')
