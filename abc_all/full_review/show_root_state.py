import json,csv
from pathlib import Path
p=Path('abc_all'); t=json.loads((p/'taxonomy.json').read_text(encoding='utf-8'))
print('\n'.join(x['tag_id']+' '+x['tag'] for x in t))
q=list(csv.DictReader((p/'full_review/resolution_queue_root.tsv').open(encoding='utf-8-sig'),delimiter='\t')); done={r['problem_id'] for r in csv.DictReader((p/'full_review/root_resolution_root.tsv').open(encoding='utf-8-sig'),delimiter='\t')}
print('REMAIN', [(r['manifest_index'],r['problem_id']) for r in q if r['problem_id'] not in done])
