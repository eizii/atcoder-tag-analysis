"""Reconcile V3.2 and publish the targeted semantic follow-up, with explicit limits."""
import csv,json,re
from collections import Counter
from pathlib import Path
from tag_precision import ROOT,read_jsonl,read_reviews,fingerprint
from tag_all import csv_write,normalize
from verify_dataset import verify,read_csv

OUT=ROOT/'output_v3_2'
def write_json(name,obj):
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
 verify('output_v3_2')
 docs={d['problem_id']:d for d in read_jsonl(ROOT/'corpus_sources.jsonl')}
 old=read_csv(ROOT/'output_v3_1/all_problems_tagged.csv');new=read_csv(OUT/'all_problems_tagged.csv')
 before={(r['problem_id'],r['tag_id']):r for r in old};after={(r['problem_id'],r['tag_id']):r for r in new}
 decisions=read_csv_tsv(ROOT/'validity_followup_decisions.tsv');decisionby={r['problem_id']:r for r in decisions}
 reviews=read_reviews(docs,ROOT/'validity_followup_reviews.tsv')
 expected=set(before)
 for pid,rr in reviews.items():
  for r in rr:
   assert r['scope']=='selected_tags'
   expected-={(pid,t) for t in r['rejected']}
   expected|={(pid,t) for t in r['accepted']}
   for t,role in r['accepted'].items():
    assert after[pid,t]['role']==role
    assert after[pid,t]['validation_status']=='assistant_reviewed'
    assert after[pid,t]['needs_review']=='0'
 assert set(after)==expected
 oldaudit=read_csv(ROOT/'output_v3_1/probability_candidate_audit.csv')
 pending={r['problem_id'] for r in oldaudit if r['status']=='pending_semantic_review'}
 closed={r['problem_id'] for r in decisions if r['origin']=='previous_pending_44'}
 assert len(pending)==44 and closed==pending
 assert len(decisions)==len(decisionby)==49
 for r in decisions:
  pid=r['problem_id'];d=docs[pid]
  sources=[d['statement']] if r['source_indices']=='statement' else [e['text'] for e in d['editorials']]
  assert any(normalize(r['evidence_quote']) in normalize(t) for t in sources),(pid,r['evidence_quote'])
  indices=[] if r['source_indices']=='statement' else [i for i,e in enumerate(d['editorials']) if normalize(r['evidence_quote']) in normalize(e['text'])]
  urls=sorted({d['editorials'][i].get('url') or d['url'] for i in indices}) if indices else [d['url']]
  r['title']=d['title'];r['url']=d['url'];r['evidence_urls']=' | '.join(urls)
  contexts=[]
  for source in sources:
   text=normalize(source);anchor=normalize(r['evidence_quote']);pos=text.find(anchor)
   if pos>=0:contexts.append(text[max(0,pos-100):pos+len(anchor)+200])
  r['evidence_context']=' | '.join(contexts)
  r['reviewer']='assistant';r['independent_human_review']=False
 csv_write(OUT/'followup_decisions.csv',list(decisions[0]),decisions)
 summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
 assert summary['baseline_directory']=='output_v3_1'
 for f in ['probability_reviews.tsv','validity_followup_reviews.tsv']:
  assert summary['additional_review_files_sha256'][f]==fingerprint(ROOT/f)
 assert summary['source_corpus_sha256']==fingerprint(ROOT/'corpus_sources.jsonl')
 assert summary['taxonomy_sha256']==fingerprint(ROOT/'taxonomy.json')
 changed=read_csv(OUT/'change_audit.csv')
 assert {(r['problem_id'],r['tag_id']) for r in changed if r['action']=='add'}==set(after)-set(before)
 assert {(r['problem_id'],r['tag_id']) for r in changed if r['action']=='remove'}==set(before)-set(after)
 # A role correction must be visible even when the binary pair did not change.
 rolechanges=[dict(problem_id=p,tag_id=t,previous_role=before[p,t]['role'],new_role=r['role'],evidence_urls=r['evidence_urls']) for (p,t),r in after.items() if (p,t) in before and before[p,t]['role']!=r['role']]
 csv_write(OUT/'role_changes.csv',['problem_id','tag_id','previous_role','new_role','evidence_urls'],rolechanges)
 assert after['abc313_f','T177']['role']=='analysis_concept'
 assert not any(r['problem_id']=='abc313_f' and r['tag_id']=='T177' for r in new if r['role'] in {'primary','alternative'})

 allreviews=read_reviews(docs)
 for f in ['probability_reviews.tsv','validity_followup_reviews.tsv']:
  for pid,rs in read_reviews(docs,ROOT/f).items():allreviews.setdefault(pid,[]).extend(rs)
 counts={}
 for tid,name in [('T029','probability_dp_problems.csv'),('T026','expectation_dp_problems.csv')]:
  enriched=[]
  for r in new:
   if r['tag_id']!=tid:continue
   assert r['validation_status']=='assistant_reviewed'
   ev=next(ev for ev in reversed(allreviews[r['problem_id']]) if tid in ev['accepted'])
   enriched.append(dict(r,state_and_transition=ev['reason'],evidence_quote=ev['evidence_quote'],classification_detail=decisionby.get(r['problem_id'],{}).get('decision','previous_confirmed_state_transition')))
  csv_write(OUT/name,list(enriched[0]),enriched);counts[tid]=len(enriched)
 # The numeric results are measured from assignments, not semantic proof assertions.
 base_notes={r['problem_id']:r for r in read_csv_tsv(ROOT/'probability_reference_methods.tsv')}
 oldby={r['problem_id']:r for r in oldaudit};audit=[]
 for pid in docs:
  if pid not in oldby and pid not in decisionby:continue
  d=docs[pid];rr=decisionby.get(pid);prior=oldby.get(pid,{})
  tags=[t for t in ('T029','T026') if (pid,t) in after]
  status='confirmed_dp_assignment' if tags else 'reference_method_assessed'
  assert tags or pid in decisionby or pid in base_notes
  evs=[ev for ev in allreviews.get(pid,[]) if {'T029','T026'}&set(ev['accepted'])]
  reason=rr['state_and_transition'] if rr else ' | '.join(ev['reason'] for ev in evs) or base_notes.get(pid,{}).get('reason','')
  quote=rr['evidence_quote'] if rr else ' | '.join(ev['evidence_quote'] for ev in evs) or base_notes.get(pid,{}).get('evidence_quote','')
  urls=rr['evidence_urls'] if rr else ' | '.join(sorted({url for ev in evs for url in ev['evidence_urls']}))
  audit.append(dict(problem_id=pid,title=d['title'],url=d['url'],status=status,source_scope='followup_reference_method' if rr else 'previous_targeted_audit',probability_dp='confirmed' if 'T029' in tags else 'reference_method_only_not_global_negative',expectation_dp='confirmed' if 'T026' in tags else 'reference_method_only_not_global_negative',decision=rr['decision'] if rr else prior.get('status',''),state_and_transition=reason,evidence_quote=quote,evidence_urls=urls,boundary_note=rr['boundary_note'] if rr else '確認済みの特定解法。全ての別解・全体再現率は未検証。'))
 csv_write(OUT/'probability_candidate_audit.csv',list(audit[0]),audit)
 assert {r['problem_id'] for r in audit}==set(oldby)|set(decisionby)
 assert len(audit)==103
 # Keep source-side keyword screening separate from semantic review.
 screened=[]
 for pid,d in docs.items():
  if pid in oldby:continue
  contexts=[]
  for i,e in enumerate(d['editorials']):
   text=re.sub(r'\s+',' ',e['text'])
   m=re.search(r'確率|期待値|probability|expected',text,re.I)
   if m:contexts.append(dict(source_index=i,url=e.get('url') or d['url'],context=text[max(0,m.start()-70):m.end()+130]))
  if contexts:screened.append(dict(problem_id=pid,title=d['title'],screening_status='semantically_assessed_in_followup' if pid in decisionby else 'context_screen_only',contexts=json.dumps(contexts,ensure_ascii=False),limitation='Keyword screening is not a full semantic audit; may include hash collision bounds, expected runtime, references, or shared text.'))
 csv_write(OUT/'editorial_expansion_screen.csv',list(screened[0]),screened)
 # Role-restricted matrices are useful for downstream clustering.
 core=[r for r in new if r['validation_status']=='assistant_reviewed' and r['role'] in {'primary','alternative'}]
 csv_write(OUT/'reviewed_core_assignments.csv',list(new[0]),core)
 tids=[t['tag_id'] for t in json.loads((ROOT/'taxonomy.json').read_text(encoding='utf-8'))]
 pairs={(r['problem_id'],r['tag_id']) for r in core};problems=read_csv(OUT/'problems.csv')
 csv_write(OUT/'reviewed_core_problem_tag_matrix.csv',['problem_id',*tids],[dict(problem_id=r['problem_id'],**{t:int((r['problem_id'],t) in pairs) for t in tids}) for r in problems])
 coverage=[]
 for r in read_csv(OUT/'tag_catalog.csv'):
  assigned=[a for a in new if a['tag_id']==r['tag_id']]
  coverage.append(dict(r,assistant_reviewed_pairs=sum(a['validation_status']=='assistant_reviewed' for a in assigned),recall_validation='not_established',note='Targeted positive cases and selected reference methods are audited; an unassigned tag is not a negative label.'))
 csv_write(OUT/'tag_validation_coverage.csv',list(coverage[0]),coverage)
 witness=json.loads((OUT/'followup_solution_witness_verification.json').read_text(encoding='utf-8'))
 assert witness['checks_passed']
 expected_witnesses={'wipeout_hidden_permutations','sugoroku_projected_survival','half_baked_merge_vs_outcomes','half_baked_single_pair_normalization','separate_digits_expectation_vs_cuts','removing_people_first_moment_vs_process','dye_hessenberg_structure','dye_potential_vs_full_markov','anti_ddos_probability_states_vs_substitutions'}
 assert expected_witnesses<=set(witness['comparisons'])
 rolecounts={t:dict(Counter(r['role'] for r in new if r['tag_id']==t)) for t in ('T029','T026')}
 result=dict(checks_passed=True,previous_pending_candidates=44,previous_pending_candidates_assessed=len(closed),followup_semantic_decisions=len(decisions),expanded_semantic_candidates=len(set(decisionby)-set(oldby)),all_targeted_candidates=len(audit),candidate_status_counts=dict(Counter(r['status'] for r in audit)),probability_dp_count=counts['T029'],expectation_dp_count=counts['T026'],tag_role_counts=rolecounts,added_pairs=len(set(after)-set(before)),removed_pairs=len(set(before)-set(after)),binary_changed_problems=len({p for p,t in set(after)^set(before)}),role_changed_problems=len({r['problem_id'] for r in rolechanges}),role_changes=len(rolechanges),previous_pending_decision_counts=dict(Counter(r['decision'] for r in decisions if r['origin']=='previous_pending_44')),new_semantic_review_problems=len(reviews),global_precision_estimated=False,global_recall_estimated=False,independent_human_review=False,editorial_context_screen_count=len(screened),context_screen_only_count=sum(r['screening_status']=='context_screen_only' for r in screened),witness_comparisons=sum(v for k,v in witness['comparisons'].items() if not k.endswith('enumerated_histories')),independent_hidden_permutations=witness['comparisons']['wipeout_enumerated_histories'],limits='Counts are confirmed assignments under the stated role-sensitive policy, not a proof of exhaustive applicability over 3012 tasks or 266 tags.')
 write_json('followup_verification.json',result)
 files=['corpus_sources.jsonl','precision_sources.jsonl','precision_reviews.tsv','probability_reviews.tsv','probability_reference_methods.tsv','validity_followup_reviews.tsv','validity_followup_decisions.tsv','record_validity_followup.py','validate_followup_witnesses.py','verify_validity_followup.py','tag_precision.py','precision_policy.py','tag_rules.json','test_precision.py','test_probability_audit.py']
 write_json('followup_input_manifest.json',{p:fingerprint(ROOT/p) for p in files})
 publish(result,decisions,rolechanges,new,witness,summary)
 print(json.dumps(result,ensure_ascii=False))

def read_csv_tsv(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))

def publish(result,decisions,rolechanges,assignments,witness,summary):
 lines=['# タグ妥当性の再検証 V3.2','', '2026-11-23。従来と同じABC 3,012問・266タグ。前回保留した44問は、参考解法の状態値・遷移・全制約での計算量まで確認しました。解説側からも候補を追加し、今回の判断記録は49問です。**全266タグの意味的な検証完了や、正解率・再現率の保証ではありません。**','', '## 今回の結果','', '| 項目 | V3.1 | V3.2 |','|---|---:|---:|',f"| 確率DP T029（補助を含む確認済み対応） | 20 | {result['probability_dp_count']} |",f"| 期待値DP T026（別解・補助を含む確認済み対応） | 22 | {result['expectation_dp_count']} |",f"| 問題–タグ対応 | 5,143 | {summary['assigned_pairs']:,} |",f"| タグあり | 2,256 | {summary['tagged_problem_count']:,} |",f"| 正のタグ対応について個別確認した問題 | 174 | {summary['assistant_semantic_reviewed_problems']} |",'',f"タグ対応は{result['binary_changed_problems']}問に{result['added_pairs']}件追加、削除0件です。これに加えABC313 F等の役割を補正しました。主解・別解・補助・証明の概念を同じ件数として混同しないため、役割別の一覧と行列も出しています。",'', '| タグ | 主解 | 別解 | 補助 |','|---|---:|---:|---:|']
 for tid,name in [('T029','確率DP'),('T026','期待値DP')]:
  c=result['tag_role_counts'][tid];lines.append(f"| {name} | {c.get('primary',0)} | {c.get('alternative',0)} | {c.get('supporting',0)} |")
 lines+=['','**25問ずつは、現在根拠を確認して付与した集合の大きさです。真の適用可能問題数とは断定しません。** 前回の候補98問は43問でいずれかのDPを確認、55問では確認した解法を別手法として記録。追加5問を含む103問では45問がDP確認・58問が参考解法の別手法の判断です。別手法という記録は、他のDP別解が存在しないという負例ではありません。','', '## 追加したDPと判断の境界','', '| 問題 | 追加 | 状態・計算方法 |','|---|---|---|', '| [ABC301 F](https://atcoder.jp/contests/abc301/editorial/6331) | 確率DP・文字列DP | 接頭辞の29状態の確率。問題文が数え上げなので前回の問題文検索では候補から漏れていた |', '| [ABC345 G](https://atcoder.jp/contests/abc345/editorial/9549) | 確率DP（補助） | 位置分布をF(x)^tで伝播し、未到達確率を分割統治・反転公式で抽出 |', '| [ABC439 G](https://atcoder.jp/contests/abc439/editorial/14995) | 確率DP（補助） | 同じ確率遷移をpower projectionで一括計算 |', '| [ABC473 G](https://atcoder.jp/contests/abc473/editorial/24872) | 確率DP（補助） | 余分な操作回数の分布を確率母関数の積で併合 |', '| [ABC481 G](https://atcoder.jp/contests/abc481/editorial/27925) | 確率DP（補助） | パンケーキの順位分布と重み付き和を区間で併合しFFTで高速化 |', '| [ABC238 H](https://atcoder.jp/contests/abc238/editorial/3361) | 期待値DP（補助）・区間DP | 区間の手順数と非正規化コスト一次モーメントを同時に伝播 |', '| [ABC249 H](https://atcoder.jp/contests/abc249/editorial/3842) | 期待値DP（補助） | 期待時間を色個数別ポテンシャルへ分解し、三角化した再帰を計算 |', '| [ABC224 F](https://atcoder.jp/contests/abc224/editorial/2830) | 期待値DP（別解） | 公式別解の線形状態(s,x)を確率平均へ変換。E[s′]=E[s]+E[x]/2、E[x′]=5E[x]+d |','', '高速化された確率遷移はV3.1と同じ方針で含めています。ただし、素朴な分布DPが時間制限内に収まるとはしていません。ABC345 G・439 G・473 G・481 Gは中心の手法が多項式・畳み込みであり、専門DPタグは補助として分離しています。','', '期待値DPでは条件付き期待値に加え、確率的な過程の一次モーメントや、期待値方程式を順次計算する変換状態を補助として含めています。ABC238 Hのcostはそのまま期待値ではなく、ABC249 Hのgは残り期待時間そのものではありません。この違いを状態の説明に残しています。','', '一方、どんな数え上げDPにも後から分母を付けて確率DPと呼ぶ規則は採りません。ABC216 Hの符号付きLGV行列式DP、ABC242 Hの被覆部分集合数、ABC253 Hの森数、ABC272 Hの包除用個数、ABC321 Gの連結配線数、ABC331 Gの包除・カード部分集合数は、確認した参考解法では数え上げDPとして区別しています。ABC301 Fは公式解説に確率状態と遷移の明示がある点も確認しています。','', 'ABC261 D・313 Fの最大化DP、平均の閉形式、全列挙、期待値の線形性のみの解法も区別しました。ABC313 Fの二項係数は証明用の別の等式なので、T177をanalysis_conceptに変更し、主手法一覧へ混ざらないようにしました。','', '## 独立した小規模照合','',f"有理数の厳密計算で{result['witness_comparisons']:,}比較を実行しました。さらにWipeoutの隠れたカード配置{result['independent_hidden_permutations']:,}通りを全列挙しました。",'', '- Sugoroku：出目列の再帰列挙と、位置分布の母関数から得る初回到達分布を比較。','- Wipeout：実際の未知カード選択のシミュレーションと、各kの確率因子の積を比較。','- Half-Baked：全選択結果のソートと、区間併合の結果を比較。同値のパンケーキを含むケースも確認。','- Removing People：実際の円環から一人ずつ除く確率過程と、区間のコスト一次モーメントを比較。','- Dye Color：N=2,3の全状態の吸収マルコフ方程式と、色個数別ポテンシャルを比較。','- Separate Digits：+の全配置と、二つの期待値状態の更新を比較。','- Anti-DDoS：縮小した大小文字集合の全置換と、同じ状態構造の確率DPを比較。','', 'これらは状態の意味・式変形の検証です。高速FFT実装の全制約テストや、全データの正解率を保証するものではありません。既存の回帰テスト19件と確率監査テスト8件も通過しています。','', '**出典の内部不一致**：ABC481 Gの保存済み解説本文の「定式化2」のMには選択確率1/2が欠けて見えますが、同じ出典の実装cmには1/2があります。N=1, A=1, B=2で期待値3/2となり、係数を省くと3になります。今回は実装の正規化を採用して全列挙と照合しました。出典本文は書き換えていません。','', '## 参照ファイルと残る範囲','', '- [今回49問の判断・原文・理由](followup_decisions.csv)、[タグ追加差分](change_audit.csv)、[役割の変更](role_changes.csv)。','- [確率DPの全25問](probability_dp_problems.csv)、[期待値DPの全25問](expectation_dp_problems.csv)。各行に状態・遷移と原文を記録。','- [103問の候補監査](probability_candidate_audit.csv)。未付与を適用不可能の意味で扱わないでください。','- [全問の状態](problems.csv)、[全対応](all_problems_tagged.csv)、[全行列](problem_tag_matrix.csv)。自動候補を含むためvalidation_statusを参照。','- [確認した主解・別解のみ](reviewed_core_assignments.csv)、[その行列](reviewed_core_problem_tag_matrix.csv)。証明・補助は除外。','- [266タグの確認範囲](tag_validation_coverage.csv)、[解説語句の追加スクリーニング](editorial_expansion_screen.csv)。スクリーニングだけの問題は意味的確認済みではありません。','- [整合性検証](followup_verification.json)、[解法照合](followup_solution_witness_verification.json)、[入力ハッシュ](followup_input_manifest.json)。','', f"全3,012問のうち、正の対応を個別確認した問題は{summary['assistant_semantic_reviewed_problems']}問、記録した解法の全タグを点検した問題は85問です。今回49問の参考解法確認には、専門DPを採用しない理由だけを点検した問題も含むため、この数字と合算しません。自動タグは多数残り、未判定の問題は{summary['unresolved_problem_count']}問です。無作為標本・独立した正解ラベルによる全体精度の評価はまだ行っていません。",'', '## 再生成','', '元のV3・V3.1およびクラスタリング結果は保存し、今回の結果はoutput_v3_2に分離しています。既存の入力でオフライン再生成できます。','', '```powershell', '.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/record_validity_followup.py', '.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/tag_precision.py --output-dir output_v3_2 --additional-review-file abc_all/probability_reviews.tsv --additional-review-file abc_all/validity_followup_reviews.tsv --baseline-dir output_v3_1 --version abc-all-266-evidence-v3.2-validity-followup', '.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/validate_followup_witnesses.py', '.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/verify_validity_followup.py', '```', '', '## 前回保留44問の判断一覧','', '| 問題 | 今回の判断 | 計算量 |','|---|---|---|']
 for r in decisions:
  if r['origin']=='previous_pending_44':lines.append(f"| [{r['problem_id']}]({r['url']}) {r['title']} | {r['decision']} | {r['complexity']} |")
 (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 root=ROOT/'README.md';text=root.read_text(encoding='utf-8-sig');marker='# 2026-11-23 妥当性再検証 V3.2'
 if marker not in text:root.write_text(marker+'\n\n[再検証結果・修正版](output_v3_2/README.md)。前回保留44問と追加5問の参考解法を確認し、確率DP25問・期待値DP25問を根拠付きで収録しました（補助・別解を含む）。全266タグの意味的検証は未完了です。\n\n'+text,encoding='utf-8')
 old=ROOT/'output_v3_1/README.md';text=old.read_text(encoding='utf-8-sig')
 if '../output_v3_2/README.md' not in text:old.write_text('> 後続の[妥当性再検証V3.2](../output_v3_2/README.md)で、保留44問の参考解法と候補漏れを追加確認しました。この版は履歴として保存しています。\n\n'+text,encoding='utf-8')

if __name__=='__main__':main()
