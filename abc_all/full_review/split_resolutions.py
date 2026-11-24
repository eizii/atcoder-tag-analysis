import csv,json
from pathlib import Path
r=Path('abc_all');w=r/'full_review';m=json.loads((r/'manifest.json').read_text(encoding='utf-8'))['problems'];ix={p['problem_id']:i for i,p in enumerate(m)}
rows=[dict(x,manifest_index=ix[x['problem_id']]) for x in csv.DictReader((w/'shard_3.tsv').open(encoding='utf-8-sig'),delimiter='\t') if x['review_status']=='needs_resolution'];assert len(rows)==256
plan={'root':[x['problem_id'] for x in rows[:86]],'agent_0':[x['problem_id'] for x in rows[86:171]],'agent_2':[x['problem_id'] for x in rows[171:]]}
(w/'root_resolution_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for who,ids in plan.items():
 with (w/('resolution_queue_'+who+'.tsv')).open('w',encoding='utf-8-sig',newline='') as f:
  rr=[x for x in rows if x['problem_id'] in ids];c=csv.DictWriter(f,fieldnames=list(rr[0]),delimiter='\t');c.writeheader();c.writerows(rr)
print({k:(len(v),v[0],v[-1]) for k,v in plan.items()})
