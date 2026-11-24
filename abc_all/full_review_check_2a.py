import ast,json,re
from pathlib import Path
D={d['problem_id']:d for d in map(json.loads,Path('abc_all/corpus_sources.jsonl').open(encoding='utf-8'))}
s=Path('abc_all/full_review_append_2d.py').read_text(encoding='utf-8-sig');block=ast.literal_eval(ast.parse(s).body[1].value.args[0])
for line in block.strip().splitlines():
 pid,_,anchor,*_=line.split('|');d=D[pid];texts=[e['text'] for e in d['editorials']]+[d['statement']]
 if not any(anchor in re.sub(r'\s+',' ',t) for t in texts):print(pid,repr(anchor))



