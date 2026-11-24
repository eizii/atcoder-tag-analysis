"""Print bounded source excerpts for semantic review. No API calls."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('ids',nargs='*')
p.add_argument('--tag')
p.add_argument('--limit',type=int,default=4000)
p.add_argument('--offset',type=int,default=0)
p.add_argument('--count',type=int,default=20)
p.add_argument('--unresolved',action='store_true')
p.add_argument('--evidence',action='store_true')
p.add_argument('--brief',action='store_true')
a=p.parse_args()
ds=list(map(json.loads,(ROOT/'output_v2_uniform/problems_tagged.jsonl').open(encoding='utf-8')))
if a.ids: ds=[d for d in ds if d['problem_id'] in a.ids]
if a.tag: ds=[d for d in ds if a.tag in d['tag_ids']]
if a.unresolved: ds=[d for d in ds if not d['tag_ids']]
for d in ds[a.offset:a.offset+a.count]:
 print('\nTASK',d['problem_id'],d['title'],','.join(d['tag_ids']),d['url'])
 if a.evidence:
  for t,es in d['labels'].items():
   if a.tag and t!=a.tag: continue
   print(t,json.dumps(sorted({(e.get('url',''),e.get('context',e.get('note',''))) for e in es}),ensure_ascii=False))
 else:
  print('STATEMENT',d['statement'].split('入力例')[0][:250 if a.brief and d['editorials'] else 900 if a.brief else 1600])
  for i,e in enumerate(d['editorials']):
   print('SOURCE',i,e.get('source'),e.get('url'),'CHARS',len(e['text']))
   print(e['text'][:a.limit])
   if e.get('codes') and not a.brief: print('CODE','\n'.join(e['codes'])[:min(1600,a.limit)])
