import csv,json
from pathlib import Path
r=Path('abc_all');rows=list(csv.DictReader((r/'full_review/resolution_queue_agent_2.tsv').open(encoding='utf-8-sig'),delimiter='\t'));d={x['problem_id']:x for x in map(json.loads,(r/'corpus_sources.jsonl').open(encoding='utf8'))}
for i,x in enumerate(rows):print(i,x['problem_id'],[(len(e['text']),e['url']) for e in d[x['problem_id']]['editorials']])
