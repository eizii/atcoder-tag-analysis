"""Check interpretation diagnostics against saved partitions and pair tables."""
import csv,json,math,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parent;O=R/'hierarchical_v4_20261124'
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def ari(a,b):
 n=len(a);pairs=n*(n-1)/2
 ca=Counter(a);cb=Counter(b);cross=Counter(zip(a,b));choose=lambda n:n*(n-1)/2
 aa=sum(map(choose,ca.values()));bb=sum(map(choose,cb.values()));xx=sum(map(choose,cross.values()));expected=aa*bb/pairs;denom=(aa+bb)/2-expected
 return (xx-expected)/denom if denom else 1.
checked=0;scope=0;labels={}
for ds in ('all_difficulties','under_2000'):
 pair={frozenset((r['tag_a_id'],r['tag_b_id'])):int(r['shared_problems']) for r in read(O/ds/'pair_distances.csv')}
 for model in ('cosine_average','cosine_single','cosine_complete','jaccard_average','jaccard_single','jaccard_complete'):
  for setting in ('cut_0.7','cut_0.8','cut_0.9','target_80'):
   groups=json.loads((O/ds/model/f'clusters_{setting}.json').read_text(encoding='utf-8'))['clusters'];lab={t:g['cluster_id'] for g in groups for t in g['tag_ids']};labels[ds,model,setting]=lab
   sizes=[g['tag_count'] for g in groups];total=sum(n*(n-1)//2 for n in sizes);zero=sum(pair[frozenset((a,b))]==0 for g in groups for i,a in enumerate(g['tag_ids']) for b in g['tag_ids'][i+1:]);r=next(r for r in read(O/'analysis_diagnostics.csv') if r['dataset']==ds and r['model']==model and r['setting']==setting)
   assert int(r['clusters'])==len(groups) and int(r['largest_cluster_tags'])==max(sizes) and int(r['singleton_clusters'])==sum(n==1 for n in sizes)
   assert int(r['within_pair_count'])==total and int(r['within_zero_overlap_pairs'])==zero
   assert abs(float(r['within_zero_overlap_fraction'])-zero/total)<1e-12
   checked+=1
for r in read(O/'scope_partition_agreement.csv'):
 a=labels['all_difficulties',r['model'],r['setting']];b=labels['under_2000',r['model'],r['setting']];common=sorted(a.keys()&b.keys());assert len(common)==int(r['common_tags'])
 assert abs(ari([a[t] for t in common],[b[t] for t in common])-float(r['ari']))<1e-12;scope+=1
text=(O/'ANALYSIS.md').read_text(encoding='utf-8-sig');links=0
for target in re.findall(r'\]\(([^)]+)\)',text):
 if target.startswith(('https:','http:','#')):continue
 assert (O/target).exists(),target;links+=1
result=dict(checks_passed=True,partitions_reconciled=checked,scope_ARI_independently_recomputed=scope,analysis_links_checked=links,diagnostics_are_not_gold_accuracy=True)
(O/'analysis_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
