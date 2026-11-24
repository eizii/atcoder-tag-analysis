# -*- coding: utf-8 -*-
"""Exploratory tag SVD on frozen annotations. No external APIs or app changes."""
import csv, hashlib, json, sys, zipfile
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.linalg import svd
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram, is_valid_linkage
from scipy.stats import spearmanr
from sklearn.metrics import silhouette_samples, adjusted_rand_score
from threadpoolctl import threadpool_limits
import scipy, sklearn, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'comparison_20261105'
OUT = ROOT / 'svd_experiment_20261112'
DIMS = (8, 16, 32, 64)
MAIN_DIM = 32
CUTS = [i / 10 for i in range(1, 11)] + [1.1, 1.25, 1.5, 2.0]
DATASETS = {'all_difficulties': '全難易度', 'under_2000': '2000未満'}
EXAMPLES = [('T053','T233','最小全域木とその解法'),('T053','T234','最小全域木とその解法'),('T233','T234','同じ課題の別解法'),('T032','T033','フローとカット'),('T036','T037','ゲームの解法'),('T132','T196','演算と実装技法'),('T001','T003','区間集計のデータ構造'),('T022','T027','一般DPと木DP'),('T066','T144','BFSと0-1 BFS'),('T066','T067','探索手法'),('T010','T011','異なるキュー操作'),('T063','T064','探索手法'),('T175','T187','最短路の別解法')]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
def write_csv(p, rows, fields=None):
    if fields is None: fields = list(rows[0]) if rows else []
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=fields);writer.writeheader();writer.writerows(rows)
def read_matrix(dataset):
    with (SOURCE/dataset/'problem_tag_matrix.csv').open(encoding='utf-8-sig', newline='') as f:
        reader=csv.reader(f);tids=next(reader)[1:];rows=list(reader)
    ids=[r[0] for r in rows]
    x=np.array([[int(v) for v in r[1:]] for r in rows],dtype=np.uint8)
    assert len(set(ids))==len(ids) and np.isin(x,[0,1]).all()
    return ids,tids,x

def cosine_matrix(vectors):
    norms=np.linalg.norm(vectors,axis=1)
    assert np.min(norms)>1e-10, 'Zero latent vector; do not assign a cosine distance to it.'
    unit=vectors/norms[:,None]
    distances=np.clip(1-unit@unit.T,0,2)
    distances=(distances+distances.T)/2
    np.fill_diagonal(distances,0)
    return distances

def partition_metrics(d,z,cut):
    labels=fcluster(z,cut,criterion='distance')
    counts=Counter(labels);single=np.array([counts[label]==1 for label in labels])
    n_clusters=len(counts)
    values=silhouette_samples(d,labels,metric='precomputed') if 1<n_clusters<len(labels) else None
    return dict(cut=float(cut),clusters=n_clusters,singleton_clusters=sum(c==1 for c in counts.values()),multi_tag_clusters=sum(c>1 for c in counts.values()),singleton_tag_fraction=float(single.mean()),silhouette=float(values.mean()) if values is not None else None,silhouette_non_singleton=float(values[~single].mean()) if values is not None and (~single).any() else None),labels

def cluster_rows(labels,tag_ids,names,support,x):
    rows=[];groups=[]
    for label in sorted(set(labels)):
        idx=np.flatnonzero(labels==label);members=[tag_ids[i] for i in idx]
        problem_count=int(x[:,idx].any(axis=1).sum());cluster_id='C_'+min(members)
        group=dict(cluster_id=cluster_id,tag_ids=members,tags=[names[t] for t in members],tag_count=len(members),problem_count=problem_count)
        groups.append(group)
        for i in idx: rows.append(dict(cluster_id=cluster_id,tag_id=tag_ids[i],tag=names[tag_ids[i]],tag_problem_count=int(support[i]),cluster_problem_count=problem_count))
    return rows,groups

def best_count_cut(z,target):
    options=np.r_[0,np.unique(z[:,2]),2.0]
    counts=[len(set(fcluster(z,float(c),criterion='distance'))) for c in options]
    index=min(range(len(options)),key=lambda i:(abs(counts[i]-target),abs(options[i]-0.9)))
    return float(options[index]),int(counts[index])

def top_neighbors(d,ids,k=5):
    result={}
    for i,t in enumerate(ids):
        order=sorted((j for j in range(len(ids)) if j!=i),key=lambda j:(d[i,j],ids[j]))[:k]
        result[t]=[ids[j] for j in order]
    return result

def draw_tree(z,labels,title,cut,prefix):
    fig,ax=plt.subplots(figsize=(19,max(18,len(labels)*.20)))
    tree=dendrogram(z,labels=labels,orientation='right',leaf_font_size=9,color_threshold=np.nextafter(cut,np.inf),above_threshold_color='#78818b',ax=ax)
    ax.axvline(cut,color='#b82739',ls='--',lw=1.2)
    ax.set_xlim(0,max(1.03,float(z[-1,2])+.03,cut+.03))
    ax.tick_params(axis='y',length=3,pad=4)
    ax.yaxis.set_ticks_position('left')
    ax.tick_params(axis='y',labelleft=True,labelright=False,left=True,right=False)
    assert ax.yaxis.get_ticks_position()=='left'
    assert tree['leaves']==dendrogram(z,no_plot=True)['leaves']
    ax.set_xlabel('距離 = 1 − コサイン類似度 / 平均連結法')
    ax.set_title(title,fontsize=14,pad=16)
    ax.grid(axis='x',alpha=.22);ax.set_axisbelow(True)
    fig.text(.025,.012,'32次元は事前に選んだ表示例。最適値ではありません。n=タグの問題数。文字列処理は共起情報なしのため別枠。\n赤破線がカット位置。枝色は繰り返され、分野を表しません。Jaccard距離の同じcutとは意味が異なります。',fontsize=9)
    fig.tight_layout(rect=(.015,.042,.995,.995))
    for ext in ('png','svg'):fig.savefig(str(prefix)+'.'+ext,dpi=140,facecolor='white')
    plt.close(fig)

def main():
    OUT.mkdir(exist_ok=True)
    names={r['tag_id']:r['tag'] for r in json.loads((ROOT/'taxonomy.json').read_text(encoding='utf-8'))}
    original_summary=json.loads((SOURCE/'comparison_summary.json').read_text(encoding='utf-8'))
    protected=[ROOT/'taxonomy.json',SOURCE/'comparison_summary.json']
    for dataset in DATASETS:
        protected += [SOURCE/dataset/n for n in ['problem_tag_matrix.csv','problems.csv','clusters.json','linkage.csv']]
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    fonts={f.name for f in font_manager.fontManager.ttflist}
    font=next((n for n in ['Meiryo','Yu Gothic','MS Gothic'] if n in fonts),'DejaVu Sans')
    matplotlib.rcParams.update({'font.family':[font,'DejaVu Sans'],'axes.unicode_minus':False,'svg.fonttype':'none'})
    summary={'created':'2026-11-12','source_snapshot':'2026-11-05','main_dimension':MAIN_DIM,'dimensions':DIMS,'preprocessing':'transpose to tag x problem; row L2 normalize; no centering; no text features','solver':'scipy.linalg.svd exact thin SVD, LAPACK gesdd, one BLAS thread','representation':'Y = U_k @ diag(s_k), cosine distance between rows','linkage':'average','paid_api_calls':0,'independent_human_validation':False,'source_sha256':before,'versions':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},'datasets':{}}
    all_sweep=[];examples=[];review=[];sensitivity=[];stability=[];models_by_dataset={}
    for dataset,title in DATASETS.items():
        folder=OUT/dataset;folder.mkdir(exist_ok=True)
        problem_ids,tax_ids,x_all=read_matrix(dataset)
        supports_all=x_all.sum(axis=0)
        active=np.flatnonzero(supports_all)
        original_x=x_all[:,active]
        overlap=original_x.T.astype(np.int64)@original_x.astype(np.int64)
        isolated=(overlap.sum(axis=1)-np.diag(overlap))==0
        eligible=active[~isolated]
        ids=[tax_ids[i] for i in eligible];support=supports_all[eligible];x=x_all[:,eligible]
        assert len(ids)>max(DIMS)
        excluded=[]
        for j in range(len(tax_ids)):
            reason='unused_no_assignments' if supports_all[j]==0 else ('no_cooccurrence_with_any_other_tag' if j in set(active[isolated]) else None)
            if reason:excluded.append(dict(tag_id=tax_ids[j],tag=names[tax_ids[j]],problem_count=int(supports_all[j]),reason=reason))
        write_csv(folder/'excluded_tags.csv',excluded)
        a=x.T.astype(float)/np.sqrt(support)[:,None]
        with threadpool_limits(limits=1):u,s,vh=svd(a,full_matrices=False,lapack_driver='gesdd')
        np.testing.assert_allclose((u*s)@vh,a,atol=1e-12)
        original_cosine=cosine_matrix(a)
        np.testing.assert_allclose(cosine_matrix(u*s),original_cosine,atol=1e-12)
        models={'jaccard':{'d':squareform(pdist(x.T.astype(bool),metric='jaccard')),'energy':None},'raw_cosine':{'d':original_cosine,'energy':1.0}}
        singular=[dict(component=i+1,singular_value=float(value),cumulative_squared_singular_energy=float(np.sum(s[:i+1]**2)/np.sum(s**2))) for i,value in enumerate(s)]
        write_csv(folder/'singular_values.csv',singular)
        for k in DIMS:
            vectors=u[:,:k]*s[:k]
            models['svd_'+str(k)]={'d':cosine_matrix(vectors),'energy':float(np.sum(s[:k]**2)/np.sum(s**2))}
            vf=folder/('svd_'+str(k));vf.mkdir(exist_ok=True)
            write_csv(vf/'tag_vectors.csv',[dict(tag_id=t,tag=names[t],problem_count=int(support[i]),**{'v'+str(j+1):float(vectors[i,j]) for j in range(k)}) for i,t in enumerate(ids)])
        dsummary={}
        for method,m in models.items():
            d=m['d'];condensed=squareform(d,checks=True)
            z=linkage(condensed,method='average',optimal_ordering=True);m['z']=z
            assert is_valid_linkage(z,throw=True) and np.all(np.diff(z[:,2])>=-1e-12)
            mf=folder/method;mf.mkdir(exist_ok=True)
            np.savetxt(mf/'linkage.csv',z,delimiter=',',header='left,right,distance,leaf_count',comments='')
            from scipy.cluster.hierarchy import cophenet
            coph=float(cophenet(z,condensed)[0])
            distances=dict(minimum=float(condensed.min()),q10=float(np.quantile(condensed,.1)),median=float(np.median(condensed)),q90=float(np.quantile(condensed,.9)),maximum=float(condensed.max()),distance_exactly_1_fraction=float(np.mean(np.abs(condensed-1)<1e-10)),distance_above_1_fraction=float(np.mean(condensed>1+1e-10)))
            local_sweep=[]
            for cut in CUTS:
                metrics,labels=partition_metrics(d,z,cut)
                row=dict(dataset=dataset,method=method,dimensions=int(method[4:]) if method.startswith('svd_') else '',compared_tags=len(ids),**metrics)
                local_sweep.append(row);all_sweep.append(row)
                if method=='svd_32' and cut in [.7,.8,.9]:
                    rows,groups=cluster_rows(labels,ids,names,support,x)
                    suffix=f'{cut:.1f}'
                    write_csv(mf/('cluster_members_cut_'+suffix+'.csv'),rows)
                    dump(mf/('clusters_cut_'+suffix+'.json'),{'cut':cut,'method':method,'compared_tags':len(ids),'excluded_active_tags':[tax_ids[j] for j in active[isolated]],'clusters':groups})
                    draw_tree(z,[t+' '+names[t]+' (n='+str(int(support[i]))+')' for i,t in enumerate(ids)],f'{title}：SVD 32次元 / cut={cut:.1f}\n{len(ids)}タグ → {metrics["clusters"]}クラスタ（共起なしの1タグは別枠）',cut,mf/('dendrogram_cut_'+suffix))
            assert local_sweep[-1]['clusters']==1
            write_csv(mf/'cut_sweep.csv',local_sweep)
            dsummary[method]={'squared_singular_energy_retained':m['energy'],'cophenetic_correlation_in_own_distance_space':coph,'distance_distribution':distances,'cut_0.7':next(r for r in local_sweep if r['cut']==.7),'cut_0.8':next(r for r in local_sweep if r['cut']==.8),'cut_0.9':next(r for r in local_sweep if r['cut']==.9)}
        # Compare memberships at the Jaccard cut=0.9 cluster count, without asserting thresholds are equivalent.
        target=partition_metrics(models['jaccard']['d'],models['jaccard']['z'],.9)[0]['clusters']
        matched=[]
        for method,m in models.items():
            cut,count=best_count_cut(m['z'],target);metrics,labels=partition_metrics(m['d'],m['z'],cut)
            m['matched_labels']=labels
            matched.append(dict(dataset=dataset,method=method,target_clusters=target,actual_clusters=count,exact_count_match=count==target,cut=cut,silhouette_in_own_space=metrics['silhouette']))
        write_csv(folder/'matched_cluster_counts.csv',matched)
        # All tag pairs, including directly non-overlapping pairs, for transparent comparison.
        pairrows=[];co=x.T.astype(np.int64)@x.astype(np.int64)
        index={t:i for i,t in enumerate(ids)}
        for i in range(len(ids)):
            for j in range(i+1,len(ids)):
                pairrows.append(dict(tag_a_id=ids[i],tag_a=names[ids[i]],tag_b_id=ids[j],tag_b=names[ids[j]],support_a=int(support[i]),support_b=int(support[j]),shared_problems=int(co[i,j]),**{method+'_distance':float(m['d'][i,j]) for method,m in models.items()}))
        write_csv(folder/'pair_distances.csv',pairrows)
        nearest=[]
        for method,m in models.items():
            nn=top_neighbors(m['d'],ids)
            for t,neighbors in nn.items():
                for rank,n in enumerate(neighbors,1):nearest.append(dict(method=method,tag_id=t,tag=names[t],rank=rank,neighbor_tag_id=n,neighbor_tag=names[n],distance=float(m['d'][index[t],index[n]]),shared_problems=int(co[index[t],index[n]])))
        write_csv(folder/'nearest_neighbors.csv',nearest)
        candidates=sorted((r for r in pairrows if r['shared_problems']==0),key=lambda r:(r['svd_32_distance'],r['tag_a_id'],r['tag_b_id']))[:30]
        write_csv(folder/'newly_close_without_overlap.csv',candidates)
        for a_id,b_id,note in EXAMPLES:
            if a_id not in index or b_id not in index:continue
            i,j=index[a_id],index[b_id]
            examples.append(dict(dataset=dataset,comparison_note=note,tag_a_id=a_id,tag_a=names[a_id],tag_b_id=b_id,tag_b=names[b_id],shared_problems=int(co[i,j]),**{method+'_distance':float(m['d'][i,j]) for method,m in models.items()},jaccard_same_at_matched_count=bool(models['jaccard']['matched_labels'][i]==models['jaccard']['matched_labels'][j]),svd32_same_at_matched_count=bool(models['svd_32']['matched_labels'][i]==models['svd_32']['matched_labels'][j])))
        for r in candidates[:15]:review.append(dict(dataset=dataset,selection_reason='SVD32で近くなった共通問題なしの組',tag_a=r['tag_a'],tag_b=r['tag_b'],shared_problems=0,svd32_distance=r['svd_32_distance'],human_relation='',human_merge_as_learning_unit='',reviewer='',notes=''))
        for k in DIMS:
            m=models['svd_'+str(k)];tri=np.triu_indices(len(ids),1)
            sensitivity.append(dict(dataset=dataset,dimensions=k,energy_retained=m['energy'],distance_spearman_vs_32=float(spearmanr(m['d'][tri],models['svd_32']['d'][tri]).statistic),ari_vs_32_at_cut_0_7=float(adjusted_rand_score(fcluster(m['z'],.7,criterion='distance'),fcluster(models['svd_32']['z'],.7,criterion='distance')))))
        summary['datasets'][dataset]={'problems':len(problem_ids),'original_active_tags':len(active),'compared_tags':len(ids),'isolated_active_tags':[{'tag_id':tax_ids[j],'tag':names[tax_ids[j]],'problem_count':int(supports_all[j])} for j in active[isolated]],'unused_tags':int((supports_all==0).sum()),'original_jaccard_reference':original_summary['datasets'][dataset],'models':dsummary,'matched_comparison_target_clusters':target,'full_rank_cosine_reconstruction_max_error':float(np.max(np.abs(cosine_matrix(u*s)-original_cosine)))}
        # Small, reproducible perturbation check. Same original tag embeddings, compare only tags still observed.
        ref_nn={method:top_neighbors(m['d'],ids) for method,m in models.items() if method in ['jaccard','raw_cosine','svd_32']}
        for seed in range(5):
            rng=np.random.default_rng(seed);take=np.sort(rng.choice(len(x),round(len(x)*.8),replace=False));sx=x[take];present=sx.sum(axis=0)>0;pi=np.flatnonzero(present);pids=[ids[i] for i in pi];sx=sx[:,pi]
            if len(pi)<=32:continue
            sa=sx.T.astype(float)/np.sqrt(sx.sum(axis=0))[:,None]
            with threadpool_limits(limits=1):su,ss,svh=svd(sa,full_matrices=False,lapack_driver='gesdd')
            vectors=su[:,:32]*ss[:32];norms=np.linalg.norm(vectors,axis=1);valid=norms>1e-10
            pi=pi[valid];pids=[ids[i] for i in pi];sx=sx[:,valid];sa=sa[valid];vectors=vectors[valid]
            sample_d={'jaccard':squareform(pdist(sx.T.astype(bool),metric='jaccard')),'raw_cosine':cosine_matrix(sa),'svd_32':cosine_matrix(vectors)}
            for method,sd in sample_d.items():
                original=models[method]['d'][np.ix_(pi,pi)];old_nn=top_neighbors(original,pids);new_nn=top_neighbors(sd,pids);tri=np.triu_indices(len(pids),1)
                overlap5=float(np.mean([len(set(old_nn[t])&set(new_nn[t]))/5 for t in pids]));corr=float(spearmanr(original[tri],sd[tri]).statistic)
                stability.append(dict(dataset=dataset,method=method,seed=seed,problem_fraction=.8,retained_tags=len(pids),nearest_neighbor_overlap_at_5=overlap5,pair_distance_spearman=corr))
        models_by_dataset[dataset]=models
        print(dataset+': computation complete',flush=True)
    write_csv(OUT/'parameter_sweep.csv',all_sweep)
    write_csv(OUT/'example_pairs.csv',examples)
    write_csv(OUT/'review_pairs.csv',review)
    write_csv(OUT/'dimension_sensitivity.csv',sensitivity)
    write_csv(OUT/'subsample_stability.csv',stability)
    assert before=={str(p.relative_to(ROOT)):sha(p) for p in protected}
    summary['checks']=['source_hashes_unchanged','binary_matrix_and_unique_problem_ids','exact_svd_reconstruction','full_rank_cosine_equals_raw_cosine','no_zero_norm_cosine','valid_monotonic_linkage','cut_2_single_cluster','isolated_tags_listed_separately']
    dump(OUT/'summary.json',summary)
    render_comparison()
    print(json.dumps({'out':str(OUT),'checks':summary['checks'],'main_results':{d:summary['datasets'][d]['models']['svd_32'] for d in DATASETS}},ensure_ascii=False,indent=2),flush=True)


def render_comparison():
    """Render the summary from saved values, displaying the whole cosine range."""
    colors={'jaccard':'#677485','raw_cosine':'#d18c2e','svd_8':'#b04c54','svd_16':'#8970b4','svd_32':'#287ea5','svd_64':'#49a17f'}
    fonts={f.name for f in font_manager.fontManager.ttflist}
    font=next((n for n in ['Meiryo','Yu Gothic','MS Gothic'] if n in fonts),'DejaVu Sans')
    matplotlib.rcParams.update({'font.family':[font,'DejaVu Sans'],'axes.unicode_minus':False,'svg.fonttype':'none'})
    fig,axes=plt.subplots(2,2,figsize=(13,8))
    with (OUT/'parameter_sweep.csv').open(encoding='utf-8-sig',newline='') as f:sweep=list(csv.DictReader(f))
    for col,(dataset,title) in enumerate(DATASETS.items()):
        with (OUT/dataset/'pair_distances.csv').open(encoding='utf-8-sig',newline='') as f:pairs=list(csv.DictReader(f))
        for method,color in colors.items():
            values=[float(r[method+'_distance']) for r in pairs]
            axes[0,col].hist(values,bins=np.linspace(0,2,81),histtype='step',label=method,color=color,lw=1.3)
            rows=[r for r in sweep if r['dataset']==dataset and r['method']==method and float(r['cut'])<=1.1]
            axes[1,col].plot([float(r['cut']) for r in rows],[int(r['clusters']) for r in rows],label=method,color=color,marker='.',ms=4)
        axes[0,col].set_title(title+'：タグ間距離の分布');axes[0,col].set_xlabel('距離（コサイン距離の全範囲0〜2）');axes[0,col].set_ylabel('タグの組み合わせ数')
        axes[1,col].set_title(title+'：cutによるクラスタ数の変化');axes[1,col].set_xlabel('distance cut（手法間で同じ意味ではない）');axes[1,col].set_ylabel('クラスタ数')
        for ax in axes[:,col]:ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('固定された同じタグ集合で比較：Jaccard・元のコサイン・SVD後のコサイン',fontsize=14)
    fig.tight_layout(rect=(0,0,1,.95))
    for ext in ('png','svg'):fig.savefig(OUT/('comparison.'+ext),dpi=160)
    plt.close(fig)


def render_dendrograms():
    """Change only saved figure layouts, preserving every numerical result."""
    numeric_files=[p for p in OUT.rglob('*') if p.is_file() and p.suffix in ('.csv','.json') and p.name!='layout_verification.json']
    before={str(p.relative_to(OUT)):sha(p) for p in numeric_files}
    summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    fonts={f.name for f in font_manager.fontManager.ttflist}
    font=next((n for n in ['Meiryo','Yu Gothic','MS Gothic'] if n in fonts),'DejaVu Sans')
    matplotlib.rcParams.update({'font.family':[font,'DejaVu Sans'],'axes.unicode_minus':False,'svg.fonttype':'none'})
    figures=[]
    for dataset,title in DATASETS.items():
        folder=OUT/dataset/'svd_32'
        with (folder/'tag_vectors.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        labels=[r['tag_id']+' '+r['tag']+' (n='+r['problem_count']+')' for r in rows]
        z=np.loadtxt(folder/'linkage.csv',delimiter=',',skiprows=1)
        for cut in (.7,.8,.9):
            count=summary['datasets'][dataset]['models']['svd_32']['cut_'+str(cut)]['clusters']
            prefix=folder/('dendrogram_cut_'+str(cut))
            draw_tree(z,labels,f'{title}：SVD 32次元 / cut={cut:.1f}\n{len(labels)}タグ → {count}クラスタ（共起なしの1タグは別枠）',cut,prefix)
            figures.append(str(prefix.relative_to(OUT)))
        print(dataset+': labels moved to the left',flush=True)
    assert before=={str(p.relative_to(OUT)):sha(p) for p in numeric_files}
    dump(OUT/'layout_verification.json',{'labels':'left','root_direction':'right','distance_axis':'0 on left; increases to right','leaf_order_unchanged':True,'numeric_files_unchanged':True,'numeric_sha256':before,'figures':figures})

if __name__=='__main__':main()
