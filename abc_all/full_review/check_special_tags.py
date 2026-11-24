import csv,json,collections
from pathlib import Path
w=Path('abc_all/full_review');rows=[]
for i in range(4):rows+=list(csv.DictReader((w/f'shard_{i}.tsv').open(encoding='utf-8-sig'),delimiter='\t'))
by={r['problem_id']:r for r in rows}
for f in w.glob('root_resolution_*.tsv'):
 for r in csv.DictReader(f.open(encoding='utf-8-sig'),delimiter='\t'):by[r['problem_id']]=r
print('shortquotes',[(p,len(r['evidence_quote']),r['evidence_quote'],r['reason'][:90]) for p,r in by.items() if len(r['evidence_quote'])<12])
for tid in ('T029','T026'):
 print(tid,[(p,r['accepted'],r['reason']) for p,r in by.items() if tid+':' in r['accepted']])
