"""Read the remaining probability/expectation candidates in bounded batches."""
import argparse,csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('ids',nargs='*');p.add_argument('--limit',type=int,default=1800);p.add_argument('--statements',action='store_true');p.add_argument('--offset',type=int,default=0);p.add_argument('--source',type=int);a=p.parse_args()
with (R/'corpus_sources.jsonl').open(encoding='utf-8') as f:docs={d['problem_id']:d for d in map(json.loads,f)}
with (R/'output_v3_1/problems.csv').open(encoding='utf-8-sig') as f:rows={r['problem_id']:r for r in csv.DictReader(f)}
def compact(t):return re.sub(r'\s+',' ',t).strip()
for pid in a.ids:
 d=docs[pid];print('\nTASK',pid,d['title'],'CURRENT',rows[pid]['tag_ids'])
 if a.statements or not d['editorials']:print('STATEMENT',compact(d['statement'].split('入力例')[0])[:1600])
 for i,e in enumerate(d['editorials']):
  if a.source is not None and i!=a.source:continue
  t=compact(e['text']);print('SOURCE',i,e.get('url'),'LENGTH',len(t));print(t[a.offset:a.offset+a.limit])
