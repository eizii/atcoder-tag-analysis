import json,csv
from pathlib import Path
p=Path('abc_all/hierarchical_v4_20261124');s=json.loads((p/'summary.json').read_text(encoding='utf-8'))
for ds,d in s['datasets'].items():
 print(ds,d['problems'],d['active_tags'],'isolated',d['isolated_active_tags'])
 for k,m in d['models'].items():print(k,'coph',round(m['cophenetic_correlation'],3),[(c,m['cut_'+c]['clusters'],m['cut_'+c]['largest_cluster_tags'],m['cut_'+c]['silhouette']) for c in ('0_7','0_8','0_9')])
print('MATCHED')
for r in csv.DictReader((p/'matched_cluster_counts.csv').open(encoding='utf-8-sig')):print(r['dataset'],r['metric'],r['linkage'],r['target_clusters'],r['actual_clusters'],r['cut'],r['largest_cluster_tags'])
