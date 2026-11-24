import csv,json
from pathlib import Path
O=Path('abc_all/hierarchical_v4_20261124')
for ds in ('all_difficulties','under_2000'):
 for model in ('cosine_average','cosine_single','cosine_complete','jaccard_average','jaccard_single','jaccard_complete'):
  data=json.loads((O/ds/model/'clusters_cut_0.8.json').read_text(encoding='utf-8'))['clusters'];multi=[g for g in data if g['tag_count']>1]
  print(ds,model,'groups',len(data),'multi',len(multi))
  targets={'T026','T029','T036','T037','T053','T233','T234','T145','T175','T039','T255','T132','T196','T223'}
  for g in multi:
   if set(g['tag_ids'])&targets:print(g['tag_count'], ' / '.join(g['tags'])[:1000])
rows=list(csv.DictReader(Path('abc_all/output_v4/problem_tag_matrix.csv').open(encoding='utf-8-sig')))
for a,b in [('T036','T223'),('T124','T265'),('T145','T175'),('T039','T255')]:
 aa={r['problem_id'] for r in rows if r[a]=='1'};bb={r['problem_id'] for r in rows if r[b]=='1'};print('pair',a,b,len(aa),len(bb),'shared',sorted(aa&bb))
