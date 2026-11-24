"""Bounded source reader for individual full-dataset review. Does not assign labels."""
import argparse,csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int);p.add_argument('--ids',nargs='*');p.add_argument('--limit',type=int,default=1400);p.add_argument('--statement-limit',type=int,default=650);p.add_argument('--offset',type=int,default=0);p.add_argument('--source',type=int);p.add_argument('--codes',action='store_true');a=p.parse_args()
manifest=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems'];docs={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))};prior={r['problem_id']:r for r in csv.DictReader((R/'output_v3_2/problems.csv').open(encoding='utf-8-sig'))};reviews=json.loads((R/'output_v3_2/semantic_reviews.json').read_text(encoding='utf-8'))
sup={}
for row in map(json.loads,(R/'precision_sources.jsonl').open(encoding='utf-8')):sup.setdefault(row['problem_id'],[]).append(row['editorial'])
def compact(s):return re.sub(r'\s+',' ',s).strip()
selected=[(i,x) for i,x in enumerate(manifest) if (x['problem_id'] in a.ids if a.ids else a.start<=i<(a.end if a.end is not None else a.start+10))]
for i,x in selected:
 pid=x['problem_id'];d=docs[pid];print('\n###',i,pid,d['title'],'TAGS',prior[pid]['tag_ids'])
 print('ST',compact(d['statement'].split('入力例')[0])[:a.statement_limit])
 for j,e in enumerate(d['editorials']):
  if a.source is not None and j!=a.source:continue
  t=compact(e['text']);print('ED',j,'chars',len(t),e.get('url'));print(t[a.offset:a.offset+a.limit])
  if a.codes:print('CODE',compact('\n'.join(e.get('codes',[])))[:1400])
 for e in sup.get(pid,[]):
  raw=next((v for v in d['editorials'] if v.get('url')==e['url']),None)
  if raw is None or len(e['text'])>len(raw['text'])+120:print('SUPPLEMENT',e['url'],compact(e['text'])[:a.limit])
 for r in reviews.get(pid,[]):print('PRIOR',r['scope'],r['accepted'],r['reason'])
