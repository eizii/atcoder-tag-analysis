from pathlib import Path
import csv,json
p=Path('abc_all/full_review/root_resolution_2.tsv');rows=list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter='\t'));fields=list(rows[0])
for r in rows:
 if r['problem_id']=='abc464_g':r['accepted']=r['accepted'].replace(',T013:supporting','');r['out_of_vocabulary'] += ',双方向連結リスト'
 if r['problem_id']=='abc473_e':r['accepted']=r['accepted'].replace(',T249:supporting','')
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fields,delimiter='\t');w.writeheader();w.writerows(rows)
p=Path('abc_all/full_review/shard_2_checkpoint.json');d=json.loads(p.read_text(encoding='utf8'));d['notes']=[x for x in d['notes'] if not x.startswith('No decisions')];p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
