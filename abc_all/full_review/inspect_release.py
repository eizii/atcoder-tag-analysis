import csv,json
from pathlib import Path
p=Path('abc_all/output_v4');r=list(csv.DictReader((p/'tag_catalog.csv').open(encoding='utf-8-sig')))
print([x for x in r if x['tag_id'] in ('T026','T029')])
print((p/'README.md').read_text(encoding='utf-8-sig')[:2200])
print('Artifacts',len(list(p.iterdir())))
