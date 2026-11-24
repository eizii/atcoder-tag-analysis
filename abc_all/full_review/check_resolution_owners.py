import csv,json,collections
from pathlib import Path
w=Path('abc_all/full_review');p=json.loads((w/'root_resolution_plan.json').read_text(encoding='utf-8'))
r=list(csv.DictReader((w/'root_resolution_0.tsv').open(encoding='utf-8-sig'),delimiter='\t'))
print({k:(type(v).__name__,len(v),v[:2]) for k,v in p.items()})
print('duplicates',[(k,n) for k,n in collections.Counter(x['problem_id'] for x in r).items() if n>1]);print('outside', [x['problem_id'] for x in r if x['problem_id'] not in p['agent_0']])
