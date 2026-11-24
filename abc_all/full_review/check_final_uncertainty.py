import json,csv
from pathlib import Path
w=Path('abc_all/full_review');by={}
for f in [*(w/f'shard_{i}.tsv' for i in range(4)),*(w/f'root_resolution_{i}.tsv' for i in ('root','0','2'))]:
 for r in csv.DictReader(f.open(encoding='utf-8-sig'),delimiter='\t'):by[r['problem_id']]=r
pending=[(p,r.get('uncertainty')) for p,r in by.items() if r.get('review_status')!='reviewed'];print('pending',pending)
print('active uncertainty',[(p,r['uncertainty']) for p,r in by.items() if r.get('review_status')=='reviewed' and r.get('uncertainty')][:35])
