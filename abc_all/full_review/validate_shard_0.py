from record_shard_0 import *
p=R/'full_review/batch_0_7.py'
t=p.read_text(encoding='utf-8-sig').replace('ceil(N/10^d)*10^d-1','(floor(N/10^d)+1)*10^d-1')
p.write_text(t,encoding='utf-8-sig')
rows['arc099_b']['reason']=rows['arc099_b']['reason'].replace('ceil(N/10^d)*10^d-1','(floor(N/10^d)+1)*10^d-1')
save()
import sys
sys.path.insert(0,str(R))
from tag_precision import read_reviews
r=read_reviews(DOC,OUT)
m=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems']
print(type(m[0]),m[0])
expected=[x['problem_id'] for x in m[:750]]
assert set(expected)==set(rows),(len(set(expected)-set(rows)),len(set(rows)-set(expected)))
tax={x['tag_id'] for x in json.loads((R/'taxonomy.json').read_text(encoding='utf-8'))}
for pid,row in rows.items():
 for a in row['accepted'].split(','):
  if a: assert a.split(':')[0] in tax,(pid,a)
 assert row['scope']=='full' and row['review_status']=='reviewed'
print('VALIDATED',len(rows),'problems; exact evidence quotes and tags pass')
