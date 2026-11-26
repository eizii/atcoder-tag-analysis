# -*- coding: utf-8 -*-
"""Inspect generated pilot inputs without exposing any V4 reference labels."""
import json,argparse
from pathlib import Path
p=Path(__file__).resolve().parent/'output';a=argparse.ArgumentParser();a.add_argument('--start',type=int,default=0);a.add_argument('--end',type=int,default=5);a.add_argument('--chars',type=int,default=2800);a.add_argument('--early',action='store_true');args=a.parse_args();selection=json.loads((p/'pilot_selection.json').read_text(encoding='utf-8'))['problem_ids'];requests={r['custom_id']:r for r in map(json.loads,(p/('early_pilot_requests_scoped.jsonl' if args.early else 'pilot_requests_scoped.jsonl')).open(encoding='utf-8'))}
for pid in selection[args.start:args.end]:
 r=json.loads(requests[pid]['messages'][1]['content']);print('\n###',pid,r['title']);print('CANDIDATES',', '.join(c['tag_id']+' '+c['tag'] for c in r['candidates']))
 for source in r['source_texts']:
  if source['source_id']=='statement':print('STATEMENT',source['text'][:700]);continue
  print('SOURCE',source['source_id'],len(source['text']),source['url']);print(source['text'][:args.chars])
