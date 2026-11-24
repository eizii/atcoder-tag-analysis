"""Reconcile the targeted probability audit against the frozen V3 baseline."""
import csv,json,hashlib
from collections import Counter
from pathlib import Path
from tag_precision import ROOT,read_jsonl,read_reviews,fingerprint
from tag_all import csv_write,normalize
from verify_dataset import verify,read_csv
from audit_probability_dp import PATTERN

def main():
 out=ROOT/'output_v3_1';verify('output_v3_1')
 docs={d['problem_id']:d for d in read_jsonl(ROOT/'corpus_sources.jsonl')}
 reviews=read_reviews(docs,ROOT/'probability_reviews.tsv')
 prior=read_csv(ROOT/'output_v3/all_problems_tagged.csv');new=read_csv(out/'all_problems_tagged.csv')
 old_counts=Counter(r['tag_id'] for r in prior)
 assert old_counts['T029']==1 and old_counts['T026']==3
 before={(r['problem_id'],r['tag_id']) for r in prior};after={(r['problem_id'],r['tag_id']) for r in new}
 requested={(pid,t) for pid,rs in reviews.items() for r in rs for t in r['accepted']}
 assert all(t in {'T026','T029'} for pid,t in requested)
 assert after==before|requested
 by={(r['problem_id'],r['tag_id']):r for r in new}
 for pid,rs in reviews.items():
  for r in rs:
   for t,role in r['accepted'].items():
    assert by[pid,t]['role']==role and by[pid,t]['validation_status']=='assistant_reviewed'
    assert by[pid,t]['needs_review']=='0'
 s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
 assert s['baseline_directory']=='output_v3'
 assert s['additional_review_files_sha256']['probability_reviews.tsv']==fingerprint(ROOT/'probability_reviews.tsv')
 assert s['source_corpus_sha256']==fingerprint(ROOT/'corpus_sources.jsonl')
 assert s['taxonomy_sha256']==fingerprint(ROOT/'taxonomy.json')
 changes=read_csv(out/'change_audit.csv')
 assert {(r['problem_id'],r['tag_id']) for r in changes if r['action']=='add'}==after-before
 assert not any(r['action']=='remove' for r in changes)
 with (ROOT/'probability_reference_methods.tsv').open(encoding='utf-8-sig') as f:notes={r['problem_id']:r for r in csv.DictReader(f,delimiter='\t')}
 for pid,r in notes.items():
  assert any(normalize(r['evidence_quote']) in normalize(e['text']) for e in docs[pid]['editorials'])
 rows=read_csv(out/'problems.csv');rowby={r['problem_id']:r for r in rows}
 audit=[]
 for pid,d in docs.items():
  tids=set(rowby[pid]['tag_ids'].split(' | '))
  if not (PATTERN.search(d['statement'].split('入力例')[0]) or {'T026','T029'}&tids):continue
  tags={t for t in ['T026','T029'] if (pid,t) in after}
  confirmed={t for t in tags if by[pid,t]['validation_status']=='assistant_reviewed'}
  status='confirmed_dp' if confirmed else 'other_reviewed_solution' if pid in notes else 'pending_semantic_review'
  rs=reviews.get(pid,[])
  audit.append(dict(problem_id=pid,title=d['title'],url=d['url'],status=status,probability_dp='confirmed' if 'T029' in confirmed else 'not_assessed',expectation_dp='confirmed' if 'T026' in confirmed else 'not_assessed',state_and_transition=' | '.join(r['reason'] for r in rs) or notes.get(pid,{}).get('reason',''),evidence_quote=' | '.join(r['evidence_quote'] for r in rs) or notes.get(pid,{}).get('evidence_quote',''),evidence_urls=' | '.join(sorted({url for r in rs for url in r['evidence_urls']}))))
 csv_write(out/'probability_candidate_audit.csv',list(audit[0]),audit)
 probability=[r for r in new if r['tag_id']=='T029'];expectation=[r for r in new if r['tag_id']=='T026']
 assert len(probability)==20 and all(r['validation_status']=='assistant_reviewed' for r in probability)
 assert len(expectation)==22 and all(r['validation_status']=='assistant_reviewed' for r in expectation)
 csv_write(out/'probability_dp_problems.csv',list(probability[0]),probability)
 csv_write(out/'expectation_dp_problems.csv',list(expectation[0]),expectation)
 for name,records in [('probability_dp_problems',probability),('expectation_dp_problems',expectation)]:
  enriched=[]
  base_reviews=read_reviews(docs)
  for rec in records:
   entries=base_reviews.get(rec['problem_id'],[])+reviews.get(rec['problem_id'],[])
   evidence=next(r for r in reversed(entries) if rec['tag_id'] in r['accepted'])
   enriched.append(dict(rec,state_and_transition=evidence['reason'],evidence_quote=evidence['evidence_quote']))
  csv_write(out/(name+'.csv'),list(enriched[0]),enriched)
 catalog=read_csv(out/'tag_catalog.csv');tag_audit=[]
 for tag in catalog:
  assigned=[r for r in new if r['tag_id']==tag['tag_id']]
  n=sum(r['validation_status']=='assistant_reviewed' for r in assigned)
  tag_audit.append(dict(tag,assistant_reviewed_pairs=n,automatic_unreviewed_pairs=len(assigned)-n,recall_validation='targeted_positive_cases_only' if tag['tag_id'] in {'T026','T029'} else 'not_established',note='Observed label count is not an independently verified count of applicable problems.'))
 csv_write(out/'tag_validation_coverage.csv',list(tag_audit[0]),tag_audit)
 report=dict(checks_passed=True,baseline_probability_dp=old_counts['T029'],revised_probability_dp=len(probability),baseline_expectation_dp=old_counts['T026'],revised_expectation_dp=len(expectation),added_pairs=len(after-before),removed_pairs=len(before-after),changed_problems=len({p for p,t in after^before}),new_review_problems=len(reviews),candidate_problems=len(audit),candidate_status_counts=dict(Counter(r['status'] for r in audit)),all_added_labels_semantically_reviewed=True,global_tag_recall_verified=False,interpretation='20 and 22 are confirmed labeled subsets, not guaranteed exhaustive totals.')
 (out/'probability_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 files=['tag_precision.py','precision_policy.py','precision_reviews.tsv','probability_reviews.tsv','probability_reference_methods.tsv','corpus_sources.jsonl','precision_sources.jsonl','tag_rules.json','test_probability_audit.py','verify_probability_audit.py','audit_probability_dp.py','report_probability_audit.py']
 (out/'probability_input_manifest.json').write_text(json.dumps({p:fingerprint(ROOT/p) for p in files},indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
