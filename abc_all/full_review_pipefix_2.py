import csv
from pathlib import Path
p=Path('abc_all/full_review/shard_2.tsv');rows=list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter='\t'));fields=list(rows[0])
for r in rows:
 if r['problem_id']=='abc351_e':r.update(scope='full',review_status='reviewed',uncertainty='',out_of_vocabulary='',reason='X+Yの偶奇で分け、u=X+Y,v=X−Yへ45度変換する。同群内距離は(abs(du)+abs(dv))/2なので各軸をソートしprefix和で全ペア絶対差を足すO(N log N)。')
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fields,delimiter='\t');w.writeheader();w.writerows(rows)
