# -*- coding: utf-8 -*-
"""Independently verify distance formulas, every greedy merge, and partitions."""
import csv,json,hashlib
from pathlib import Path
import numpy as np
from scipy.cluster.hierarchy import fcluster
from scipy.sparse.csgraph import connected_components
R=Path(__file__).resolve().parent;O=R/'hierarchical_v4_20261124'
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def same(a,b):return np.array_equal(np.equal.outer(a,a),np.equal.outer(b,b))
def main():
 s=json.loads((O/'summary.json').read_text(encoding='utf-8'));checks=[];merges=0;parts=0
 for name,h in s['source_sha256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h,name
 source=read(R/'output_v4/problem_tag_matrix.csv');sourceby={r['problem_id']:r for r in source}
 sweeps=read(O/'parameter_sweep.csv');matched=read(O/'matched_cluster_counts.csv')
 for ds,dsinfo in s['datasets'].items():
  f=O/ds;tags=read(f/'included_tags.csv');ids=[r['tag_id'] for r in tags];rows=read(f/'problem_tag_matrix.csv');x=np.array([[int(r[t]) for t in ids] for r in rows],dtype=np.int64);n=len(ids);counts=x.sum(axis=0)
  assert len(rows)==dsinfo['problems'] and all(r==sourceby[r['problem_id']] for r in rows)
  assert len(tags)==dsinfo['active_tags'] and all(counts>0) and np.array_equal(counts,[int(t['problem_count']) for t in tags])
  if ds=='under_2000':assert all(r['difficulty']!='' and float(r['difficulty'])<2000 for r in read(f/'problems.csv'))
  for metric in s['distance_metrics']:
   d=np.load(f/f'{metric}_distance.npy');intersection=x.T@x
   expected=1-intersection/(counts[:,None]+counts[None,:]-intersection) if metric=='jaccard' else 1-intersection/np.sqrt(counts[:,None]*counts[None,:])
   np.fill_diagonal(expected,0);np.testing.assert_allclose(d,expected,atol=1e-12);assert np.isfinite(d).all() and d.min()>=0 and d.max()<=1
   for method in s['linkages']:
    mf=f/(metric+'_'+method);z=np.loadtxt(mf/'linkage.csv',delimiter=',',skiprows=1);assert z.shape==(n-1,4)
    work=np.full((2*n-1,2*n-1),np.inf);work[:n,:n]=d;np.fill_diagonal(work,np.inf);active=set(range(n));members={i:[i] for i in range(n)};sizes={i:1 for i in range(n)}
    for step,(aa,bb,h,number) in enumerate(z):
     a,b=int(aa),int(bb);assert a in active and b in active and a!=b
     ix=sorted(active);minimum=work[np.ix_(ix,ix)].min();assert abs(h-minimum)<2e-12,(ds,metric,method,step,'not global minimum',h,minimum)
     block=d[np.ix_(members[a],members[b])];exact={'single':np.min,'complete':np.max,'average':np.mean}[method](block)
     assert abs(h-exact)<2e-12,(ds,metric,method,step,'wrong linkage height')
     c=n+step;members[c]=members.pop(a)+members.pop(b);sizes[c]=sizes[a]+sizes[b];assert number==sizes[c]
     active.remove(a);active.remove(b)
     for v in active:
      value=min(work[a,v],work[b,v]) if method=='single' else max(work[a,v],work[b,v]) if method=='complete' else (sizes[a]*work[a,v]+sizes[b]*work[b,v])/sizes[c]
      work[c,v]=work[v,c]=value
     active.add(c);merges+=1
    assert len(active)==1 and len(members[next(iter(active))])==n
    for cut in s['display_cuts']:
     labs=fcluster(z,cut,criterion='distance');obj=json.loads((mf/f'clusters_cut_{cut:.1f}.json').read_text(encoding='utf-8'));got={t:g['cluster_id'] for g in obj['clusters'] for t in g['tag_ids']};assert len(got)==n and set(got)==set(ids);assert same(labs,[got[t] for t in ids])
     for g in obj['clusters']:
      ix=[ids.index(t) for t in g['tag_ids']];assert g['problem_count']==int(x[:,ix].any(axis=1).sum()) and g['tag_count']==len(ix)
      if method=='complete':assert d[np.ix_(ix,ix)].max()<=cut+1e-12
     row=next(r for r in sweeps if r['dataset']==ds and r['metric']==metric and r['linkage']==method and float(r['cut'])==cut)
     assert int(row['clusters'])==len(obj['clusters']) and int(row['largest_cluster_tags'])==max(g['tag_count'] for g in obj['clusters'])
     if method=='single':
      k,cc=connected_components(d<=cut,directed=False);assert same(labs,cc),'single must equal threshold-graph connected components'
     parts+=1
    for target in s['matched_cluster_targets']:
     row=next(r for r in matched if r['dataset']==ds and r['metric']==metric and r['linkage']==method and int(r['target_clusters'])==target);cut=float(row['cut']);k=len(set(fcluster(z,cut,criterion='distance')));assert k==int(row['actual_clusters'])
     best=min(abs(len(set(fcluster(z,float(c),criterion='distance')))-target) for c in np.r_[0,np.unique(z[:,2]),1]);assert abs(k-target)==best
    assert (mf/'dendrogram.png').stat().st_size>10000 and (mf/'dendrogram.svg').stat().st_size>10000
    checks.append(dict(dataset=ds,metric=metric,linkage=method,all_merges_global_minimum=True,heights_match_original_pair_reduction=True))
 report=dict(checks_passed=True,conditions=len(checks),verified_merges=merges,verified_display_partitions=parts,source_hashes_unchanged=True,single_equals_threshold_graph_components=True,complete_cluster_diameters_bounded_by_cut=True,matched_cuts_nearest_achievable=True,details=checks)
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='details'}))
if __name__=='__main__':main()
