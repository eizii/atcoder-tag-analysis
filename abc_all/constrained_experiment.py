# -*- coding: utf-8 -*-
"""Hard pair constraints + ordinary average linkage; explicit, incomplete forests.
No text embeddings, annotation changes, paid APIs, or app updates.
"""
import argparse,csv,hashlib,json,zipfile,sys
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import fcluster
from sklearn.metrics import silhouette_samples,adjusted_rand_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nmf_experiment import read_csv,write_csv,dump,setup_font
from svd_experiment import read_matrix,cluster_rows,EXAMPLES

ROOT=Path(__file__).resolve().parent
PRIOR=ROOT/'nmf_experiment_20261119'
DEFAULT=ROOT/'constrained_experiment_20261119'
DATASETS={'all_difficulties':'全難易度','under_2000':'2000未満'}
METHODS={'jaccard':'Jaccard','svd_32':'SVD 32次元','nmf_32':'NMF 32成分'}
CUTS=[i/10 for i in range(11)]

class UnionFind:
    def __init__(self,n):self.p=list(range(n))
    def find(self,i):
        while self.p[i]!=i:self.p[i]=self.p[self.p[i]];i=self.p[i]
        return i
    def union(self,i,j):
        a,b=self.find(i),self.find(j)
        if a!=b:self.p[max(a,b)]=min(a,b)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def parse_constraints(rows,ids):
    idx={t:i for i,t in enumerate(ids)};active=[];skipped=[];seen=set()
    for row in rows:
        if row['enabled'].strip().lower() not in ['true','false','1','0']:raise ValueError('enabled must be true/false: '+str(row))
        if row['enabled'].strip().lower() in ['false','0']:continue
        kind=row['relation'].strip();a,b=row['tag_a_id'].strip(),row['tag_b_id'].strip()
        if kind not in ['must_link','cannot_link']:raise ValueError('Unknown constraint relation: '+kind)
        if a==b:raise ValueError('A pair must contain two different tags: '+a)
        key=(kind,*sorted([a,b]))
        if key in seen:raise ValueError('Duplicate constraint: '+str(key))
        seen.add(key)
        if a not in idx or b not in idx:skipped.append(dict(row,skip_reason='tag outside this comparison set'));continue
        active.append(dict(row,a=idx[a],b=idx[b]))
    uf=UnionFind(len(ids))
    for r in active:
        if r['relation']=='must_link':uf.union(r['a'],r['b'])
    for r in active:
        if r['relation']=='cannot_link' and uf.find(r['a'])==uf.find(r['b']):raise ValueError('Cannot-link conflicts with must-link transitive closure: '+r['constraint_id'])
    return active,skipped

def average_forest(d,ids,constraints):
    """Global closest admissible merge; UPGMA weighted by original tag counts.
    Must-link components are contracted at height zero (a convention, not distance).
    Cannot-link is hereditary: a forbidden original pair blocks every ancestor merge.
    Return only real/forced merges, with no fabricated common root.
    """
    n=len(ids);d=np.asarray(d,dtype=float)
    if d.shape!=(n,n) or not np.isfinite(d).all() or np.min(d)<0:raise ValueError('Invalid distance matrix')
    np.testing.assert_allclose(d,d.T,atol=1e-12);np.testing.assert_allclose(np.diag(d),0,atol=1e-12)
    uf=UnionFind(n)
    for r in constraints:
        if r['relation']=='must_link':uf.union(r['a'],r['b'])
    cl=[(r['a'],r['b']) for r in constraints if r['relation']=='cannot_link']
    if any(uf.find(a)==uf.find(b) for a,b in cl):raise ValueError('Contradictory ML/CL closure')
    cap=2*n-1;dist=np.full((cap,cap),np.inf);dist[:n,:n]=d
    blocked=np.zeros((cap,cap),dtype=bool)
    for a,b in cl:blocked[a,b]=blocked[b,a]=True
    active=set(range(n));members={i:[i] for i in active};rows=[]
    def merge(a,b,height,forced):
        c=n+len(rows);size_a,size_b=len(members[a]),len(members[b])
        raw=float(dist[a,b]);members[c]=members[a]+members[b]
        for t in active-{a,b}:
            dist[c,t]=dist[t,c]=(size_a*dist[a,t]+size_b*dist[b,t])/(size_a+size_b)
            blocked[c,t]=blocked[t,c]=blocked[a,t] or blocked[b,t]
        active.remove(a);active.remove(b);active.add(c)
        rows.append(dict(node_id=c,left=a,right=b,distance=float(height),leaf_count=size_a+size_b,forced_must_link=bool(forced),original_average_distance=raw))
        return c
    components={}
    for i in range(n):components.setdefault(uf.find(i),[]).append(i)
    for group in components.values():
        cur=group[0]
        for other in group[1:]:cur=merge(cur,other,0.0,True)
    while len(active)>1:
        nodes=np.array(sorted(active));sub=dist[np.ix_(nodes,nodes)].copy()
        sub[blocked[np.ix_(nodes,nodes)]]=np.inf
        sub[np.tril_indices(len(nodes))]=np.inf
        i,j=np.unravel_index(np.argmin(sub),sub.shape);height=float(sub[i,j])
        if not np.isfinite(height):break
        merge(int(nodes[i]),int(nodes[j]),height,False)
    if len(rows)>1 and np.min(np.diff([r['distance'] for r in rows])) < -1e-10:raise AssertionError('Nonmonotone heights')
    return dict(n_tags=n,merges=rows,roots=sorted(active,key=lambda t:min(members[t])),root_members={str(t):members[t] for t in active},tie_breaking='lexicographic node IDs among minimum admissible mean distances')

def partition(forest,cut):
    n=forest['n_tags'];uf=UnionFind(n);rep={i:i for i in range(n)}
    for r in forest['merges']:
        a,b=rep[r['left']],rep[r['right']];rep[r['node_id']]=a
        if r['distance']<=cut:uf.union(a,b)
    labels=np.array([uf.find(i) for i in range(n)])
    return np.array([sorted(set(labels)).index(v)+1 for v in labels])

def metrics(d,labels):
    counts=Counter(labels);k=len(counts)
    values=silhouette_samples(d,labels,metric='precomputed') if 1<k<len(labels) else None
    return dict(clusters=k,singleton_clusters=sum(v==1 for v in counts.values()),largest_cluster_tags=max(counts.values()),silhouette=float(values.mean()) if values is not None else None)

def violations(labels,constraints):
    return sum((labels[r['a']]!=labels[r['b']]) if r['relation']=='must_link' else (labels[r['a']]==labels[r['b']]) for r in constraints)

def pair_labels(labels,ids):return {t:set(ids[j] for j in np.flatnonzero(labels==labels[i])) for i,t in enumerate(ids)}

def draw_forest(forest,ids,names,support,labels,cut,title,prefix):
    n=len(ids);rows={r['node_id']:r for r in forest['merges']}
    def leaves(t):
        if t<n:return [t]
        r=rows[t];return leaves(r['left'])+leaves(r['right'])
    order=[]
    for t in forest['roots']:order.extend(leaves(t))
    assert len(order)==n and len(set(order))==n
    pos={t:float(i) for i,t in enumerate(reversed(order))};height={t:0.0 for t in range(n)}
    node_group={t:int(labels[t]) for t in range(n)}
    fig,ax=plt.subplots(figsize=(19,max(18,n*.20)))
    cmap=plt.get_cmap('tab20');segments=[]
    for r in forest['merges']:
        t,a,b=r['node_id'],r['left'],r['right'];h=r['distance'];pos[t]=(pos[a]+pos[b])/2;height[t]=h
        group=node_group[a] if node_group[a]==node_group[b] else -1;node_group[t]=group
        color=cmap((group-1)%20) if group>0 and h<=cut else '#7b818b'
        ax.plot([height[a],h,h,height[b]],[pos[a],pos[a],pos[b],pos[b]],color=color,lw=1.05)
        segments.append(dict(node=t,left=a,right=b,distance=h))
    for t in forest['roots']:ax.scatter([height[t]],[pos[t]],s=18,color='#374151',zorder=5)
    ticks=sorted(range(n),key=lambda i:pos[i]);ax.set_yticks([pos[i] for i in ticks]);ax.set_yticklabels([f'{ids[i]} {names[ids[i]]} (n={support[i]})' for i in ticks],fontsize=9)
    ax.yaxis.set_ticks_position('left');ax.tick_params(axis='y',length=2,pad=4,labelleft=True,labelright=False)
    assert ax.yaxis.get_ticks_position()=='left'
    xmax=max(1.03,max([r['distance'] for r in forest['merges']]+[0])+.03);ax.set_xlim(-.003,xmax);ax.set_ylim(-1,n)
    ax.axvline(cut,color='#bb263e',ls='--',lw=1.2);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    ax.set_xlabel('元の距離に対する平均連結法（結合禁止を全階層で維持）')
    ax.set_title(title+f' / cut={cut:.1f}\n{n}タグ → {len(set(labels))}群、最終的な木は{len(forest["roots"])}本（文字列処理1タグは別枠）',fontsize=14,pad=16)
    fig.text(.025,.012,'黒点は各木の根。木と木の間を結ぶ架空の枝は描いていません。タグ名は左側。n=タグの問題数。\n枝色はcutで分けた群の目印で、分野ではありません。制約は少数の仮説であり、分類の正解ラベルではありません。',fontsize=9)
    fig.tight_layout(rect=(.01,.042,.995,.995))
    for ext in ['png','svg']:fig.savefig(str(prefix)+'.'+ext,dpi=140,facecolor='white')
    plt.close(fig)
    return dict(labels='left',tags_displayed=n,unique_leaf_count=len(set(order)),real_merges_drawn=len(segments),roots_drawn=len(forest['roots']),fake_root_edges=0)

def compute(out,constraints_path):
    out.mkdir(parents=True,exist_ok=True);constraint_rows=read_csv(constraints_path)
    taxonomy=json.loads((ROOT/'taxonomy.json').read_text(encoding='utf-8'));names={r['tag_id']:r['tag'] for r in taxonomy}
    for r in constraint_rows:
        for key in ['tag_a_id','tag_b_id']:
            if r[key] not in names:raise ValueError('Unknown taxonomy ID: '+r[key])
    protected=[ROOT/'taxonomy.json',constraints_path]
    protected.extend(p for folder in [PRIOR,ROOT/'svd_experiment_20261112',ROOT/'comparison_20261105'] for p in folder.rglob('*') if p.is_file())
    before={str(p.relative_to(ROOT)):sha(p) for p in protected if p.is_relative_to(ROOT)}
    write_csv(out/'constraints_used.csv',constraint_rows)
    summary=dict(created='2026-11-19',snapshot='2026-11-05',paid_api_calls=0,source_sha256=before,script_sha256=sha(Path(__file__)),constraints_sha256=sha(constraints_path),protocol='hard global cannot-link; initial must-link closure contracted at height zero; UPGMA with original tag counts; admissible greedy closest-pair merge; deterministic ties; stop as a forest',constraints_status='provisional_assistant unless edited by the user; no independent human evaluation',main_cut=.7,cophenetic_correlation=None,cophenetic_note='Not computed: across-root cophenetic distances are undefined; never impute fake root distances.',datasets={})
    setup_font();sweep=[];audits=[];diag=[];changes=[];layouts=[];remaining=[]
    for ds,title in DATASETS.items():
        folder=out/ds;folder.mkdir(exist_ok=True)
        vr=read_csv(PRIOR/ds/'nmf_32/tag_vectors.csv');ids=[r['tag_id'] for r in vr];support=np.array([int(r['problem_count']) for r in vr]);index={t:i for i,t in enumerate(ids)}
        pids,allids,xall=read_matrix(ds);x=xall[:,[allids.index(t) for t in ids]]
        np.testing.assert_array_equal(support,x.sum(axis=0))
        active,skipped=parse_constraints(constraint_rows,ids)
        write_csv(folder/'constraints_applied.csv',[{k:v for k,v in r.items() if k not in ['a','b']} for r in active],fields=list(constraint_rows[0]) if constraint_rows else ['constraint_id','relation','tag_a_id','tag_b_id','enabled'])
        if skipped:write_csv(folder/'constraints_skipped.csv',skipped)
        dsets={key:np.zeros((len(ids),len(ids))) for key in METHODS}
        pairs=read_csv(PRIOR/ds/'pair_distances.csv')
        for r in pairs:
            a,b=index[r['tag_a_id']],index[r['tag_b_id']]
            for method,d in dsets.items():d[a,b]=d[b,a]=float(r[method+'_distance'])
        dataset_summary=dict(problems=len(pids),compared_tags=len(ids),separate_tags=['T073'],active_constraints=len(active),skipped_constraints=len(skipped),models={})
        specified={(min(r['a'],r['b']),max(r['a'],r['b'])) for r in active}
        for method,d in dsets.items():
            mf=folder/method;mf.mkdir(exist_ok=True)
            forests={'unconstrained':average_forest(d,ids,[]),'constrained':average_forest(d,ids,active)}
            model_summary={}
            for variant,forest in forests.items():
                dump(mf/(variant+'_forest.json'),forest)
                write_csv(mf/(variant+'_merges.csv'),forest['merges'])
                for cut in CUTS:
                    lab=partition(forest,cut);base=partition(forests['unconstrained'],cut)
                    row=dict(dataset=ds,method=method,variant=variant,cut=cut,**metrics(d,lab),constraint_violations=violations(lab,active),final_forest_roots=len(forest['roots']),ari_to_unconstrained=float(adjusted_rand_score(base,lab)))
                    sweep.append(row)
                    if cut in [.7,.8,.9]:
                        flat,groups=cluster_rows(lab,ids,names,support,x)
                        write_csv(mf/(variant+'_members_cut_'+str(cut)+'.csv'),flat)
                        dump(mf/(variant+'_clusters_cut_'+str(cut)+'.json'),dict(cut=cut,groups=groups))
                        md=['# '+title+' / '+METHODS[method]+' / '+variant+f' / cut={cut}','',f'{len(groups)}群。文字列処理1タグは別枠。制約は独立した正解データではありません。','']
                        for g in groups:md.extend(['- **'+g['cluster_id']+'**（'+str(g['problem_count'])+'問）：'+'、'.join(g['tags'])])
                        (mf/(variant+'_clusters_cut_'+str(cut)+'.md')).write_text('\n'.join(md)+'\n',encoding='utf-8')
                lab=partition(forest,.7)
                model_summary[variant]=dict(roots=len(forest['roots']),cut_0_7=metrics(d,lab))
                if variant=='constrained':
                    for cut in [.7,.8,.9]:
                        info=draw_forest(forest,ids,names,support,partition(forest,cut),cut,title+'：'+METHODS[method]+' / 制約あり',mf/('constrained_cut_'+str(cut)))
                        layouts.append(dict(dataset=ds,method=method,cut=cut,**info))
            old=np.loadtxt(PRIOR/ds/method/'linkage.csv',delimiter=',',skiprows=1)
            model_summary['ari_baseline_to_previous_at_0_7']=float(adjusted_rand_score(partition(forests['unconstrained'],.7),fcluster(old,.7,criterion='distance')))
            dataset_summary['models'][method]=model_summary
            for cut in [.7,.8,.9]:
                base,lab=[partition(forests[v],cut) for v in ['unconstrained','constrained']]
                oldgroups,newgroups=pair_labels(base,ids),pair_labels(lab,ids)
                for i,t in enumerate(ids):
                    if oldgroups[t]!=newgroups[t]:changes.append(dict(dataset=ds,method=method,cut=cut,tag_id=t,tag=names[t],old_group=';'.join(sorted(oldgroups[t])),new_group=';'.join(sorted(newgroups[t]))))
                for r in active:audits.append(dict(dataset=ds,method=method,cut=cut,constraint_id=r['constraint_id'],relation=r['relation'],tag_a=names[ids[r['a']]],tag_b=names[ids[r['b']]],original_distance=float(d[r['a'],r['b']]),same_before=bool(base[r['a']]==base[r['b']]),same_after=bool(lab[r['a']]==lab[r['b']]),status=r['status']))
                for a,b,note in EXAMPLES:
                    if a in index and b in index:diag.append(dict(dataset=ds,method=method,cut=cut,tag_a_id=a,tag_a=names[a],tag_b_id=b,tag_b=names[b],note=note,same_before=bool(base[index[a]]==base[index[b]]),same_after=bool(lab[index[a]]==lab[index[b]]),independent_human_label=''))
            # Review candidates exclude all directly constrained pairs. No semantic label is inferred.
            base,lab=[partition(forests[v],.7) for v in ['unconstrained','constrained']]
            cand=[(d[i,j],i,j) for i in range(len(ids)) for j in range(i+1,len(ids)) if lab[i]==lab[j] and (i,j) not in specified]
            for distance,i,j in sorted(cand)[:30]:remaining.append(dict(dataset=ds,method=method,cut=.7,tag_a_id=ids[i],tag_a=names[ids[i]],tag_b_id=ids[j],tag_b=names[ids[j]],distance=float(distance),same_before=bool(base[i]==base[j]),human_should_share_learning_unit='',human_reason='',review_status='not_reviewed'))
            print(ds+' / '+method+': '+str(model_summary),flush=True)
        summary['datasets'][ds]=dataset_summary
    write_csv(out/'cut_sweep.csv',sweep);write_csv(out/'constraint_audit.csv',audits);write_csv(out/'tag_membership_changes.csv',changes)
    write_csv(out/'unconstrained_diagnostic_pairs.csv',diag);write_csv(out/'review_candidates.csv',remaining)
    dump(out/'layout_verification.json',layouts)
    after={name:sha(ROOT/name) for name in before};assert before==after
    summary['source_files_unchanged']=True;dump(out/'summary.json',summary)
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=DEFAULT);parser.add_argument('--constraints',type=Path,default=DEFAULT/'constraints.csv');args=parser.parse_args()
    compute(args.out,args.constraints)
