# -*- coding: utf-8 -*-
"""V4 binary tag clustering: two distances by three linkage rules."""
import csv,hashlib,json,sys
from pathlib import Path
from collections import Counter
import numpy as np,scipy,sklearn,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy.spatial.distance import pdist,squareform
from scipy.cluster.hierarchy import linkage,fcluster,dendrogram,cophenet,is_valid_linkage
from sklearn.metrics import silhouette_samples,adjusted_rand_score
R=Path(__file__).resolve().parent;SOURCE=R/'output_v4';OUT=R/'hierarchical_v4_20261124'
DATASETS={'all_difficulties':'全難易度','under_2000':'2000未満'}
METRICS={'cosine':'コサイン距離','jaccard':'ジャカード距離'}
METHODS={'average':'平均連結法','single':'単連結法','complete':'完全連結法'}
CUTS=[round(i/20,2) for i in range(21)];SHOW=(.7,.8,.9);TARGETS=(40,80)
EXAMPLES=[('T026','T029'),('T053','T233'),('T053','T234'),('T233','T234'),('T032','T033'),('T001','T003'),('T022','T027'),('T066','T067'),('T066','T144'),('T132','T196'),('T145','T175'),('T039','T255')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def write(p,rows,fields=None):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def metrics(d,lab):
 c=Counter(lab);n=len(c);v=silhouette_samples(d,lab,metric='precomputed') if 1<n<len(lab) else None
 sizes=sorted(c.values(),reverse=True)
 return dict(clusters=n,multi_tag_clusters=sum(x>1 for x in sizes),singleton_clusters=sum(x==1 for x in sizes),largest_cluster_tags=sizes[0],largest_cluster_fraction=sizes[0]/len(lab),silhouette=float(v.mean()) if v is not None else None)
def groups(lab,ids,names,x):
 result=[]
 for label in set(lab):
  ix=np.flatnonzero(lab==label);members=[ids[i] for i in ix]
  result.append(dict(cluster_id='C_'+min(members),tag_ids=members,tags=[names[t] for t in members],tag_count=len(members),problem_count=int(x[:,ix].any(axis=1).sum())))
 return sorted(result,key=lambda r:r['cluster_id'])
def export_partition(folder,suffix,lab,ids,names,x,support,info):
 gs=groups(lab,ids,names,x);dump(folder/f'clusters_{suffix}.json',dict(info,clusters=gs))
 members=[];table=['# クラスタ内訳','',info['description'],'','| クラスタ | タグ数 | 問題和集合 | タグ |','| --- | ---: | ---: | --- |']
 for g in gs:
  table.append('| '+g['cluster_id']+' | '+str(g['tag_count'])+' | '+str(g['problem_count'])+' | '+'、'.join(g['tags'])+' |')
  for t in g['tag_ids']:members.append(dict(cluster_id=g['cluster_id'],tag_id=t,tag=names[t],tag_problem_count=int(support[ids.index(t)]),cluster_problem_count=g['problem_count']))
 write(folder/f'members_{suffix}.csv',members);(folder/f'clusters_{suffix}.md').write_text('\n'.join(table)+'\n',encoding='utf-8-sig')
def draw(z,ids,names,support,title,metric,folder):
 fig,ax=plt.subplots(figsize=(18,max(14,len(ids)*.20)))
 dendrogram(z,labels=[t+' '+names[t]+' (n='+str(int(support[i]))+')' for i,t in enumerate(ids)],orientation='right',leaf_font_size=9,color_threshold=np.nextafter(.7,np.inf),above_threshold_color='#7b8794',ax=ax)
 for cut,color in [(.7,'#bb3045'),(.8,'#b57316'),(.9,'#466ca8')]:ax.axvline(cut,color=color,ls='--',lw=1,label=f'cut={cut:.1f}')
 ax.set_xlim(-.005,1.025);ax.set_xlabel(METRICS[metric]+' / 結合距離');ax.set_title(title,fontsize=15,pad=14);ax.legend(loc='lower right');ax.grid(axis='x',alpha=.2);ax.tick_params(axis='y',length=2,pad=4)
 fig.text(.025,.012,'V4：主解・別解・補助を同じ1で扱う二値行列。n=対象内の付与問題数。未使用タグのみ除外。\n枝色はcut=0.7での区切り（色は繰り返される）。破線0.7/0.8/0.9の各内訳を別途収録。',fontsize=9)
 fig.tight_layout(rect=(.01,.04,.995,.995))
 for ext in ('png','svg'):fig.savefig(folder/f'dendrogram.{ext}',dpi=130,facecolor='white')
 plt.close(fig)
def best_cut(z,target):
 options=np.r_[0,np.unique(z[:,2]),1.0];items=[(float(c),len(set(fcluster(z,float(c),criterion='distance')))) for c in options]
 return min(items,key=lambda a:(abs(a[1]-target),abs(a[0]-.7),a[0]))
def main():
 OUT.mkdir(exist_ok=True);fonts={f.name for f in font_manager.fontManager.ttflist};font=next((n for n in ('Meiryo','Yu Gothic','MS Gothic') if n in fonts),'DejaVu Sans')
 matplotlib.rcParams.update({'font.family':[font,'DejaVu Sans'],'axes.unicode_minus':False,'svg.fonttype':'none'})
 protected=[SOURCE/n for n in ('problem_tag_matrix.csv','problems.csv','all_problems_tagged.csv','summary.json')]+[R/'taxonomy.json'];before={str(p.relative_to(R)):sha(p) for p in protected}
 rows=read(SOURCE/'problem_tag_matrix.csv');tids=list(rows[0])[1:];pids=[r['problem_id'] for r in rows];xall=np.array([[int(r[t]) for t in tids] for r in rows],dtype=np.uint8);metadata={p['problem_id']:p for p in read(SOURCE/'problems.csv')};names={t['tag_id']:t['tag'] for t in json.loads((R/'taxonomy.json').read_text(encoding='utf-8'))}
 assert len(rows)==3012 and len(set(pids))==3012 and len(tids)==266 and np.isin(xall,[0,1]).all()
 summary=dict(created='2026-11-24',source_version='abc-all-266-semantic-v4',source_snapshot='2026-11-05',clustered_objects='tags',representation='tag x problem binary; primary/alternative/supporting equal weight; no concept or proof labels',distance_metrics=list(METRICS),linkages=list(METHODS),cuts=CUTS,display_cuts=SHOW,matched_cluster_targets=TARGETS,source_sha256=before,versions=dict(python=sys.version.split()[0],numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,matplotlib=matplotlib.__version__),tie_policy='taxonomy tag-ID order; SciPy deterministic ties for recorded versions; no forced splitting of equal-height merges',paid_api_calls=0,independent_human_validation=False,datasets={})
 sweeps=[];matched=[];examples=[];aris=[]
 for ds,title in DATASETS.items():
  folder=OUT/ds;folder.mkdir(exist_ok=True);ix=np.array([True if ds=='all_difficulties' else metadata[p]['difficulty']!='' and float(metadata[p]['difficulty'])<2000 for p in pids]);x=xall[ix];supports=x.sum(axis=0);active=np.flatnonzero(supports>0);ids=[tids[i] for i in active];x=x[:,active];support=supports[active];co=x.T.astype(np.int64)@x.astype(np.int64);isolated=(co.sum(axis=1)-support)==0
  write(folder/'problems.csv',[metadata[p] for p,take in zip(pids,ix) if take]);write(folder/'problem_tag_matrix.csv',[dict(problem_id=p,**{t:int(v) for t,v in zip(tids,row)}) for p,row,take in zip(pids,xall,ix) if take]);write(folder/'included_tags.csv',[dict(tag_id=t,tag=names[t],problem_count=int(support[i]),has_cooccurrence=bool(not isolated[i])) for i,t in enumerate(ids)])
  write(folder/'excluded_tags.csv',[dict(tag_id=tids[i],tag=names[tids[i]],problem_count=0,reason='unused_in_this_problem_scope') for i in range(len(tids)) if supports[i]==0],['tag_id','tag','problem_count','reason'])
  dsinfo=dict(problems=int(ix.sum()),tagged_problems=int(x.any(axis=1).sum()),zero_tag_problems=int((~x.any(axis=1)).sum()),active_tags=len(ids),unused_tags=int((supports==0).sum()),isolated_active_tags=[ids[i] for i in np.flatnonzero(isolated)],models={});models={};distances={}
  for metric in METRICS:
   cond=pdist(x.T.astype(bool) if metric=='jaccard' else x.T.astype(float),metric=metric);d=squareform(cond)
   direct=1-co/(support[:,None]+support[None,:]-co) if metric=='jaccard' else 1-co/np.sqrt(support[:,None]*support[None,:])
   np.fill_diagonal(direct,0);np.testing.assert_allclose(d,direct,atol=1e-12);d=np.clip(d,0,1);np.fill_diagonal(d,0);cond=squareform(d);distances[metric]=d
   np.save(folder/f'{metric}_distance.npy',d)
   for method in METHODS:
    key=metric+'_'+method;mf=folder/key;mf.mkdir(exist_ok=True);z=linkage(cond,method=method,optimal_ordering=True);assert is_valid_linkage(z,throw=True) and np.all(np.diff(z[:,2])>=-1e-12)
    np.savetxt(mf/'linkage.csv',z,delimiter=',',header='left,right,distance,leaf_count',comments='');models[key]=(d,z)
    local=[]
    for cut in CUTS:
     lab=fcluster(z,cut,criterion='distance');stat=metrics(d,lab);row=dict(dataset=ds,metric=metric,linkage=method,tags=len(ids),cut=cut,**stat);local.append(row);sweeps.append(row)
     if cut in SHOW:export_partition(mf,f'cut_{cut:.1f}',lab,ids,names,x,support,dict(metric=metric,linkage=method,cut=cut,description=f'{title} / {METRICS[metric]} / {METHODS[method]} / cut={cut:.1f}'))
    assert local[-1]['clusters']==1
    write(mf/'cut_sweep.csv',local)
    coph=float(cophenet(z,cond)[0]);dsinfo['models'][key]=dict(cophenetic_correlation=coph,cut_0_7=next(r for r in local if r['cut']==.7),cut_0_8=next(r for r in local if r['cut']==.8),cut_0_9=next(r for r in local if r['cut']==.9))
    for target in TARGETS:
     cut,k=best_cut(z,target);lab=fcluster(z,cut,criterion='distance');matched.append(dict(dataset=ds,metric=metric,linkage=method,target_clusters=target,actual_clusters=k,exact_match=k==target,cut=cut,**{k:v for k,v in metrics(d,lab).items() if k!='clusters'}));export_partition(mf,f'target_{target}',lab,ids,names,x,support,dict(metric=metric,linkage=method,target_clusters=target,actual_clusters=k,cut=cut,description=f'{title} / {METRICS[metric]} / {METHODS[method]} / 目標{target}群、実際{k}群、cut={cut:.6g}'))
    draw(z,ids,names,support,f'{title}：{METRICS[metric]} × {METHODS[method]} / {len(ids)}タグ',metric,mf);print(ds+' '+key+' complete',flush=True)
  pairs=[]
  for i in range(len(ids)):
   for j in range(i+1,len(ids)):pairs.append(dict(tag_a_id=ids[i],tag_a=names[ids[i]],tag_b_id=ids[j],tag_b=names[ids[j]],support_a=int(support[i]),support_b=int(support[j]),shared_problems=int(co[i,j]),cosine_distance=float(distances['cosine'][i,j]),jaccard_distance=float(distances['jaccard'][i,j])))
  write(folder/'pair_distances.csv',pairs)
  for a,b in EXAMPLES:
   if a not in ids or b not in ids:continue
   i,j=ids.index(a),ids.index(b)
   for key,(d,z) in models.items():
    for cut in SHOW:
     lab=fcluster(z,cut,criterion='distance');examples.append(dict(dataset=ds,model=key,cut=cut,tag_a_id=a,tag_a=names[a],tag_b_id=b,tag_b=names[b],shared_problems=int(co[i,j]),distance=float(d[i,j]),same_cluster=bool(lab[i]==lab[j])))
  for cut in SHOW:
   keys=list(models)
   for i,key in enumerate(keys):
    for other in keys[i+1:]:aris.append(dict(dataset=ds,cut=cut,model_a=key,model_b=other,adjusted_rand_index=float(adjusted_rand_score(fcluster(models[key][1],cut,criterion='distance'),fcluster(models[other][1],cut,criterion='distance')))))
  summary['datasets'][ds]=dsinfo
 write(OUT/'parameter_sweep.csv',sweeps);write(OUT/'matched_cluster_counts.csv',matched);write(OUT/'example_pairs.csv',examples);write(OUT/'partition_agreement.csv',aris)
 assert before=={str(p.relative_to(R)):sha(p) for p in protected};summary['checks']=['source_hashes_unchanged','all_3012_ids_unique','binary_matrix','distances_match_independent_count_formulas','finite_distances','valid_monotone_linkages','cut_1_single_cluster','unused_tags_only_excluded','all_rare_and_isolated_used_tags_retained'];dump(OUT/'summary.json',summary)
 fig,axes=plt.subplots(2,2,figsize=(15,10),sharex=True);colors={'average':'#237a8c','single':'#cb7840','complete':'#79569c'}
 for row,(ds,title) in enumerate(DATASETS.items()):
  for col,metric in enumerate(METRICS):
   ax=axes[row,col]
   for method in METHODS:
    data=[r for r in sweeps if r['dataset']==ds and r['metric']==metric and r['linkage']==method];ax.plot([r['cut'] for r in data],[r['clusters'] for r in data],label=METHODS[method],color=colors[method],marker='.',ms=4)
   ax.set_title(title+' / '+METRICS[metric]);ax.set_ylabel('クラスタ数');ax.set_xlabel('カット距離');ax.grid(alpha=.2);ax.legend()
 fig.suptitle('V4 タグ階層クラスタリング：距離2種類 × 連結法3種類',fontsize=16);fig.tight_layout(rect=(0,.03,1,.95));fig.text(.02,.015,'同じcutは同じ粒度を保証しません。目標40/80群での比較内訳も収録。',fontsize=10)
 for ext in ('png','svg'):fig.savefig(OUT/f'comparison.{ext}',dpi=140,facecolor='white')
 plt.close(fig);print(json.dumps({d:{k:v['cut_0_7']['clusters'] for k,v in s['models'].items()} for d,s in summary['datasets'].items()}))
if __name__=='__main__':main()
