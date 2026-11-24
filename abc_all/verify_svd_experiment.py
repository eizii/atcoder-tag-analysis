# -*- coding: utf-8 -*-
"""Independently reconcile saved SVD outputs against the frozen source matrices."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist,squareform
from scipy.cluster.hierarchy import fcluster,cophenet,is_valid_linkage
from scipy.linalg import eigvalsh
from sklearn.metrics import silhouette_score
from PIL import Image
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'svd_experiment_20261112'
summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
checks=[]
for name,digest in summary['source_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
checks.append('All frozen source hashes are unchanged')
for dataset,info in summary['datasets'].items():
    with (ROOT/'comparison_20261105'/dataset/'problem_tag_matrix.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);headers=reader.fieldnames[1:];rows=list(reader)
    x=np.array([[int(r[t]) for t in headers] for r in rows],dtype=float)
    with (OUT/dataset/'excluded_tags.csv').open(encoding='utf-8-sig',newline='') as f:excluded=list(csv.DictReader(f))
    excluded_ids={r['tag_id'] for r in excluded}
    ids=[t for t in headers if t not in excluded_ids];xi=x[:,[headers.index(t) for t in ids]]
    assert len(ids)==info['compared_tags']
    original_active=int((x.sum(axis=0)>0).sum())
    isolated=[r for r in excluded if r['reason']=='no_cooccurrence_with_any_other_tag']
    assert len(ids)+len(isolated)==original_active==info['original_active_tags']
    for r in isolated:
        column=x[:,headers.index(r['tag_id'])]
        assert float(column@xi.sum(axis=1))==0 and column.sum()>0
    a=xi.T/np.sqrt(xi.sum(axis=0))[:,None]
    with threadpool_limits(limits=1):eigenvalues=eigvalsh(a@a.T)[::-1]
    with (OUT/dataset/'singular_values.csv').open(encoding='utf-8-sig',newline='') as f:saved_s=np.array([float(r['singular_value']) for r in csv.DictReader(f)])
    np.testing.assert_allclose(saved_s**2,np.maximum(eigenvalues,0),atol=2e-12)
    distances={'jaccard':squareform(pdist(xi.T.astype(bool),metric='jaccard')),'raw_cosine':squareform(pdist(a,metric='cosine'))}
    for k in summary['dimensions']:
        with (OUT/dataset/('svd_'+str(k))/'tag_vectors.csv').open(encoding='utf-8-sig',newline='') as f:vrows=list(csv.DictReader(f))
        assert [r['tag_id'] for r in vrows]==ids
        v=np.array([[float(r['v'+str(j+1)]) for j in range(k)] for r in vrows])
        assert np.isfinite(v).all() and np.min(np.linalg.norm(v,axis=1))>1e-10
        np.testing.assert_allclose(np.sum(v*v),np.sum(saved_s[:k]**2),rtol=1e-12)
        distances['svd_'+str(k)]=squareform(pdist(v,metric='cosine'))
    index={t:i for i,t in enumerate(ids)}
    with (OUT/dataset/'pair_distances.csv').open(encoding='utf-8-sig',newline='') as f:pairs=list(csv.DictReader(f))
    assert len(pairs)==len(ids)*(len(ids)-1)//2
    for r in pairs:
        i,j=index[r['tag_a_id']],index[r['tag_b_id']]
        assert int(r['shared_problems'])==int(xi[:,i]@xi[:,j])
        for method,d in distances.items():assert abs(float(r[method+'_distance'])-d[i,j])<1e-10
    for method,d in distances.items():
        z=np.loadtxt(OUT/dataset/method/'linkage.csv',delimiter=',',skiprows=1)
        assert is_valid_linkage(z,throw=True) and len(z)+1==len(ids)
        np.fill_diagonal(d,0)
        c=float(cophenet(z,squareform(d))[0])
        assert abs(c-info['models'][method]['cophenetic_correlation_in_own_distance_space'])<1e-10
        for cut in [.7,.8,.9]:
            labels=fcluster(z,cut,criterion='distance')
            metrics=info['models'][method]['cut_'+str(cut)]
            assert len(set(labels))==metrics['clusters']
            score=silhouette_score(d,labels,metric='precomputed') if 1<len(set(labels))<len(labels) else None
            assert score is None and metrics['silhouette'] is None or score is not None and abs(score-metrics['silhouette'])<1e-10
            if method=='svd_32':
                contents=json.loads((OUT/dataset/method/('clusters_cut_'+str(cut)+'.json')).read_text(encoding='utf-8'))
                groups=contents['clusters'];assert len(groups)==len(set(labels))
                flat=[t for g in groups for t in g['tag_ids']]
                assert len(flat)==len(set(flat))==len(ids) and set(flat)==set(ids)
                for g in groups:
                    idx=[index[t] for t in g['tag_ids']]
                    assert len(set(labels[idx]))==1
                    assert g['problem_count']==int(xi[:,idx].any(axis=1).sum())
                png=OUT/dataset/method/('dendrogram_cut_'+str(cut)+'.png')
                with Image.open(png) as im:assert im.width>2000 and im.height>2000;im.verify()
                svg=(OUT/dataset/method/('dendrogram_cut_'+str(cut)+'.svg')).read_text(encoding='utf-8')
                assert '<svg' in svg
    checks.extend([dataset+': singular values independently checked by Gram-matrix eigenvalues',dataset+': saved tag vectors reproduce all exported cosine distances',dataset+': overlap counts and Jaccard distances independently reconciled',dataset+': saved linkage, silhouette and cophenetic metrics agree',dataset+': every SVD32 cluster membership and problem union agrees',dataset+': all six PNG/SVG full dendrogram files exist and parse'])
result={'passed':True,'checks':checks,'independent_human_semantic_validation':False}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
