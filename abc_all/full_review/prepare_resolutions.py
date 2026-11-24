import csv,json
from pathlib import Path
r=Path('abc_all');w=r/'full_review';m=json.loads((r/'manifest.json').read_text(encoding='utf-8'))['problems'];ix={p['problem_id']:i for i,p in enumerate(m)}
p=w/'root_decisions.txt';s=p.read_text(encoding='utf-8-sig');lines=s.splitlines();out=[]
for line in lines:
 if line.startswith('2638|') and not line.endswith('|needs_resolution'):line+='||needs_resolution'
 out.append(line)
p.write_text('\n'.join(out)+'\n',encoding='utf-8-sig')
# The plan is derived after regenerating shard_3 in the next command.
