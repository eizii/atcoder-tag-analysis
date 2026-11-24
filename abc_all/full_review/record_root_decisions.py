"""Manually authored decisions for the final manifest quarter."""
import csv,json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent
M=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems'];D={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))}
DATA=Path(__file__).with_name(sys.argv[1] if len(sys.argv)>1 else 'root_decisions.txt')
rows=[]
for line in DATA.read_text(encoding='utf-8-sig').splitlines():
 if not line or line.startswith('#'):continue
 parts=(line.split('|')+['']*7)[:7];idx,tags,reason,gap,status,quote,source=parts;pid=M[int(idx)]['problem_id'];d=D[pid]
 accepted=[]
 for t in tags.split(','):
  if not t:continue
  role={'~':'supporting','?':'alternative','^':'analysis_concept',':':'concept'}.get(t[-1],'primary');tid=t[:-1] if t[-1] in '~?^:' else t
  accepted.append(tid+':'+role)
 if not source:source='0' if d['editorials'] else 'statement'
 text=d['statement'] if source=='statement' else '\n'.join(d['editorials'][int(j)]['text'] for j in source.split(','))
 if not quote:
  chunks=re.split(r'(?<=。)\s*|\n+',text)
  meaningful=[s for s in chunks if len(s.strip())>=12 and not re.search(r'初心者|practice|学習|はじめたばかり|APG4b|AtCoder Beginners|実装例|解答例',s)]
  quote=(meaningful[0] if meaningful else text)[:110].strip()
 if quote not in text:raise ValueError((pid,quote))
 rows.append(dict(problem_id=pid,scope='selected_tags' if status else 'full',accepted=','.join(accepted),rejected='',out_of_vocabulary=gap,source_indices=source,evidence_quote=quote,reason=reason,review_status=status or 'reviewed',uncertainty='解説後半・別解の追加点検が必要' if status else ''))
with Path(__file__).with_name(sys.argv[2] if len(sys.argv)>2 else 'shard_3.tsv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
print('root ledger',len(rows),'reviewed',sum(r['review_status']=='reviewed' for r in rows))
