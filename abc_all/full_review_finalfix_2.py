import csv
from pathlib import Path
p=Path('abc_all/full_review/shard_2.tsv');rows=list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter='\t'));fields=list(rows[0])
for r in rows:
 if r['problem_id']=='abc324_f':
  r['accepted'] += ',T258:alternative'
  r['reason']='比率Xを固定しDAG上で重みb−Xcの最大経路をDPして可否判定、二分探索でO((N+M)log精度)。別出典1はStern–Brocot木で分母上限2e9の有理数探索、別出典2は最大化経路PからX←B(P)/C(P)を更新するDinkelbach法（区分線形関数のNewton更新）を示す。'
 if r['problem_id']=='abc330_f':
  r['reason']='正方形辺長Lを二分探索する。各軸の移動費Σ(l−x)_++Σ(x−l−L)_+は凸で、最適左端lは2N個の折点{x_i,x_i−L}のN番目に取れる。ソート後2列マージで折点を見つけprefix和から費用を評価してO(Nlog N+Nlog座標幅)。問題文から導出した実行可能解。'
 if r['problem_id']=='abc356_e':r['accepted']=r['accepted'].replace(',T154:analysis_concept','')
 if r['problem_id']=='abc365_b':r['accepted']=r['accepted'].replace(',T065:alternative','')
 if r['problem_id']=='abc370_g':r['accepted']=r['accepted'].replace(',T001:alternative','');r['reason']=r['reason'].replace('、Fenwick高速版も説明あり','。Fenwick高速化は詳細省略につき未採用')
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fields,delimiter='\t');w.writeheader();w.writerows(rows)
p=Path('abc_all/full_review_validate_2.py');s=p.read_text(encoding='utf-8-sig').replace("'next_problem_id':M[1500+len(rows)]['problem_id']", "'next_problem_id':M[1500+len(rows)]['problem_id'] if len(rows)<750 else None").replace("'status':'partial_checkpoint_not_complete'", "'status':'assigned_shard_complete' if len(rows)==750 else 'partial_checkpoint_not_complete'");p.write_bytes(b'\xef\xbb\xbf'+s.encode('utf8'))
