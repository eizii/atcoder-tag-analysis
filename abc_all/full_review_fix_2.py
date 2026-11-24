import csv
from pathlib import Path
R=Path('abc_all')
updates={
 'abc288_f':'先頭i桁までの全分割値の積和dp_i=sum_j dp_j*X[j+1:i]。i>=2でdp_i=10dp_(i-1)+digit_i*sum_(j=0..i-1)dp_jへ変形し、累積dpを保持してO(N)。dp_0=1、dp_1=先頭桁を初期化する。',
 'abc293_f':'b進表記の桁数d=2..floor(log2 N)+1を列挙する。d=2はb=N,N-1を直接検査。d>=3は0/1表記が入る区間[b^(d-1),sum_(i=0..d-1)b^i]が異なるbで交わらないため、b^(d-1)<=Nの最大bだけを二分探索して桁検査する。上限打切りの累乗評価でO(log^3 N)以下。'
}
p=R/'full_review/shard_2.tsv';rows=list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter='\t'));fields=list(rows[0])
for r in rows:
 if r['problem_id'] in updates:r['reason']=updates[r['problem_id']]
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(rows)
for name in ['full_review_append_2b.py','full_review_append_2c.py']:
 p=R/name;s=p.read_text(encoding='utf-8-sig');lines=[]
 for line in s.splitlines():
  pid=line.split('|')[0]
  if pid in updates:
   parts=line.split('|');line='|'.join(parts[:3]+[updates[pid]])
  lines.append(line)
 p.write_bytes(b'\xef\xbb\xbf'+('\n'.join(lines)+'\n').encode('utf-8'))
