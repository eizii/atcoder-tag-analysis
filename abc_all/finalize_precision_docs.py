"""Write the V3 review guide and core-method subset from verified tables."""
import csv,json
from pathlib import Path
from tag_all import csv_write
R=Path(__file__).resolve().parent

def main():
 out=R/'output_v3'
 s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
 with (out/'all_problems_tagged.csv').open(encoding='utf-8-sig') as f:assignments=list(csv.DictReader(f))
 with (out/'problems.csv').open(encoding='utf-8-sig') as f:problems=list(csv.DictReader(f))
 with (out/'tag_catalog.csv').open(encoding='utf-8-sig') as f:catalog=list(csv.DictReader(f))
 core=[r for r in assignments if r['validation_status']=='assistant_reviewed' and r['role'] in {'primary','alternative'}]
 csv_write(out/'reviewed_core_assignments.csv',list(assignments[0]),core)
 core_pairs={(r['problem_id'],r['tag_id']) for r in core}
 csv_write(out/'reviewed_core_problem_tag_matrix.csv',['problem_id',*[r['tag_id'] for r in catalog]],[dict(problem_id=p['problem_id'],**{t['tag_id']:int((p['problem_id'],t['tag_id']) in core_pairs) for t in catalog}) for p in problems])
 q=json.loads((out/'quality_audit.json').read_text(encoding='utf-8'));q['reviewed_core_assignments']=len(core)
 (out/'quality_audit.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 text=f'''# タグ付け精度改善版 V3

レビュー日：2026-11-23。問題集合は2026-11-05時点のABC001〜482（ABC316欠番）、全3,012問・266タグを維持しています。

## 結果

全問に根拠範囲の修正を適用し、**{s['changed_problems']}問のタグを変更**しました。追加{s['added_pairs']}対応・削除{s['removed_pairs']}対応です。削除には、確認した誤付与に加え、根拠を絞って保留した対応も含みます。

| 指標 | V2統一自動付与 | V3 |
|---|---:|---:|
| 対象問題 | 3,012 | 3,012 |
| タグあり | 2,189 | {s['tagged_problem_count']:,} |
| 未判定 | 823 | {s['unresolved_problem_count']:,} |
| 確認した解法に対応タグなし | 0 | {s['no_matching_tag_after_review_count']} |
| 問題–タグ対応 | 5,089 | {s['assigned_pairs']:,} |
| 使用タグ | 157 | {s['used_tags']} |

AIアシスタントが個別確認したのは**{s['assistant_semantic_reviewed_problems']}問**です。内訳は、記録した解法全体のタグを点検した{s['fully_reviewed_problems']}問と、特定タグの根拠を点検した{s['partially_reviewed_problems']}問です。採用を確認した対応は{s['reviewed_assignments']}件、そのうち主解・実行可能な別解は{len(core)}件です。部分確認の問題で、他の自動タグまで確認済みにはしていません。

`full` は記録した満点解法のタグ集合を点検したという意味で、すべての可能な別解を網羅したという意味ではありません。原文からの確認に加え、問題文と制約から実行可能な解法を構成したものもあり、理由欄に手順・式・計算量を記録しています。以前の898問の暫定タグや27問の個別レビューを無条件で引き継いではいません。

## 修正した原因

- 古いPDFで、次の問題や英語版全体の解説が混ざる問題を修正。26箇所の次問題境界、13箇所の部分点節を分離しました。問題記号の誤植だけで本文を切らないケースもテストしています。
- 優先度付きキュー内のQueue、平衡二分探索木内の二分探索、topological sort内のsortなど、名前の包含による誤検出を抑えました。独立した利用根拠は保持します。
- 部分点用の列挙、不適用の手法、参考記事名、比喩、数学的定理と同名の探索法を区別しました。
- 短い保存済み解説に対応する公開ページ195件を再取得。対象問題へのリンクを照合して192件を補完用入力に採用しました。17件の問題–出典対応はリンク不一致で保留し、28件で100文字以上の本文を回復しました。

| 問題 | 点検した内容 |
|---|---|
| ABC062 D / ARC074 B | ヒープと分割位置の走査。別問題のDP・最大流・最小カットを除去 |
| ABC069 D / ARC080 B | 蛇行順に色を塗る構築。後続問題のセグ木・マッチングを除去 |
| ABC015 D | 個数制約つきナップサックDP。比較説明中のXORと制約外のDFSを除去 |
| ABC178 D | 玉と仕切りの並べ方の数は、ソートの実行ではない |
| ABC239 H | 期待値のメモ化DPを追加。関連問題名のTotientを除去 |
| ABC328 E | 全コストを保持する集合DPはPrim法そのものではない |
| ABC386 F | 編集距離の問題で、参考記事名のLCSを除去 |
| ABC448 G | ミニマックス定理と探索法、永続木の比喩と累積和を区別 |

## データの使い方

- [全問のタグ・状態](problems.csv)：`review_scope`、`tagging_status`、語彙外の技法も表示。
- [全対応](all_problems_tagged.csv)：自動候補を含む。確認済みは `validation_status=assistant_reviewed`。
- [確認した対応のみ](reviewed_assignments.csv)：役割別の216対応。
- [確認した主解・別解のみ](reviewed_core_assignments.csv)：中心的な手法を比較するための{len(core)}対応。
- [全問の行列](problem_tag_matrix.csv)、[確認した対応の行列](reviewed_problem_tag_matrix.csv)、[確認した主解・別解の行列](reviewed_core_problem_tag_matrix.csv)。いずれも3,012問×266列。
- [明示した採用・除外判断](reviewed_decisions.csv)：原文箇所・理由・出典つき。
- [V2との差分](change_audit.csv)、[出典範囲の除外](source_scope_audit.csv)、[根拠の除外](rejected_evidence.csv)、[本文回復](source_recovery_audit.csv)。
- [残るレビュー順](review_queue.csv)：未判定のC以降、少数タグ、多数タグの問題を優先。
- [語彙不足](vocabulary_gaps.csv)：貪欲法、Mo法、最小公倍数、基本算術など。266タグへ無理に置き換えません。
- [集計](summary.json)、[詳細監査](quality_audit.json)、[検証結果](precision_verification.json)、[入力ハッシュ](input_manifest.json)。

役割は `primary`（主解）、`alternative`（別解）、`supporting`（補助）、`concept`（問題の構造・対象）、`analysis_concept`（証明上の概念）。自動候補の `unresolved` は役割も未確認です。`needs_review=0` はAIによる今回の確認が済んだ対応を表し、人手確認済みという意味ではありません。

**確認用行列の0は未確認・未収録を含み、適用不可能という負例ではありません。** 全0行から「アルゴリズムなし」と判断しないでください。確認した主解・別解のデータも、点検対象を選んだ小さい部分集合であり、全体の代表標本ではありません。

## 検証と残り

問題ID・タグID・重複・全問収録、CSV/JSONL/行列の一致、原文箇所、根拠ハッシュ、役割、差分を照合済みです。回帰テスト19件に加え、9種類の解法を小規模な独立した全探索と照合しました（[解法の照合結果](solution_witness_verification.json)）。これらは整合性と特定の解法の検証であり、データ全体の正解率ではありません。

**未判定は{s['unresolved_problem_count']}問、解法全体の確認が残る問題は{q['review_queue_size']}問です。** 独立した人手による正解集合や無作為標本での全体精度推定は未実施です。全問を正確に確認し終えたとは主張していません。

従来の実験用データ、クラスタリング結果、アプリのデータは保存しています。

## 再生成

作業フォルダーから既存の仮想環境で実行します。通常の再生成にネットワークアクセス・外部AI APIは不要です。

```powershell
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/tag_precision.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/report_precision.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/finalize_precision_docs.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/verify_precision.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 -m unittest discover -s abc_all -p test_precision.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/validate_review_witnesses.py
```

判断の原本は `../precision_reviews.tsv`、追加出典は `../precision_sources.jsonl`。元の `../corpus_sources.jsonl` は変更せず、補完した本文とコードは別入力です。ダウンロードHTMLの `../precision_cache/` はキャッシュであり、補完済みJSONLがあればタグ付け再生成には不要です。
'''
 (out/'README.md').write_text(text,encoding='utf-8')
 print(json.dumps(dict(core_assignments=len(core),guide_written=True)))

if __name__=='__main__':main()
