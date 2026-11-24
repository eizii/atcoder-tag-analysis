import csv,json
from pathlib import Path
w=Path('abc_all/full_review');by={}
for f in [*(w/f'shard_{i}.tsv' for i in range(4)),*(w/f'root_resolution_{i}.tsv' for i in ('root','0','2'))]:
 for r in csv.DictReader(f.open(encoding='utf-8-sig'),delimiter='\t'):by[r['problem_id']]=r
old=[json.loads(l) for l in Path('abc_all/output_v3_2/problems_tagged.jsonl').open(encoding='utf-8')]
for t in ('T026','T029'):
 print(t,'REMOVED')
 for d in old:
  p=d['problem_id']
  if t in d['tag_ids'] and p in by and t+':' not in by[p]['accepted']:print(p,by[p]['reason'])
