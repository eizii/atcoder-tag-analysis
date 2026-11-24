from record_resolution_0 import *
import sys
sys.path.insert(0,str(R))
from tag_precision import read_reviews
validated=read_reviews(DOC,OUT)
plan=json.loads((R/'full_review/root_resolution_plan.json').read_text(encoding='utf-8'))['agent_0']
assert set(rows)==set(plan)|{'abc426_g'},(set(plan)-set(rows),set(rows)-set(plan))
tax={x['tag_id'] for x in json.loads((R/'taxonomy.json').read_text(encoding='utf-8'))}
for pid,row in rows.items():
 for a in row['accepted'].split(','):
  if a: assert a.split(':')[0] in tax,(pid,a)
 assert row['scope']=='full' and row['review_status']=='reviewed'
print('VALIDATED',len(rows),'rows; designated',len(plan),'plus abc426_g')
print('PROBABILITY EXPECTATION ADOPTED')
report=[]
for filename in ['shard_0.tsv','root_resolution_0.tsv']:
 for row in csv.DictReader((R/'full_review'/filename).open(encoding='utf-8-sig'),delimiter='\t'):
  tags=[s for s in row['accepted'].split(',') if s.split(':')[0] in ('T026','T029')]
  removed=[s for s in row['rejected'].split(',') if s in ('T026','T029')]
  if tags or removed:
   report.append(dict(problem_id=row['problem_id'],accepted=','.join(tags),removed=','.join(removed),reason=row['reason'],file=filename))
for x in report: print(json.dumps(x,ensure_ascii=False))
(R/'full_review/probability_report_0.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8-sig')
