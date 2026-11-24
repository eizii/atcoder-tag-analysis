"""Reconcile main/concept outputs against the exact completed decision ledger."""
import csv,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from verify_dataset import verify
R=Path(__file__).resolve().parent.parent;W=R/'full_review';O=R/'output_v4'
def read(p,delimiter=','):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''),delimiter=delimiter))
def keyed(rows):
 result={(r['problem_id'],r['tag_id']):r['role'] for r in rows}
 assert len(result)==len(rows),'duplicate pair'
 return result
verify('output_v4')
ledger=read(W/'merged_full_reviews.tsv','\t');assert len(ledger)==3012
expected={};expected_analysis={}
for r in ledger:
 assert r['scope']=='full' and r['review_status']=='reviewed'
 for a in filter(None,r['accepted'].split(',')):
  t,role=a.split(':');target=expected if role in {'primary','alternative','supporting'} else expected_analysis;target[r['problem_id'],t]=role
manifest=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems']; aliases={p['contest_id']+'_'+p['problem_index'].lower():p['problem_id'] for p in manifest}; ids={p['problem_id'] for p in manifest}
main=keyed(read(O/'all_problems_tagged.csv'));analysis=keyed(read(O/'analysis_concept_assignments.csv'));allroles=keyed(read(O/'all_role_assignments.csv'))
assert main==expected and analysis==expected_analysis
assert not (main.keys()&analysis.keys())
assert allroles==dict(main,**{})|analysis
for fname,pairs in [('all_roles_problem_tag_matrix.csv',allroles),('analysis_concept_problem_tag_matrix.csv',analysis)]:
 actual={(r['problem_id'],t) for r in read(O/fname) for t,v in r.items() if t!='problem_id' and v=='1'}
 assert actual==set(pairs),fname
assert all(r['needs_review']=='0' and r['validation_status']=='assistant_reviewed' for r in read(O/'all_role_assignments.csv'))
assert not read(O/'review_queue.csv') and not read(O/'unresolved_problems.csv')
reviews=json.loads((O/'semantic_reviews.json').read_text(encoding='utf-8'))
for r in ledger:
 p=r['problem_id'];assert len(reviews[p])==1 and reviews[p][0]['reason']==r['reason']
for pid,t in [('abc055_c','T052'),('abc054_b','T118'),('abc170_d','T022'),('abc229_h','T036'),('abc382_g','T144'),('abc404_d','T017'),('abc405_g','T001'),('abc415_g','T264')]:
 pid=aliases.get(pid,pid);assert pid in ids,pid
 assert (pid,t) not in main,(pid,t,'known incidental/partial tag survived')
for pid,t,role in [('abc319_c','T029','alternative'),('abc360_e','T026','alternative'),('abc184_d','T026','primary'),('abc184_d','T029','alternative'),('abc395_f','T187','alternative'),('abc411_c','T003','alternative')]:
 assert main[pid,t]==role,(pid,t)
s=json.loads((O/'summary.json').read_text(encoding='utf-8'))
assert s['fully_reviewed_problems']==3012 and s['partially_reviewed_problems']==0 and s['accuracy_estimate'] is None
assert s['merged_reviews_sha256']==hashlib.sha256((W/'merged_full_reviews.tsv').read_bytes()).hexdigest()
report=dict(checks_passed=True,problem_count=len(ledger),main_pairs=len(main),separate_concept_pairs=len(analysis),all_review_decisions_match_outputs=True,role_separation_verified=True,unresolved=0,known_source_and_role_regressions_passed=True,independent_gold_accuracy_estimate=None)
(O/'full_review_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
