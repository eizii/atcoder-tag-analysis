import csv,json
from pathlib import Path
import numpy as np
O=Path('abc_all/hierarchical_v4_20261124')
for ds in ('all_difficulties','under_2000'):
 t=list(csv.DictReader((O/ds/'included_tags.csv').open(encoding='utf-8-sig')));ids=[r['tag_id'] for r in t];pair=list(csv.DictReader((O/ds/'pair_distances.csv').open(encoding='utf-8-sig')))
 print(ds,'identical',[(r['tag_a'],r['tag_b'],r['support_a']) for r in pair if float(r['jaccard_distance'])==0])
 for a,b in [('T026','T029'),('T036','T223'),('T037','T223'),('T053','T234'),('T053','T233')]:
  rs=[r for r in pair if {r['tag_a_id'],r['tag_b_id']}=={a,b}]
  if rs:print(rs[0])
# One zero-overlap pair in average cut=.8
for r in csv.DictReader((O/'cut_0.8_group_pairs.csv').open(encoding='utf-8-sig')):
 if r['model']=='cosine_average' and r['shared']=='0':print('average bridge pair',r)
