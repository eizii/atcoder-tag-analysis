import csv,re
from pathlib import Path
p=Path('abc_all/full_review/shard_3.tsv')
for r in csv.DictReader(p.open(encoding='utf-8-sig'),delimiter='\t'):
 if r['review_status']=='reviewed' and re.search(r'(?:追加|全文|後半|統合時|再照合|照合が必要).{0,20}(?:確認|精査)|(?:確認|精査).{0,8}(?:必要|する)',r['reason']):print(r['problem_id'],r['reason'])
