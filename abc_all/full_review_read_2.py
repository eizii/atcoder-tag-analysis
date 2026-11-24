import argparse,json,csv,re
from pathlib import Path
R=Path('abc_all');p=argparse.ArgumentParser();p.add_argument('start',type=int);p.add_argument('end',type=int);p.add_argument('--limit',type=int,default=700);a=p.parse_args()
D={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))};M=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems'];B={r['problem_id']:r for r in csv.DictReader((R/'output_v3_2/problems.csv').open(encoding='utf-8-sig'))}
for i in range(a.start,a.end):
 p=M[i];d=D[p['problem_id']];txt=re.sub(r'\s+',' ',d['editorials'][0]['text']) if d['editorials'] else re.sub(r'\s+',' ',d['statement'])
 print('\n',i,p['problem_id'],p['title'],'[',B[p['problem_id']]['tag_ids'],']',len(txt))
 if len(txt)>a.limit:print(txt[:a.limit//2]+' ... '+txt[-a.limit//2:])
 else:print(txt)
