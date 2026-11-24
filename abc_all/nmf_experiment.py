# -*- coding: utf-8 -*-
"""NMF comparison on the frozen SVD tag set. Local computation only."""
import argparse,csv,hashlib,json,sys,time,warnings,zipfile
from pathlib import Path
from collections import Counter
import numpy as np
import scipy,sklearn
from scipy.sparse import csr_matrix
from scipy.spatial.distance import pdist,squareform
from scipy.cluster.hierarchy import linkage,fcluster,cophenet,dendrogram,is_valid_linkage
from scipy.stats import spearmanr
from sklearn.decomposition import NMF
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from svd_experiment import read_matrix,partition_metrics,cluster_rows,top_neighbors,best_count_cut,EXAMPLES

ROOT=Path(__file__).resolve().parent
SVD=ROOT/'svd_experiment_20261112'
SOURCE=ROOT/'comparison_20261105'
OUT=ROOT/'nmf_experiment_20261119'
DATASETS={'all_difficulties':'全難易度','under_2000':'2000未満'}
DIMS=(8,16,32,64)
CUTS=[i/10 for i in range(1,11)]
MAX_ITER=5000
TOL=1e-5
MAIN_SEED=42

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(p,rows,fields=None):
    if fields is None:fields=list(rows[0]) if rows else []
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def cosdist(v):
    norms=np.linalg.norm(v,axis=1)
    if (norms<=1e-10).any():raise ValueError('Zero tag embedding: cosine distance undefined; inspect rather than fill.')
    unit=v/norms[:,None];d=np.clip(1-unit@unit.T,0,1)
    d=(d+d.T)/2;np.fill_diagonal(d,0)
    return d

def fit_nmf(a,k,init='nndsvda',seed=MAIN_SEED):
    t=time.perf_counter()
    model=NMF(n_components=k,init=init,solver='cd',beta_loss='frobenius',tol=TOL,max_iter=MAX_ITER,random_state=seed,alpha_W=0.0,alpha_H=0.0,l1_ratio=0.0,shuffle=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning)
        with threadpool_limits(limits=1):w=model.fit_transform(csr_matrix(a))
    h=model.components_.copy()
    norms=np.linalg.norm(h,axis=1)
    live=norms>1e-12
    hc=np.divide(h,norms[:,None],out=np.zeros_like(h),where=live[:,None])
    wc=w*norms[None,:]
    np.testing.assert_allclose(w@h,wc@hc,rtol=1e-10,atol=1e-12)
    assert np.min(wc)>=0 and np.min(hc)>=0
    residual=float(np.linalg.norm(a-wc@hc))
    np.testing.assert_allclose(residual,model.reconstruction_err_,rtol=1e-9,atol=1e-10)
    # Arbitrary positive rescaling of factors must not change the canonical distances.
    scaling=np.linspace(.5,2.0,k);w2=w*scaling;h2=h/scaling[:,None]
    canonical2=w2*np.linalg.norm(h2,axis=1)[None,:]
    np.testing.assert_allclose(canonical2,wc,rtol=1e-10,atol=1e-12)
    metadata=dict(components=k,initialization=init,seed=seed,iterations=int(model.n_iter_),max_iter=MAX_ITER,tolerance=TOL,converged=not any(issubclass(c.category,ConvergenceWarning) for c in caught),warnings=[str(c.message) for c in caught],seconds=time.perf_counter()-t,frobenius_reconstruction_error=residual,relative_squared_reconstruction_error=residual**2/float(np.sum(a*a)),active_components=int(live.sum()),minimum_tag_vector_norm=float(np.min(np.linalg.norm(wc,axis=1))))
    return wc,hc,metadata

def model_from_distance(d):
    z=linkage(squareform(d),method='average',optimal_ordering=True)
    assert is_valid_linkage(z,throw=True)
    return {'d':d,'z':z}

def setup_font():
    available={f.name for f in font_manager.fontManager.ttflist}
    font=next((n for n in ['Meiryo','Yu Gothic','MS Gothic'] if n in available),'DejaVu Sans')
    matplotlib.rcParams.update({'font.family':[font,'DejaVu Sans'],'axes.unicode_minus':False,'svg.fonttype':'none'})
    return font

def compute():
    OUT.mkdir(exist_ok=True)
    taxonomy=json.loads((ROOT/'taxonomy.json').read_text(encoding='utf-8'))
    names={r['tag_id']:r['tag'] for r in taxonomy};by_name={r['tag']:r['tag_id'] for r in taxonomy}
    previous=json.loads((SVD/'summary.json').read_text(encoding='utf-8'))
    protected=[ROOT/'taxonomy.json',ROOT/'svd_experiment.py']+list(SVD.rglob('*'))
    protected=[p for p in protected if p.is_file()]
    for ds in DATASETS:protected.extend(SOURCE/ds/n for n in ['problem_tag_matrix.csv','problems.csv','clusters.json','linkage.csv'])
    hashes={str(p.relative_to(ROOT)):sha(p) for p in protected}
    summary={'created':'2026-11-19','source_snapshot':'2026-11-05','main_components':32,'components':DIMS,'preprocessing':'exact same tags as SVD; tag x problem binary matrix; row L2 normalization; no centering or text input','objective':'minimize squared Frobenius norm of A-WH, W>=0,H>=0; no regularization','factor_scaling':'Normalize each nonzero H row to L2=1 and multiply corresponding W column by the original H row norm, preserving WH','tag_distance':'cosine distance of scale-canonical W rows; nonnegative coordinates imply range 0..1','main_initialization':'nndsvda','main_seed':MAIN_SEED,'solver':'coordinate descent','tolerance':TOL,'max_iter':MAX_ITER,'linkage':'average','paid_api_calls':0,'independent_human_validation':False,'versions':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},'source_sha256':hashes,'datasets':{}}
    parameter_rows=[];example_rows=[];initialization_rows=[];review=[]
    extra_names=[('連分数','Bellman-Ford 法','SVDで混在を確認した例'),('後退解析','Suffix Automaton','SVDで混在を確認した例'),('Map / 連想配列','離散対数','SVDで混在を確認した例'),('2-SAT','木の塗り分け','共通問題なしで近くなった例')]
    for ds,title in DATASETS.items():
        folder=OUT/ds;folder.mkdir(exist_ok=True)
        problem_ids,taxids,xall=read_matrix(ds)
        vector_rows=read_csv(SVD/ds/'svd_32/tag_vectors.csv');ids=[r['tag_id'] for r in vector_rows]
        x=xall[:,[taxids.index(t) for t in ids]];support=x.sum(axis=0)
        assert len(ids)==previous['datasets'][ds]['compared_tags']
        a=x.T.astype(float)/np.sqrt(support)[:,None]
        svectors=np.array([[float(r['v'+str(j+1)]) for j in range(32)] for r in vector_rows])
        excluded=read_csv(SVD/ds/'excluded_tags.csv');write_csv(folder/'excluded_tags.csv',excluded)
        index={t:i for i,t in enumerate(ids)};co=x.T.astype(np.int64)@x.astype(np.int64)
        models={}
        for key in ['jaccard','raw_cosine','svd_32']:
            d=np.zeros((len(ids),len(ids)))
            for r in read_csv(SVD/ds/'pair_distances.csv'):
                i,j=index[r['tag_a_id']],index[r['tag_b_id']];d[i,j]=d[j,i]=float(r[key+'_distance'])
            z=np.loadtxt(SVD/ds/key/'linkage.csv',delimiter=',',skiprows=1)
            models[key]={'d':d,'z':z}
        for k in DIMS:
            print(f'{ds}: fitting NMF {k}',flush=True)
            w,h,fit=fit_nmf(a,k)
            models['nmf_'+str(k)]=dict(model_from_distance(cosdist(w)),fit=fit)
            mf=folder/('nmf_'+str(k));mf.mkdir(exist_ok=True)
            np.savez_compressed(mf/'factors.npz',W=w,H=h,tag_ids=np.array(ids),problem_ids=np.array(problem_ids))
            write_csv(mf/'tag_vectors.csv',[dict(tag_id=t,tag=names[t],problem_count=int(support[i]),**{'v'+str(j+1):float(w[i,j]) for j in range(k)}) for i,t in enumerate(ids)])
            top_tags=[];top_problems=[]
            for component in range(k):
                for rank,i in enumerate(np.argsort(-w[:,component],kind='stable')[:10],1):top_tags.append(dict(component=component+1,rank=rank,tag_id=ids[i],tag=names[ids[i]],contribution=float(w[i,component])))
                for rank,j in enumerate(np.argsort(-h[component],kind='stable')[:10],1):top_problems.append(dict(component=component+1,rank=rank,problem_id=problem_ids[j],loading=float(h[component,j])))
            write_csv(mf/'component_top_tags.csv',top_tags);write_csv(mf/'component_top_problems.csv',top_problems);dump(mf/'fit.json',fit)
            print(f'{ds}: NMF {k}: iterations={fit["iterations"]}, converged={fit["converged"]}',flush=True)
        model_summary={}
        for method,m in models.items():
            d,z=m['d'],m['z'];mf=folder/method;mf.mkdir(exist_ok=True)
            np.savetxt(mf/'linkage.csv',z,delimiter=',',header='left,right,distance,leaf_count',comments='')
            coph=float(cophenet(z,squareform(d))[0]);values=squareform(d)
            msum={'cophenetic_correlation_in_own_space':coph,'distance_median':float(np.median(values)),'distance_exactly_1_fraction':float(np.mean(np.abs(values-1)<1e-10)),'fit':m.get('fit')}
            sweep=[]
            for cut in CUTS:
                metrics,labels=partition_metrics(d,z,cut)
                row=dict(dataset=ds,method=method,compared_tags=len(ids),**metrics);sweep.append(row);parameter_rows.append(row)
                if cut in [.7,.8,.9]:msum['cut_'+str(cut)]=metrics
                if method=='nmf_32' and cut in [.7,.8,.9]:
                    flat,groups=cluster_rows(labels,ids,names,support,x)
                    write_csv(mf/('cluster_members_cut_'+str(cut)+'.csv'),flat)
                    dump(mf/('clusters_cut_'+str(cut)+'.json'),{'cut':cut,'components':32,'compared_tags':len(ids),'excluded_active_tags':previous['datasets'][ds]['isolated_active_tags'],'clusters':groups})
            write_csv(mf/'cut_sweep.csv',sweep);model_summary[method]=msum
        # Match the existing SVD32 cut=0.7 count, and the Jaccard cut=0.9 count.
        matched=[]
        targets={'svd32_cut_0.7':previous['datasets'][ds]['models']['svd_32']['cut_0.7']['clusters'],'jaccard_cut_0.9':previous['datasets'][ds]['matched_comparison_target_clusters']}
        for target_name,target in targets.items():
            for method,m in models.items():
                cut,count=best_count_cut(m['z'],target);metrics,labels=partition_metrics(m['d'],m['z'],cut)
                matched.append(dict(dataset=ds,reference=target_name,method=method,target_clusters=target,actual_clusters=count,exact_match=count==target,cut=cut,silhouette_in_own_space=metrics['silhouette'],ari_vs_svd32_at_this_count=float(adjusted_rand_score(fcluster(models['svd_32']['z'],best_count_cut(models['svd_32']['z'],target)[0],criterion='distance'),labels))))
        write_csv(folder/'matched_cluster_counts.csv',matched)
        pairrows=[]
        for i in range(len(ids)):
            for j in range(i+1,len(ids)):
                pairrows.append(dict(tag_a_id=ids[i],tag_a=names[ids[i]],tag_b_id=ids[j],tag_b=names[ids[j]],support_a=int(support[i]),support_b=int(support[j]),shared_problems=int(co[i,j]),**{key+'_distance':float(m['d'][i,j]) for key,m in models.items()}))
        write_csv(folder/'pair_distances.csv',pairrows)
        newpairs=sorted((r for r in pairrows if r['shared_problems']==0),key=lambda r:(r['nmf_32_distance'],r['tag_a_id'],r['tag_b_id']))[:30]
        write_csv(folder/'newly_close_without_overlap.csv',newpairs)
        nearest=[]
        for method,m in models.items():
            for t,neighbors in top_neighbors(m['d'],ids).items():
                for rank,n in enumerate(neighbors,1):nearest.append(dict(method=method,tag_id=t,tag=names[t],rank=rank,neighbor_tag_id=n,neighbor_tag=names[n],distance=float(m['d'][index[t],index[n]]),shared_problems=int(co[index[t],index[n]])))
        write_csv(folder/'nearest_neighbors.csv',nearest)
        fixed_pairs=list(EXAMPLES)+[(by_name[a_name],by_name[b_name],note) for a_name,b_name,note in extra_names]
        for ta,tb,note in fixed_pairs:
            if ta not in index or tb not in index:continue
            i,j=index[ta],index[tb]
            row=dict(dataset=ds,comparison_note=note,tag_a_id=ta,tag_a=names[ta],tag_b_id=tb,tag_b=names[tb],shared_problems=int(co[i,j]),**{key+'_distance':float(m['d'][i,j]) for key,m in models.items()})
            for key in ['svd_32','nmf_32']:
                for cut in [.7,.9]:
                    labels=fcluster(models[key]['z'],cut,criterion='distance');row[key+'_same_at_cut_'+str(cut)]=bool(labels[i]==labels[j])
            example_rows.append(row)
        for r in newpairs[:15]:review.append(dict(dataset=ds,selection_reason='NMF32で近い共通問題なしの組',tag_a=r['tag_a'],tag_b=r['tag_b'],shared_problems=0,nmf32_distance=r['nmf_32_distance'],human_relation='',merge_as_learning_unit='',reviewer='',notes=''))
        ref=models['nmf_32'];ref_neighbors=top_neighbors(ref['d'],ids);ref_labels=fcluster(ref['z'],.7,criterion='distance');tri=np.triu_indices(len(ids),1)
        for seed in range(5):
            print(f'{ds}: random initialization {seed}',flush=True)
            w,h,fit=fit_nmf(a,32,init='random',seed=seed)
            m=model_from_distance(cosdist(w));nn=top_neighbors(m['d'],ids);metrics,labels=partition_metrics(m['d'],m['z'],.7)
            rf=folder/'initialization_runs'/('seed_'+str(seed));rf.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(rf/'factors.npz',W=w,H=h,tag_ids=np.array(ids),problem_ids=np.array(problem_ids));dump(rf/'fit.json',fit)
            initialization_rows.append(dict(dataset=ds,seed=seed,initialization='random',converged=fit['converged'],iterations=fit['iterations'],relative_squared_reconstruction_error=fit['relative_squared_reconstruction_error'],clusters_at_cut_0_7=metrics['clusters'],silhouette_at_cut_0_7=metrics['silhouette'],ari_vs_nndsvda_cut_0_7=float(adjusted_rand_score(ref_labels,labels)),nearest_neighbor_overlap_at_5=float(np.mean([len(set(nn[t])&set(ref_neighbors[t]))/5 for t in ids])),distance_spearman=float(spearmanr(m['d'][tri],ref['d'][tri]).statistic)))
        summary['datasets'][ds]={'problems':len(problem_ids),'original_active_tags':previous['datasets'][ds]['original_active_tags'],'compared_tags':len(ids),'isolated_active_tags':previous['datasets'][ds]['isolated_active_tags'],'unused_tags':previous['datasets'][ds]['unused_tags'],'models':model_summary,'matched_targets':targets}
        print(ds+': calculation complete',flush=True)
    write_csv(OUT/'parameter_sweep.csv',parameter_rows);write_csv(OUT/'example_pairs.csv',example_rows);write_csv(OUT/'review_pairs.csv',review);write_csv(OUT/'initialization_stability.csv',initialization_rows)
    assert hashes=={str(p.relative_to(ROOT)):sha(p) for p in protected}
    summary['checks']=['frozen_source_and_all_svd_artifacts_unchanged','same_tags_as_svd','nonnegative_factors','canonical_scale_preserves_WH','canonical_scale_invariant_to_factor_rescaling','stored_reconstruction_error_matches_actual_error','no_zero_norm_tag_vectors','valid_linkage']
    dump(OUT/'summary.json',summary)
    print(json.dumps({'output':str(OUT),'main_results':{d:summary['datasets'][d]['models']['nmf_32'] for d in DATASETS}},ensure_ascii=False,indent=2),flush=True)

def render():
    setup_font();summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    numeric={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.suffix in ['.npz','.json','.csv'] and p.name!='layout_verification.json'}
    for ds,title in DATASETS.items():
        mf=OUT/ds/'nmf_32';vrows=read_csv(mf/'tag_vectors.csv');labels=[r['tag_id']+' '+r['tag']+' (n='+r['problem_count']+')' for r in vrows];z=np.loadtxt(mf/'linkage.csv',delimiter=',',skiprows=1)
        for cut in [.7,.8,.9]:
            count=summary['datasets'][ds]['models']['nmf_32']['cut_'+str(cut)]['clusters']
            fig,ax=plt.subplots(figsize=(19,max(18,len(labels)*.20)))
            tree=dendrogram(z,labels=labels,orientation='right',leaf_font_size=9,color_threshold=np.nextafter(cut,np.inf),above_threshold_color='#78818b',ax=ax)
            ax.yaxis.set_ticks_position('left');ax.tick_params(axis='y',labelleft=True,labelright=False,left=True,right=False,length=3,pad=4)
            assert ax.yaxis.get_ticks_position()=='left' and tree['leaves']==dendrogram(z,no_plot=True)['leaves']
            ax.set_xlim(0,1.03);ax.axvline(cut,color='#b82739',ls='--',lw=1.2);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
            ax.set_xlabel('距離 = 1 − コサイン類似度 / 平均連結法')
            ax.set_title(f'{title}：NMF 32成分 / cut={cut:.1f}\n{len(labels)}タグ → {count}クラスタ（共起なしの1タグは別枠）',fontsize=14,pad=16)
            fig.text(.025,.012,'32成分は事前に選んだ表示例。最適値ではありません。n=タグの問題数。初期化NNDSVDa・成分の尺度を正規化。\n赤破線がカット位置。枝色は繰り返され、分野を表しません。同じcutでもSVD・Jaccard版と意味は異なります。',fontsize=9)
            fig.tight_layout(rect=(.015,.042,.995,.995))
            for ext in ['png','svg']:fig.savefig(mf/('dendrogram_cut_'+str(cut)+'.'+ext),dpi=140,facecolor='white')
            plt.close(fig)
        print(ds+': left-label figures saved',flush=True)
    sweep=read_csv(OUT/'parameter_sweep.csv');fig,axes=plt.subplots(2,2,figsize=(13,8))
    colors={'jaccard':'#677485','raw_cosine':'#d18c2e','svd_32':'#287ea5','nmf_8':'#ac7184','nmf_16':'#8763b0','nmf_32':'#219576','nmf_64':'#6c8b29'}
    for col,(ds,title) in enumerate(DATASETS.items()):
        pairs=read_csv(OUT/ds/'pair_distances.csv')
        for method,color in colors.items():
            values=[float(r[method+'_distance']) for r in pairs]
            axes[0,col].hist(values,bins=np.linspace(0,2,81),histtype='step',color=color,label=method,lw=1.2)
            r=[r for r in sweep if r['dataset']==ds and r['method']==method]
            axes[1,col].plot([float(v['cut']) for v in r],[int(v['clusters']) for v in r],color=color,label=method,marker='.',ms=4)
        axes[0,col].set_title(title+'：距離分布');axes[0,col].set_xlabel('距離（SVDを含む全範囲0〜2）');axes[0,col].set_ylabel('タグの組み合わせ数')
        axes[1,col].set_title(title+'：cutとクラスタ数');axes[1,col].set_xlabel('distance cut（手法間で同じ意味ではない）');axes[1,col].set_ylabel('クラスタ数')
        for ax in axes[:,col]:ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.suptitle('同じタグ集合で比較：Jaccard・コサイン・SVD・NMF',fontsize=14);fig.tight_layout(rect=(0,0,1,.95))
    for ext in ['png','svg']:fig.savefig(OUT/('comparison.'+ext),dpi=160)
    plt.close(fig)
    assert numeric=={str((OUT/p).relative_to(OUT)):sha(OUT/p) for p in numeric}
    dump(OUT/'layout_verification.json',{'labels':'left','distance_increases_to':'right','leaf_order_unchanged':True,'numerical_files_unchanged':True})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['compute','render','all'],default='all');args=parser.parse_args()
    if args.stage in ['compute','all']:compute()
    if args.stage in ['render','all']:render()
