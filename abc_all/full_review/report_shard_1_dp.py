import csv,json
from pathlib import Path
R=Path('abc_all');rows=list(csv.DictReader((R/'full_review/shard_1.tsv').open(encoding='utf-8-sig'),delimiter='\t'));old={r['problem_id']:r for r in csv.DictReader((R/'output_v3_2/problems.csv').open(encoding='utf-8-sig'))}
a=[];removed=[]
for r in rows:
 tags=dict(x.split(':') for x in r['accepted'].split(',') if x)
 for t in ('T026','T029'):
  if t in tags:a.append(dict(problem_id=r['problem_id'],tag_id=t,role=tags[t],reason=r['reason']))
  elif t in old[r['problem_id']]['tag_ids']:removed.append(dict(problem_id=r['problem_id'],tag_id=t,reason=r['reason']))
report=dict(assigned=[750,1499],reviewed=750,adopted=a,removed_from_v3_2=removed)
(R/'full_review/shard_1_probability_expectation_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for t in ('T026','T029'):
 print(t,len([x for x in a if x['tag_id']==t]));print(', '.join(x['problem_id']+':'+x['role'] for x in a if x['tag_id']==t))
print('REMOVED',json.dumps(removed,ensure_ascii=False))
