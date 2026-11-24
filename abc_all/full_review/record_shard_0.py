import csv,json,re,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parents[1];OUT=R/'full_review/shard_0.tsv'
DOC={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))}
OLD={r['problem_id']:r for r in csv.DictReader((R/'output_v3_2/problems.csv').open(encoding='utf-8-sig'))}
rows={r['problem_id']:r for r in csv.DictReader(OUT.open(encoding='utf-8-sig'),delimiter='\t')} if OUT.exists() else {}
def put(pid,tags,reason,gaps='',anchor='',source=None,status='reviewed',uncertainty=''):
 d=DOC[pid];src='statement' if source=='statement' or not d['editorials'] else '0' if source is None else str(source)
 t=d['statement'] if src=='statement' else d['editorials'][int(src)]['text'];t=re.sub(r'\s+',' ',unicodedata.normalize('NFKC',t))
 if anchor:
  anchor=unicodedata.normalize('NFKC',anchor);loc=t.find(anchor)
  if loc<0:
   positions=[i for i,c in enumerate(t) if not c.isspace()];flat=''.join(t[i] for i in positions);hit=flat.find(''.join(anchor.split()));loc=positions[hit] if hit>=0 else -1
  if loc<0:raise ValueError((pid,anchor))
 else:loc=0
 quote=t[max(0,loc-20):loc+max(len(anchor),60)+80]
 old=set(OLD[pid]['tag_ids'].split(' | '))-{''};accepted={x.split(':')[0] for x in tags.split(',') if x}
 rows[pid]=dict(problem_id=pid,scope='full' if status=='reviewed' else 'selected_tags',accepted=tags,rejected=','.join(sorted(old-accepted)),out_of_vocabulary=gaps,source_indices=src,evidence_quote=quote,reason=reason,review_status=status,uncertainty=uncertainty)
def save():
 with OUT.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['problem_id','scope','accepted','rejected','out_of_vocabulary','source_indices','evidence_quote','reason','review_status','uncertainty'],delimiter='\t');w.writeheader();w.writerows(rows.values())
 print('saved',len(rows))

