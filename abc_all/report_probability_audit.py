"""Document the probability-DP recall defect without claiming global tag validity."""
import json,csv
from pathlib import Path
from tag_precision import ROOT

def main():
 out=ROOT/'output_v3_1'
 s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
 v=json.loads((out/'probability_verification.json').read_text(encoding='utf-8'))
 tests=json.loads((out/'probability_test_results.json').read_text(encoding='utf-8'))
 with (out/'probability_dp_problems.csv').open(encoding='utf-8-sig') as f:prob=list(csv.DictReader(f))
 with (out/'expectation_dp_problems.csv').open(encoding='utf-8-sig') as f:expect=list(csv.DictReader(f))
 def table(rows):return '\n'.join('| ['+r['problem_id']+']('+r['url']+') | '+r['title']+' | '+r['role']+' |' for r in rows)
 text=f'''# 確率DP・期待値DPの付け漏れ監査 V3.1

2026-11-23。対象は従来と同じ3,012問・266タグです。**V3の「確率DPが1問」という集計には重大な付け漏れがありました。** 全体のタグ付けが妥当だと確認できた状態ではありません。

## 原因と確認範囲

旧ルールは「確率DP」「確率 DP」という手法名に依存しており、「基礎DP」は検出できても、状態値が確率であることから専門タグを判定できていませんでした。誤検出の抑制、CSV整合性、限られた解法のテストが通ったことは、付け漏れの少なさを保証しません。

今回、既存タグを絞り込み条件にせず、問題文の確率・期待値・ランダム性などから**98問の候補**を抽出しました。新たに35問について状態値と遷移を記録し、34問に合計38対応を追加しました。

| タグ | V3で付いていた件数 | 根拠付きで確認・反映したV3.1の件数 |
|---|---:|---:|
| 確率DP T029 | 1 | {v['revised_probability_dp']} |
| 期待値DP T026 | 3 | {v['revised_expectation_dp']} |

**20問・22問は確認できた集合であり、適用可能問題の真の総数とは主張しません。** 候補98問のうち、37問でいずれかの専門DPを確認、17問は確認した参考解法が別の手法である理由を記録、44問は追加の意味的精査が残っています。「別手法」の記録も他の実行可能なDP別解を否定しません。候補抽出自体の取りこぼしも未評価です。

## 今回の判定基準

- **確率DP**：状態ごとの到達確率、成功確率、確率分布、または共通係数を戻すと確率質量になる状態量を、遷移で計算する。行列累乗や畳み込みで高速化した同じ確率漸化式も含む。
- **期待値DP**：状態ごとの将来費用・報酬・回数の条件付き期待値、または必要なモーメントを確率的遷移から計算する。最適な選択肢を比較するものも含む。
- 答えが期待値でも、分布を確率DPで求めて最後に期待値へ変換する方法は確率DP。ABC226 H、ABC326 E、ABC360 Eなどが該当する。
- 同じ問題で二つのDPを使う場合は両方を付ける。ABC382 Eはレア枚数分布を確率DPで求め、必要残り枚数ごとの期待パック数を期待値DPで求める。
- 「確率」「期待値」「DP」という単語の共存だけでは採用しない。単純な平均、組合せ式、期待値の線形性、全列挙、一般の多項式係数DPなどは状態値と遷移を確認して区別する。境界的な方法は保留する。
- `primary` は記録した主解、`alternative` は実行可能な別解、`supporting` は前計算や高速化された状態伝播などの補助。すべての別解を網羅したという意味ではない。

## 明確な付け漏れの例

| 問題 | 公式解説の状態・遷移 |
|---|---|
| [ABC275 E](https://atcoder.jp/contests/abc275/editorial/5116) | dp[i][j]＝ルーレットi回後にマスjにいる確率 |
| [ABC298 E](https://atcoder.jp/contests/abc298/editorial/6216) | 両者の位置と手番からの高橋君の勝率 |
| [ABC300 E](https://atcoder.jp/contests/abc300/editorial/6279) | 現在値nから最終値Nに一致する確率 |
| [ABC310 F](https://atcoder.jp/contests/abc310/editorial/6791) | i個のサイコロ後に作れる部分和集合がSである確率 |
| [ABC323 E](https://atcoder.jp/contests/abc323/editorial/7357) | 時刻tに曲が切り替わる確率p[t] |
| [ABC342 F](https://atcoder.jp/contests/abc342/editorial/9345) | ディーラーの最終点数分布と、自分の状態からの最適勝率 |

## 確率DPとして確認した20問

| 問題 | タイトル | 役割 |
|---|---|---|
{table(prob)}

## 期待値DPとして確認した22問

| 問題 | タイトル | 役割 |
|---|---|---|
{table(expect)}

## データと検証

- [確率DP一覧・状態と遷移・根拠](probability_dp_problems.csv)
- [期待値DP一覧・状態と遷移・根拠](expectation_dp_problems.csv)
- [98候補の監査状態](probability_candidate_audit.csv)
- [全266タグの確認範囲](tag_validation_coverage.csv)：専門タグ以外の網羅性が保証されたとは扱わない。
- [全問の修正版](problems.csv)、[全対応](all_problems_tagged.csv)、[行列](problem_tag_matrix.csv)、[V3との差分](change_audit.csv)
- [監査の検証結果](probability_verification.json)、[追加テスト結果](probability_test_results.json)、[入力ハッシュ](probability_input_manifest.json)

原本の判断は `../probability_reviews.tsv`。タグ追加には根拠原文の箇所、状態の意味、遷移の説明、出典を保存しています。今回追加した38対応がT026・T029だけであること、全問収録、CSV/JSONL/行列、変更前後の差分、採用した全対応の根拠を照合しました。

既存の回帰テスト19件に加えて、追加テスト{tests['tests']}件を通過。双六・プレイリスト・Lottery・二項分布前計算を、小規模な全列挙の厳密有理数解と{tests['exact_comparisons']}ケースで照合しました。これは特定の状態解釈と遷移の検証であり、全266タグの精度・再現率の推定ではありません。

## 再生成

```powershell
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/tag_precision.py --output-dir output_v3_1 --additional-review-file abc_all/probability_reviews.tsv --baseline-dir output_v3 --version abc-all-266-evidence-v3.1-probability-audit
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/test_probability_audit.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/verify_probability_audit.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/report_probability_audit.py
```

V3のデータ本体は比較用に保存しています。新しいタグを他の実験やアプリに反映する場合は、どの版・どの確認範囲を使ったかを記録してください。
'''
 (out/'README.md').write_text(text,encoding='utf-8')
 p=ROOT/'README.md';old=p.read_text(encoding='utf-8-sig')
 marker='# 2026-11-23 確率DP・期待値DPの付け漏れ監査 V3.1'
 prefix=marker+'\n\n[V3.1の監査結果と修正版](output_v3_1/README.md)。V3の確率DPは付け漏れにより1問でした。状態値と遷移を確認し、確率DP20問・期待値DP22問を反映しました。全体の網羅性は未検証です。\n\n'
 if not old.startswith(marker):p.write_text(prefix+old,encoding='utf-8')
 p=ROOT/'output_v3/README.md';old=p.read_text(encoding='utf-8-sig')
 warning='> 追記：確率DP・期待値DPの重大な付け漏れを確認しました。[V3.1の監査結果](../output_v3_1/README.md)を参照してください。この版のタグ件数を、適用可能問題の総数として扱うことはできません。\n\n'
 if not old.startswith('> 追記：'):p.write_text(warning+old,encoding='utf-8')
 print(json.dumps(dict(report_written=True,probability_dp=len(prob),expectation_dp=len(expect)),ensure_ascii=False))

if __name__=='__main__':main()
