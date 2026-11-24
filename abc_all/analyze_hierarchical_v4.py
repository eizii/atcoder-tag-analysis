# -*- coding: utf-8 -*-
"""Additional diagnostics for interpreting each existing V4 hierarchy."""
import csv,json
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.cluster.hierarchy import fcluster
from sklearn.metrics import adjusted_rand_score
R=Path(__file__).resolve().parent;O=R/'hierarchical_v4_20261124'
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
matched=read(O/'matched_cluster_counts.csv');summary=json.loads((O/'summary.json').read_text(encoding='utf-8'));details=[];groupdata={};scope_labels={};pairissues=[]
for ds in summary['datasets']:
 folder=O/ds;tags=read(folder/'included_tags.csv');ids=[r['tag_id'] for r in tags];names={r['tag_id']:r['tag'] for r in tags};rows=read(folder/'problem_tag_matrix.csv');x=np.array([[int(r[t]) for t in ids] for r in rows],dtype=np.int64);co=x.T@x
 for metric in summary['distance_metrics']:
  d=np.load(folder/f'{metric}_distance.npy')
  for method in summary['linkages']:
   model=metric+'_'+method;z=np.loadtxt(folder/model/'linkage.csv',delimiter=',',skiprows=1)
   for setting in ('cut_0.7','cut_0.8','cut_0.9','target_80'):
    cut=float(setting[4:]) if setting.startswith('cut_') else float(next(r['cut'] for r in matched if r['dataset']==ds and r['metric']==metric and r['linkage']==method and r['target_clusters']=='80'))
    lab=fcluster(z,cut,criterion='distance');scope_labels[ds,model,setting]=(ids,lab);sizes=Counter(lab);within=[];nooverlap=0;grouprecords=[]
    for label in sizes:
     ix=np.flatnonzero(lab==label);pairs=[(i,j) for a,i in enumerate(ix) for j in ix[a+1:]]
     distances=[float(d[i,j]) for i,j in pairs];zero=[(i,j) for i,j in pairs if co[i,j]==0];nooverlap+=len(zero);within+=distances
     grouprecords.append(dict(tag_count=len(ix),tag_ids=[ids[i] for i in ix],tags=[names[ids[i]] for i in ix],problem_count=int(x[:,ix].any(axis=1).sum()),pair_count=len(pairs),no_overlap_pairs=len(zero),mean_pair_distance=float(np.mean(distances)) if distances else None,max_pair_distance=max(distances) if distances else None))
    grouprecords.sort(key=lambda g:(-g['tag_count'],g['tag_ids']))
    r=dict(dataset=ds,model=model,setting=setting,cut=cut,clusters=len(sizes),singleton_clusters=sum(v==1 for v in sizes.values()),largest_cluster_tags=max(sizes.values()),within_pair_count=len(within),within_zero_overlap_pairs=nooverlap,within_zero_overlap_fraction=nooverlap/len(within) if within else 0,mean_within_pair_distance=float(np.mean(within)) if within else None,max_within_pair_distance=max(within) if within else None)
    details.append(r);groupdata[ds+'/'+model+'/'+setting]=grouprecords
    if setting=='cut_0.8' and ds=='all_difficulties':
     for g in grouprecords:
      if g['tag_count']<=1 or g['tag_count']>12:continue
      for ia,a in enumerate(g['tag_ids']):
       for b in g['tag_ids'][ia+1:]:
        i,j=ids.index(a),ids.index(b);pairissues.append(dict(model=model,tag_a=a,name_a=names[a],support_a=int(co[i,i]),tag_b=b,name_b=names[b],support_b=int(co[j,j]),shared=int(co[i,j]),distance=float(d[i,j])))
 comparisons=[]
 for metric in summary['distance_metrics']:
  for method in summary['linkages']:
   model=metric+'_'+method
   for a,b in ((.7,.8),(.8,.9)):
    labels1=scope_labels[ds,model,f'cut_{a:.1f}'][1];labels2=scope_labels[ds,model,f'cut_{b:.1f}'][1]
    comparisons.append(dict(dataset=ds,model=model,cut_a=a,cut_b=b,ari=float(adjusted_rand_score(labels1,labels2))))
 write(folder/'cut_partition_changes.csv',comparisons)
scope=[]
for metric in summary['distance_metrics']:
 for method in summary['linkages']:
  model=metric+'_'+method
  for setting in ('cut_0.7','cut_0.8','cut_0.9','target_80'):
   ai,al=scope_labels['all_difficulties',model,setting];bi,bl=scope_labels['under_2000',model,setting];common=sorted(set(ai)&set(bi));a=[al[ai.index(t)] for t in common];b=[bl[bi.index(t)] for t in common]
   scope.append(dict(model=model,setting=setting,common_tags=len(common),full_scope_groups_on_common_tags=len(set(a)),under_2000_groups=len(set(b)),ari=float(adjusted_rand_score(a,b))))
write(O/'analysis_diagnostics.csv',details);write(O/'scope_partition_agreement.csv',scope);write(O/'cut_0.8_group_pairs.csv',pairissues)
(O/'analysis_groups.json').write_text(json.dumps(groupdata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('ALL DIAGNOSTICS AT CUT .8 OR TARGET80')
for r in details:
 if r['dataset']=='all_difficulties' and r['setting'] in ('cut_0.8','target_80'):print(r)
print('SCOPE COMPARISON')
for r in scope:
 if r['setting']=='target_80':print(r)
print('LARGEST GROUPS AT TARGET80')
for key,groups in groupdata.items():
 if key.startswith('all_difficulties/') and key.endswith('/target_80'):
  print(key)
  for g in groups[:5]:print(g['tag_count'],g['no_overlap_pairs'],','.join(g['tags'])[:550])
