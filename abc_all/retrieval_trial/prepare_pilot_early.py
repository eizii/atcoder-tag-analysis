# -*- coding: utf-8 -*-
"""Prepare the fixed demonstration while the full embedding run is in progress."""
import sys,json,hashlib,time
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE));from encoder import Encoder
from generate import SYSTEM,load_unlabelled
OUT=BASE/'output';manifest,docs,profiles,supplements=load_unlabelled();encoder=Encoder(threads=2)
selections=[('abc007','C'),('abc168','D'),('abc284','E'),('abc184','D'),('abc319','C'),('abc411','E'),('abc220','F'),('abc340','G'),('abc222','H'),('abc055','C'),('abc092','B'),('abc100','D'),('abc263','E'),('abc375','G'),('abc395','F'),('abc396','G'),('abc404','D'),('abc405','G'),('abc417','D'),('abc412','G')];lookup={(p['contest_id'],p['problem_index']):p for p in manifest['problems']};pilot=[lookup[k]['problem_id'] for k in selections]
chunks=[c for c in map(json.loads,(OUT/'chunks.jsonl').open(encoding='utf-8')) if c['problem_id'] in pilot];rules=json.loads((OUT/'rule_candidates.json').read_text(encoding='utf-8'));texts=[p['tag']+'。'+p['definition']+'。別名: '+', '.join(p['aliases']) for p in profiles];tv=encoder.encode(texts,prefix='passage: ');cv=encoder.encode([c['text'] for c in chunks],prefix='query: ');scores=cv@tv.T;tagids=[p['tag_id'] for p in profiles];records=[]
for key in selections:
 p=lookup[key];pid=p['problem_id'];ix=[i for i,c in enumerate(chunks) if c['problem_id']==pid];best=scores[ix].argmax(axis=0);vals=scores[ix].max(axis=0);rank=np.argsort(-vals,kind='stable');candidates=set(rules[pid])|{tagids[j] for j in rank[:20]};d=docs[pid];replacement={e['url']:e for e in supplements.get(pid,[])};es=[replacement.pop(e.get('url'),e) for e in d['editorials']];es.extend(replacement.values());sources=[dict(source_id='statement',url=p['url'],text=d['statement'],codes=[])]+[dict(source_id=f'editorial_{j}',url=e.get('url') or p['url'],text=e['text'],codes=e.get('codes',[])) for j,e in enumerate(es)]
 payload=dict(problem_id=pid,title=p['title'],candidate_policy='top20 definitions plus rule union; early pilot copy',candidates=[dict(profiles[tagids.index(t)],rule_evidence=rules[pid].get(t,[]),retrieval_evidence=chunks[ix[best[tagids.index(t)]]]) for t in sorted(candidates)],source_texts=sources);records.append(dict(custom_id=pid,messages=[dict(role='system',content=SYSTEM),dict(role='user',content=json.dumps(payload,ensure_ascii=False))]))
with (OUT/'early_pilot_requests.jsonl').open('w',encoding='utf-8') as f:
 for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
(OUT/'pilot_selection.json').write_text(json.dumps(dict(problem_ids=pilot,selection='fixed illustrative cases; not representative evaluation'),indent=2)+'\n',encoding='utf-8')
print('early pilot ready',len(records),'chunks',len(chunks))
