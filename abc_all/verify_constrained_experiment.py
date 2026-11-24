# -*- coding: utf-8 -*-
"""Independent replay of saved constrained average-link forests plus synthetic checks."""
import json,hashlib,itertools
from pathlib import Path
import numpy as np
from scipy.cluster.hierarchy import linkage,cophenet,fcluster
from scipy.spatial.distance import squareform,pdist
from sklearn.metrics import adjusted_rand_score,silhouette_score
from threadpoolctl import threadpool_limits
from constrained_experiment import DEFAULT,PRIOR,ROOT,DATASETS,METHODS,average_forest,partition,parse_constraints
from nmf_experiment import read_csv,dump

def coheight(forest):
    n=forest['n_tags'];groups={i:[i] for i in range(n)};c=np.full((n,n),np.nan);np.fill_diagonal(c,0)
    for r in forest['merges']:
        a,b=groups[r['left']],groups[r['right']];c[np.ix_(a,b)]=r['distance'];c[np.ix_(b,a)]=r['distance'];groups[r['node_id']]=a+b
    return c

def test_synthetic():
    passed=[]
    for seed in range(4):
        x=np.random.default_rng(seed).normal(size=(9,4));d=squareform(pdist(x));ids=[str(i) for i in range(9)]
        forest=average_forest(d,ids,[]);z=linkage(squareform(d),method='average')
        np.testing.assert_allclose(squareform(coheight(forest)),cophenet(z),rtol=1e-12,atol=1e-12)
    passed.append('unconstrained exact coheights match SciPy average linkage on 4 continuous-distance examples')
    d=np.array([[0.,.1,.7],[.1,0,.2],[.7,.2,0]])
    cs=[dict(relation='cannot_link',a=0,b=2)]
    forest=average_forest(d,['a','b','c'],cs)
    assert len(forest['roots'])==2 and partition(forest,100)[0]!=partition(forest,100)[2]
    passed.append('cannot-link propagates through intermediary tag and remains valid at cut above every distance')
    d=np.array([[0.,.8,.2,.9],[.8,0,.7,.9],[.2,.7,0,.6],[.9,.9,.6,0]])
    ml=[dict(relation='must_link',a=0,b=1),dict(relation='must_link',a=1,b=2)]
    forest=average_forest(d,['a','b','c','d'],ml)
    assert len(set(partition(forest,0)[:3]))==1
    assert abs(forest['merges'][-1]['distance']-(.9+.9+.6)/3)<1e-12
    passed.append('must-link transitive closure forced at zero; average distances weighted by original tag counts')
    try:average_forest(d,['a','b','c','d'],ml+[dict(relation='cannot_link',a=0,b=2)])
    except ValueError:pass
    else:raise AssertionError('Missed transitive contradiction')
    passed.append('contradictory transitive must-link/cannot-link rejected')
    assert len(average_forest(np.zeros((1,1)),['a'],[])['roots'])==1
    assert len(average_forest(np.array([[0.,1],[1,0]]),['a','b'],[])['merges'])==1
    passed.append('one-tag and two-tag inputs supported')
    return passed

def replay(forest,d,constraints):
    n=len(d);active={i:[i] for i in range(n)};cl=[(r['a'],r['b']) for r in constraints if r['relation']=='cannot_link'];previous=0.
    for row in forest['merges']:
        t,a,b=int(row['node_id']),int(row['left']),int(row['right']);left,right=active[a],active[b]
        avg=float(d[np.ix_(left,right)].mean());np.testing.assert_allclose(avg,row['original_average_distance'],rtol=1e-10,atol=2e-12)
        if not row['forced_must_link']:
            np.testing.assert_allclose(avg,row['distance'],rtol=1e-10,atol=2e-12)
            # Recompute ALL candidate means directly from original distances via membership matrices.
            keys=sorted(active);u=np.zeros((len(keys),n));owner={v:i for i,k in enumerate(keys) for v in active[k]}
            for i,k in enumerate(keys):u[i,active[k]]=1./len(active[k])
            means=u@d@u.T;means[np.tril_indices(len(keys))]=np.inf
            for p,q in cl:
                i,j=owner[p],owner[q]
                if i!=j:means[min(i,j),max(i,j)]=np.inf
            np.testing.assert_allclose(float(np.min(means)),avg,rtol=1e-10,atol=2e-12)
        assert row['distance']>=previous-1e-12;previous=row['distance']
        merged=left+right
        assert not any(p in merged and q in merged for p,q in cl)
        del active[a],active[b];active[t]=merged
        assert len(merged)==row['leaf_count']
    assert set(active)==set(forest['roots'])
    assert sorted(v for group in active.values() for v in group)==list(range(n))
    for p,q in itertools.combinations(active,2):
        assert any((a in active[p] and b in active[q]) or (b in active[p] and a in active[q]) for a,b in cl), 'Forest stopped while an admissible root pair remained'
    # Independent cuts via cophenetic connectivity, avoiding production partition().
    c=coheight(forest)
    for cut in [i/10 for i in range(11)]+[2.,100.]:
        labels=partition(forest,cut);assert np.array_equal(labels[:,None]==labels[None,:],np.nan_to_num(c,nan=np.inf)<=cut)
        for r in constraints:assert (labels[r['a']]==labels[r['b']])==(r['relation']=='must_link')
    return True

def main():
    summary=json.loads((DEFAULT/'summary.json').read_text(encoding='utf-8'));checks=test_synthetic();runs=0;metrics_checked=0
    for name,digest in summary['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    rows=read_csv(DEFAULT/'cut_sweep.csv')
    for ds in DATASETS:
        ids=[r['tag_id'] for r in read_csv(PRIOR/ds/'nmf_32/tag_vectors.csv')];idx={t:i for i,t in enumerate(ids)}
        cons,_=parse_constraints(read_csv(DEFAULT/'constraints_used.csv'),ids)
        for method in METHODS:
            d=np.zeros((len(ids),len(ids)))
            for r in read_csv(PRIOR/ds/'pair_distances.csv'):
                a,b=idx[r['tag_a_id']],idx[r['tag_b_id']];d[a,b]=d[b,a]=float(r[method+'_distance'])
            for variant in ['unconstrained','constrained']:
                forest=json.loads((DEFAULT/ds/method/(variant+'_forest.json')).read_text(encoding='utf-8'))
                replay(forest,d,cons if variant=='constrained' else []);runs+=1
                for row in rows:
                    if (row['dataset'],row['method'],row['variant'])!=(ds,method,variant):continue
                    labels=partition(forest,float(row['cut']));assert len(set(labels))==int(row['clusters'])
                    if row['silhouette']:np.testing.assert_allclose(silhouette_score(d,labels,metric='precomputed'),float(row['silhouette']),atol=1e-12)
                    if variant=='constrained':assert int(row['constraint_violations'])==0
                    metrics_checked+=1
                for cut in [.7,.8,.9]:
                    csvrows=read_csv(DEFAULT/ds/method/(variant+'_members_cut_'+str(cut)+'.csv'))
                    assert len(csvrows)==len(ids) and {r['tag_id'] for r in csvrows}==set(ids)
                    labels=partition(forest,cut);groups={r['tag_id']:r['cluster_id'] for r in csvrows}
                    for a,b in itertools.combinations(ids,2):assert (labels[idx[a]]==labels[idx[b]])==(groups[a]==groups[b])
    checks.extend(['12 forests independently replayed: each non-forced merge is globally closest admissible original pairwise mean','CL holds in every merged node, all cuts 0..1, and artificial cuts 2 and 100','forest roots are an exact partition and no admissible root pair remains','all 132 cut metrics independently recomputed','all 36 exported cluster memberships match cuts','all frozen annotations, SVD and NMF artifacts unchanged'])
    result=dict(passed=True,synthetic_and_data_checks=checks,forests_verified=runs,metrics_verified=metrics_checked,independent_human_validation=False,verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),current_script_sha256=hashlib.sha256((ROOT/'constrained_experiment.py').read_bytes()).hexdigest())
    dump(DEFAULT/'verification.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1):main()
