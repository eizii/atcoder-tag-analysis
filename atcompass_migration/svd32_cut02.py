# -*- coding: utf-8 -*-
"""Stage/apply the frozen SVD32 under-2000 cut .2 dataset to AtCompass."""
import argparse,csv,hashlib,io,json
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.cluster.hierarchy import fcluster
ROOT=Path(__file__).resolve().parent
APP=Path('C:/Users/ejham/theme2026-kaziru')
OUT=ROOT/'svd32_under2000_cut02'
SOURCE=ROOT.parent/'abc_all/comparison_20261105/under_2000'
SVD=ROOT.parent/'abc_all/svd_experiment_20261112/under_2000/svd_32'
VERSION='svd32-under2000-average-d0.2-20261119'
CUT=.2
FIELDS=['tag','problem_id','title','difficulty','diff_band','url']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csv_bytes(rows,fields):
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows);return s.getvalue().encode('utf-8')
def stage():
    OUT.mkdir(exist_ok=True)
    if (OUT/'manifest.json').exists():raise RuntimeError('Already staged: preserve the current backup rather than overwrite it.')
    problems=read_csv(SOURCE/'problems.csv');matrix=read_csv(SOURCE/'problem_tag_matrix.csv');vectors=read_csv(SVD/'tag_vectors.csv')
    ids=[r['tag_id'] for r in vectors];names={r['tag_id']:r['tag'] for r in json.loads((ROOT.parent/'abc_all/taxonomy.json').read_text(encoding='utf-8'))}
    support={r['tag_id']:int(r['problem_count']) for r in vectors}
    z=np.loadtxt(SVD/'linkage.csv',delimiter=',',skiprows=1);labels=fcluster(z,CUT,criterion='distance')
    grouped={}
    for tid,lab in zip(ids,labels):grouped.setdefault(int(lab),[]).append(tid)
    groups=sorted(grouped.values(),key=lambda g:min(g));assert len(groups)==86 and len(ids)==138
    active=[t for t in matrix[0] if t!='problem_id' and any(int(r[t]) for r in matrix)]
    assert set(active)-set(ids)=={'T073'}
    groups.append(['T073']);support['T073']=sum(int(r['T073']) for r in matrix)
    assert len(problems)==len(matrix)==2473
    by_id={r['problem_id']:r for r in problems};matrix_by_id={r['problem_id']:r for r in matrix}
    assert len(by_id)==len(matrix_by_id)==2473 and set(by_id)==set(matrix_by_id)
    catalog_groups=[];mapping={};assignments=[];unassigned=[]
    for serial,members in enumerate(groups,1):
        representative=sorted(members,key=lambda t:(-support[t],t))[0];name=names[representative]
        label=f'C{serial:03d}: '+name+(f' ほか{len(members)-1}タグ' if len(members)>1 else '')
        pids=sorted(pid for pid,row in matrix_by_id.items() if any(int(row[t]) for t in members))
        group=dict(cluster_id='SVD32_'+min(members),label=label,representative=name,member_tags=[dict(tag_id=t,tag=names[t]) for t in members],detail_methods=[names[t] for t in members],algorithm_count=len(members),problem_count=len(pids),visible=True,separate_from_svd=members==['T073'],description='この群のいずれかのタグが付いた問題です。')
        catalog_groups.append(group)
        for tid in members:mapping[tid]=group
        for pid in pids:
            r=by_id[pid];difficulty=float(r['difficulty']);assert 0<=difficulty<2000
            band=int(difficulty//400)*400
            assignments.append(dict(tag=label,problem_id=pid,title=r['title'],difficulty=r['difficulty'],diff_band=f'{band}-{band+399}',url=r['url']))
    for pid,r in by_id.items():
        if not any(int(matrix_by_id[pid][t]) for t in active):unassigned.append(dict(problem_id=pid,title=r['title'],difficulty=r['difficulty'],url=r['url'],reason='no_supported_tag_in_frozen_annotation'))
    tagged_ids={r['problem_id'] for r in assignments};assert len(tagged_ids)==1693 and len(unassigned)==780
    assert len(set((r['tag'],r['problem_id']) for r in assignments))==len(assignments)
    assert set(tagged_ids).isdisjoint(r['problem_id'] for r in unassigned)
    assert sum(g['problem_count'] for g in catalog_groups)==len(assignments)
    data=csv_bytes(assignments,FIELDS)
    sources=[SOURCE/'problems.csv',SOURCE/'problem_tag_matrix.csv',SVD/'tag_vectors.csv',SVD/'linkage.csv',ROOT.parent/'abc_all/taxonomy.json']
    catalog=dict(version=VERSION,classification_method='svd_hierarchical_clustering',display_label='SVDによる分類',source_problem_count=len(tagged_ids),source_dataset_problem_count=2473,untagged_problem_count=780,source_fine_tag_count=len(active),compared_fine_tag_count=len(ids),svd_dimensions=32,distance='cosine',linkage='average',distance_threshold=CUT,clustered_group_count=86,separate_tag_count=1,display_min_problem_count=1,visible_cluster_count=87,independent_human_review=False,annotations_provisional=True,clusters=catalog_groups,problemCatalog='public/all_problems.csv',problemCatalogSha256=hashlib.sha256(data).hexdigest(),source_sha256={str(p.relative_to(ROOT.parent)):sha(p) for p in sources})
    main=(APP/'src/components/Main.jsx').read_text(encoding='utf-8')
    old='{tagCatalog.source_problem_count}問（学習単位）'
    assert main.count(old)==1
    main=main.replace(old,'{tagCatalog.source_problem_count}問（{tagCatalog.display_label ?? "学習単位"}）',1)
    docs=f'''# SVD32次元によるタグ分類

現在の表示は、2000未満の問題・SVD32次元・コサイン距離・平均連結法・distance cut=0.2です。
SVDの138タグを86群に分け、共起のない文字列処理1タグを別枠に加えた87分類を表示します。
1問だけの分類も表示します。これは制約付きクラスタリングではありません。

2026-11-05の固定データ2,473問のうち、タグが付与された1,693問を表示します。
未付与780問は未分類として記録し、推測でタグを付けたり円グラフの分母に混ぜたりしません。
以前の898問・82学習単位版から、問題データと分類の両方を更新しました。

public/all_problems.csvは従来と同じ6列です。
各群に含まれる元タグのいずれかが付いた問題を、その群に1回だけ対応づけます。
同じ問題が複数の元タグを持っていても、同じ群内では重複計上しません。
クラスタ内の全手法を各問題が使う意味ではなく、学習単位の粒度を保証するものでもありません。

カタログ版：{VERSION}
カタログ：src/data/tagCatalog.json

ノード選択時は、含まれる元タグと対応する問題一覧を確認できます。
個人のAC・WA・未挑戦は従来どおり問題IDに基づきます。
同レート帯データは版が一致するまで既存の互換性判定により表示しません。
既存の題材メタデータは保持し、根拠のない新しい題材を生成していません。

固定入力・全139タグの対応表・未付与問題・変更前バックアップは、分析用リポジトリの
atcompass_migration/svd32_under2000_cut02/に保存しています。
タグ付与の意味的正しさと分類の妥当性について、独立した人手評価は未実施です。
'''
    plans={'public/all_problems.csv':data,'src/data/tagCatalog.json':(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n').encode('utf-8'),'src/components/Main.jsx':main.encode('utf-8'),'docs/SVD_TAGS.md':docs.encode('utf-8')}
    for rel in ['docs/SEMANTIC_TAGS.md','docs/CLUSTER_TAGS.md']:
        olddoc=(APP/rel).read_text(encoding='utf-8')
        plans[rel]=('この文書は旧分類の記録です。現行の分類は [SVD32次元版](SVD_TAGS.md) を参照してください。\n\n---\n\n'+olddoc).encode('utf-8')
    manifest={}
    for rel,content in plans.items():
        current=(APP/rel).resolve();assert APP.resolve() in current.parents
        backup=OUT/'before'/rel;staged=OUT/'staged'/rel
        staged.parent.mkdir(parents=True,exist_ok=True);staged.write_bytes(content)
        if current.exists():backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(current.read_bytes());before=sha(current)
        else:before=None
        manifest[rel]=dict(before_sha256=before,staged_sha256=sha(staged))
    (OUT/'unassigned_problems.csv').write_bytes(csv_bytes(unassigned,['problem_id','title','difficulty','url','reason']))
    mapping_rows=[dict(tag_id=t,tag=names[t],cluster_id=g['cluster_id'],cluster_label=g['label'],tag_problem_count=support[t],cluster_problem_count=g['problem_count'],separate_from_svd=g['separate_from_svd']) for t,g in mapping.items()]
    (OUT/'tag_to_cluster.csv').write_bytes(csv_bytes(mapping_rows,list(mapping_rows[0])))
    dump(OUT/'manifest.json',manifest)
    summary=dict(version=VERSION,svd_components=32,distance_cut=.2,svd_cluster_count=86,total_display_tags=87,source_problems=2473,displayed_problems=1693,unassigned_problems=780,problem_cluster_pairs=len(assignments),display_single_problem_tags=True,files=list(plans),backups=str(OUT/'before'),source_sha256=catalog['source_sha256'])
    dump(OUT/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
def apply():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    for rel,info in manifest.items():
        target=(APP/rel).resolve();assert APP.resolve() in target.parents
        assert sha(OUT/'staged'/rel)==info['staged_sha256']
        if info['before_sha256'] is None:assert not target.exists(),rel
        else:assert sha(target)==info['before_sha256'] and sha(OUT/'before'/rel)==info['before_sha256'],rel
    for rel,info in manifest.items():
        target=APP/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((OUT/'staged'/rel).read_bytes());assert sha(target)==info['staged_sha256']
    dump(OUT/'applied.json',dict(version=VERSION,files=list(manifest),published=False));print('Applied '+VERSION)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
    apply() if args.apply else stage()
