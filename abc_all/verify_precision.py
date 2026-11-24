"""Independent reconciliation of V3 labels, reviews, source hashes and the delta."""
import csv,hashlib,json
from collections import Counter
from pathlib import Path
from verify_dataset import verify,read_csv
from collect_statements import save_json
from tag_precision import read_jsonl,read_reviews,fingerprint
R=Path(__file__).resolve().parent

def main():
 out=R/'output_v3';verify('output_v3')
 summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
 docs={d['problem_id']:d for d in read_jsonl(R/'corpus_sources.jsonl')}
 records={d['problem_id']:d for d in read_jsonl(out/'problems_tagged.jsonl')}
 reviews=read_reviews(docs)
 assignments=read_csv(out/'all_problems_tagged.csv');by={(r['problem_id'],r['tag_id']):r for r in assignments}
 reviewed={(r['problem_id'],r['tag_id']) for r in assignments if r['validation_status']=='assistant_reviewed'}
 reviewed_table={(r['problem_id'],r['tag_id']) for r in read_csv(out/'reviewed_assignments.csv')}
 assert reviewed==reviewed_table
 names={r['tag_id'] for r in read_csv(out/'tag_catalog.csv')}
 reviewed_matrix=read_csv(out/'reviewed_problem_tag_matrix.csv')
 assert {r['problem_id'] for r in reviewed_matrix}==set(docs)
 assert {(r['problem_id'],t) for r in reviewed_matrix for t in names if r[t]=='1'}==reviewed
 assert all(r[t] in {'0','1'} for r in reviewed_matrix for t in names)
 expected_reviewed=set();explicit_rejected=set();decisions=[]
 for pid,rs in reviews.items():
  expected={};full=False
  for r in rs:
   if r['scope']=='full':expected={};full=True
   for t in r['rejected']:
    expected.pop(t,None);explicit_rejected.add((pid,t))
    decisions.append(dict(problem_id=pid,tag_id=t,decision='exclude_from_selected_solution_tags',role='',reason=r['reason'],evidence_quote=r['evidence_quote'],evidence_urls=' | '.join(r['evidence_urls']),scope=r['scope']))
   for t,role in r['accepted'].items():
    expected[t]=role
    decisions.append(dict(problem_id=pid,tag_id=t,decision='include',role=role,reason=r['reason'],evidence_quote=r['evidence_quote'],evidence_urls=' | '.join(r['evidence_urls']),scope=r['scope']))
  rec=records[pid]
  assert rec['review_scope']==('full' if full else 'selected_tags')
  if full:assert set(rec['tag_ids'])==set(expected),(pid,rec['tag_ids'],expected)
  for t,role in expected.items():
   expected_reviewed.add((pid,t));a=by[pid,t]
   assert a['role']==role and a['needs_review']=='0'
   assert a['validation_status']=='assistant_reviewed'
   assert all(e['validation_status']=='assistant_reviewed' for e in rec['labels'][t])
 assert reviewed==expected_reviewed
 assert not (set(by)&explicit_rejected)
 for key,a in by.items():
  if key not in reviewed:assert a['needs_review']=='1' and a['validation_status']=='not_independently_reviewed'
 baseline={d['problem_id']:d for d in read_jsonl(R/'output_v2_uniform/problems_tagged.jsonl')}
 old={(pid,t) for pid,d in baseline.items() for t in d['tag_ids']};new=set(by)
 changes=read_csv(out/'change_audit.csv')
 assert {(r['problem_id'],r['tag_id']) for r in changes if r['action']=='add'}==new-old
 assert {(r['problem_id'],r['tag_id']) for r in changes if r['action']=='remove'}==old-new
 rows=read_csv(out/'problems.csv');queue=read_csv(out/'review_queue.csv')
 assert {r['problem_id'] for r in queue}=={r['problem_id'] for r in rows if r['review_scope']!='full'}
 assert summary['assistant_semantic_reviewed_problems']==len(reviews)
 assert summary['fully_reviewed_problems']==sum(r['review_scope']=='full' for r in rows)
 assert summary['partially_reviewed_problems']==sum(r['review_scope']=='selected_tags' for r in rows)
 assert summary['reviewed_assignments']==len(reviewed)
 assert summary['changed_problems']==len({pid for pid,t in old^new})
 assert summary['added_pairs']==len(new-old) and summary['removed_pairs']==len(old-new)
 assert summary['source_corpus_sha256']==fingerprint(R/'corpus_sources.jsonl')
 assert summary['taxonomy_sha256']==fingerprint(R/'taxonomy.json')
 assert summary['review_file_sha256']==fingerprint(R/'precision_reviews.tsv')
 assert summary['supplemental_sources_sha256']==fingerprint(R/'precision_sources.jsonl')
 sources=read_jsonl(R/'precision_sources.jsonl')
 for row in sources:
  e=row['editorial'];assert row['problem_id'] in e['task_ids']
  assert e['text_sha256']==hashlib.sha256(e['text'].encode()).hexdigest()
  cache=R/'precision_cache'/('editorial_'+e['url'].rsplit('/',1)[-1]+'.html')
  if cache.exists():assert row['raw_sha256']==fingerprint(cache)
 from tag_all import csv_write
 csv_write(out/'reviewed_decisions.csv',['problem_id','tag_id','decision','role','reason','evidence_quote','evidence_urls','scope'],decisions)
 core={(r['problem_id'],r['tag_id']) for r in read_csv(out/'reviewed_core_assignments.csv')}
 assert core=={(r['problem_id'],r['tag_id']) for r in assignments if r['validation_status']=='assistant_reviewed' and r['role'] in {'primary','alternative'}}
 cm=read_csv(out/'reviewed_core_problem_tag_matrix.csv')
 assert {(r['problem_id'],t) for r in cm for t in names if r[t]=='1'}==core
 inputs=['report_precision.py','finalize_precision_docs.py','validate_review_witnesses.py','manifest.json','taxonomy.json','corpus_sources.jsonl','precision_sources.jsonl','precision_reviews.tsv','tag_rules.json','tag_precision.py','precision_policy.py','tag_all.py','evidence_scope.py','collect_statements.py','verify_precision.py','test_precision.py','refresh_precision_sources.py']
 hashes={p:fingerprint(R/p) for p in inputs}
 save_json(out/'input_manifest.json',dict(version=summary['version'],sha256=hashes))
 audited_ids=set(reviews)
 reviewed_added={(pid,t) for pid,t in new-old if pid in audited_ids and (pid,t) in reviewed}
 reviewed_removed={(pid,t) for pid,t in old-new if pid in audited_ids}
 report=dict(checks_passed=True,problem_count=len(records),reviewed_problems=len(reviews),fully_reviewed_problems=summary['fully_reviewed_problems'],partially_reviewed_problems=summary['partially_reviewed_problems'],reviewed_assignments=len(reviewed),explicit_exclusion_decisions=len(explicit_rejected),reviewed_added_pairs=len(reviewed_added),removed_pairs_on_reviewed_problems=len(reviewed_removed),added_pairs=len(new-old),removed_pairs=len(old-new),changed_problems=summary['changed_problems'],source_hashes_checked=True,review_quotes_checked=True,curated_matrix_checked=True,delta_checked=True,independent_human_review=False,accuracy_estimate=None)
 save_json(out/'precision_verification.json',report)
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
