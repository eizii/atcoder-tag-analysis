"""Inspect probability/expectation candidates without using existing tags as a filter."""
import csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parent
PATTERN=re.compile(r'確率|期待値|一様|ランダム|サイコロ|ダイス|コイントス|probability|expected',re.I)

def load():
 with (R/'corpus_sources.jsonl').open(encoding='utf-8') as f:docs={d['problem_id']:d for d in map(json.loads,f)}
 with (R/'output_v3/problems.csv').open(encoding='utf-8-sig') as f:rows={r['problem_id']:r for r in csv.DictReader(f)}
 return docs,rows

def compact(text):return re.sub(r'\s+',' ',text).strip()

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('ids',nargs='*');p.add_argument('--list',action='store_true');p.add_argument('--limit',type=int,default=1800);a=p.parse_args()
 docs,rows=load()
 candidates=[d for d in docs.values() if PATTERN.search(d['statement'].split('入力例')[0]) or {'T026','T029'}&set(rows[d['problem_id']]['tag_ids'].split(' | '))]
 if a.list:
  for d in candidates:
   pid=d['problem_id'];print(pid,d['title'],rows[pid]['tag_ids'])
  print('TOTAL',len(candidates));return
 for pid in a.ids:
  d=docs[pid]
  print('\nTASK',pid,d['title'],'V3',rows[pid]['tag_ids'])
  print('STATEMENT',compact(d['statement'].split('入力例')[0])[:1200])
  for i,e in enumerate(d['editorials']):print('SOURCE',i,e.get('url'),compact(e['text'])[:a.limit])

if __name__=='__main__':main()
