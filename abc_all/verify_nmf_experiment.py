# -*- coding: utf-8 -*-
"""Independent reconciliation of NMF factors, distances, and saved clustering."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist,squareform
from scipy.linalg import svdvals
from scipy.cluster.hierarchy import fcluster,cophenet,is_valid_linkage
from sklearn.metrics import silhouette_score,adjusted_rand_score
from threadpoolctl import threadpool_limits
from PIL import Image
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'nmf_experiment_20261119'
SVD=ROOT/'svd_experiment_20261112'
summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))

def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def distance(w):
    norms=np.linalg.norm(w,axis=1);unit=w/norms[:,None]
    d=np.clip(1-unit@unit.T,0,1);d=(d+d.T)/2;np.fill_diagonal(d,0)
    return d

checks=[];fit_checks=[]
for name,digest in summary['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
checks.append('All original source files and all previous SVD artifacts unchanged')
for ds,info in summary['datasets'].items():
    input_rows=read_csv(ROOT/'comparison_20261105'/ds/'problem_tag_matrix.csv')
    problem_ids=[r['problem_id'] for r in input_rows]
    refs=read_csv(SVD/ds/'svd_32/tag_vectors.csv');ids=[r['tag_id'] for r in refs]
    x=np.array([[int(r[t]) for t in ids] for r in input_rows],dtype=float)
    a=x.T/np.sqrt(x.sum(axis=0))[:,None]
    with threadpool_limits(limits=1):s=svdvals(a)
    assert len(ids)==info['compared_tags']
    pair_rows=read_csv(OUT/ds/'pair_distances.csv');assert len(pair_rows)==len(ids)*(len(ids)-1)//2
    index={t:i for i,t in enumerate(ids)};by_method={}
    # Cross-check every factor file, including all five random initializations.
    for fp in sorted((OUT/ds).rglob('factors.npz')):
        with np.load(fp) as data:w=data['W'];h=data['H'];saved_ids=data['tag_ids'].tolist();saved_problems=data['problem_ids'].tolist()
        fit=json.loads(fp.with_name('fit.json').read_text(encoding='utf-8'));k=fit['components']
        assert saved_ids==ids and saved_problems==problem_ids
        assert w.shape==(len(ids),k) and h.shape==(k,len(problem_ids))
        assert np.isfinite(w).all() and np.isfinite(h).all() and w.min()>=0 and h.min()>=0
        rownorms=np.linalg.norm(h,axis=1);live=rownorms>1e-12
        np.testing.assert_allclose(rownorms[live],1,atol=1e-12)
        assert np.min(np.linalg.norm(w,axis=1))>1e-10
        residual=float(np.linalg.norm(a-w@h))
        assert abs(residual-fit['frobenius_reconstruction_error'])<1e-9
        assert abs(residual**2/np.sum(a*a)-fit['relative_squared_reconstruction_error'])<1e-10
        # Best unconstrained rank-k SVD approximation is a lower bound on NMF's loss.
        assert residual**2+1e-8>=float(np.sum(s[k:]**2))
        # Canonicalization should undo the NMF scale ambiguity exactly.
        scale=np.linspace(.3,2.7,k);ws=w*scale;hs=h/scale[:,None];canonical=ws*np.linalg.norm(hs,axis=1)[None,:]
        np.testing.assert_allclose(canonical,w,atol=1e-12)
        d=distance(w)
        np.testing.assert_allclose(d,squareform(pdist(w,metric='cosine')),atol=1e-12)
        if fp.parent.parent.name!='initialization_runs':
            method=fp.parent.name;by_method[method]=d
            vector_rows=read_csv(fp.with_name('tag_vectors.csv'))
            assert [r['tag_id'] for r in vector_rows]==ids
            vectors=np.array([[float(r['v'+str(j+1)]) for j in range(k)] for r in vector_rows])
            np.testing.assert_array_equal(vectors,w)
        fit_checks.append(dict(dataset=ds,path=str(fp.relative_to(OUT)),converged=fit['converged'],iterations=fit['iterations']))
    for method in ['jaccard','raw_cosine','svd_32']:
        d=np.zeros((len(ids),len(ids)))
        for r in pair_rows:
            i,j=index[r['tag_a_id']],index[r['tag_b_id']];d[i,j]=d[j,i]=float(r[method+'_distance'])
        by_method[method]=d
    for r in pair_rows:
        i,j=index[r['tag_a_id']],index[r['tag_b_id']]
        assert int(r['shared_problems'])==int(x[:,i]@x[:,j])
        for method,d in by_method.items():assert abs(float(r[method+'_distance'])-d[i,j])<1e-10
    for method,d in by_method.items():
        z=np.loadtxt(OUT/ds/method/'linkage.csv',delimiter=',',skiprows=1)
        assert is_valid_linkage(z,throw=True) and len(z)+1==len(ids)
        expected=info['models'][method]
        assert abs(float(cophenet(z,squareform(d))[0])-expected['cophenetic_correlation_in_own_space'])<1e-9
        for cut in [.7,.8,.9]:
            labels=fcluster(z,cut,criterion='distance');metrics=expected['cut_'+str(cut)]
            assert len(set(labels))==metrics['clusters']
            measured=silhouette_score(d,labels,metric='precomputed') if 1<len(set(labels))<len(ids) else None
            assert measured is None and metrics['silhouette'] is None or measured is not None and abs(measured-metrics['silhouette'])<1e-10
            if method=='nmf_32':
                data=json.loads((OUT/ds/method/('clusters_cut_'+str(cut)+'.json')).read_text(encoding='utf-8'))
                groups=data['clusters'];flat=[t for g in groups for t in g['tag_ids']]
                assert set(flat)==set(ids) and len(flat)==len(ids) and len(groups)==metrics['clusters']
                for g in groups:
                    indexes=[index[t] for t in g['tag_ids']]
                    assert len(set(labels[indexes]))==1
                    assert g['problem_count']==int(x[:,indexes].any(axis=1).sum())
                with Image.open(OUT/ds/method/('dendrogram_cut_'+str(cut)+'.png')) as im:assert im.width>2000 and im.height>2000;im.verify()
                svg=(OUT/ds/method/('dendrogram_cut_'+str(cut)+'.svg')).read_text(encoding='utf-8');assert '<svg' in svg
    # Validate initial-value comparisons using each independently stored factorization.
    ref_labels=fcluster(np.loadtxt(OUT/ds/'nmf_32/linkage.csv',delimiter=',',skiprows=1),.7,criterion='distance')
    from scipy.cluster.hierarchy import linkage
    for row in read_csv(OUT/'initialization_stability.csv'):
        if row['dataset']!=ds:continue
        with np.load(OUT/ds/'initialization_runs'/('seed_'+row['seed'])/'factors.npz') as data:d=distance(data['W'])
        z=linkage(squareform(d),method='average',optimal_ordering=True);labels=fcluster(z,.7,criterion='distance')
        assert len(set(labels))==int(row['clusters_at_cut_0_7'])
        assert abs(adjusted_rand_score(ref_labels,labels)-float(row['ari_vs_nndsvda_cut_0_7']))<1e-12
    checks.extend([ds+': nonnegative factors and unit-norm component patterns',ds+': all factor reconstructions agree with saved losses and SVD lower bounds',ds+': canonical factor distances invariant under positive rescaling',ds+': all saved tag vectors and all pair distances reconciled',ds+': cluster membership, problem unions, silhouette and cophenetic metrics reconciled',ds+': random initialization group counts and ARI independently reproduced',ds+': PNG and SVG files parse'])
layout=json.loads((OUT/'layout_verification.json').read_text(encoding='utf-8'));assert layout['labels']=='left' and layout['numerical_files_unchanged']
result={'passed':True,'checks':checks,'fit_runs':fit_checks,'all_fit_runs_converged':all(r['converged'] for r in fit_checks),'independent_human_semantic_validation':False}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
