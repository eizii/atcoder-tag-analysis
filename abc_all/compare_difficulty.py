"""Controlled difficulty comparison from ONE frozen annotation, and correction audit."""
import csv,hashlib,json,sys,zipfile
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist,squareform
from scipy.cluster.hierarchy import linkage,fcluster,dendrogram,cophenet
from sklearn.metrics import adjusted_rand_score,silhouette_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from collect_statements import ROOT,load_json,save_json
from tag_all import csv_write

OUT=ROOT/"comparison_20261105"
CUT=.7
def read_csv(p):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def native(x):
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)
def model(x,tids,ids):
    support=x.sum(axis=0)
    active=np.flatnonzero(support)
    a=x[:,active].T.astype(bool)
    d=pdist(a,metric="jaccard")
    z=linkage(d,method="average",optimal_ordering=True)
    labels=fcluster(z,CUT,criterion="distance")
    # Use stable membership IDs rather than comparing arbitrary scipy labels.
    groups=[]
    for n in sorted(set(labels)):
        idx=np.flatnonzero(labels==n)
        members=[tids[active[i]] for i in idx]
        problem_ids=[ids[i] for i in np.flatnonzero(x[:,[tids.index(t) for t in members]].any(axis=1))]
        groups.append(dict(cluster_id="C_"+min(members),tag_ids=members,problem_count=len(problem_ids),problem_ids=problem_ids))
    summary=dict(problem_count=len(ids),tagged_problem_count=int(x.any(axis=1).sum()),
        untagged_problem_count=int((~x.any(axis=1)).sum()),assigned_pairs=int(x.sum()),
        active_tags=len(active),unused_tags=len(tids)-len(active),
        tags_support_1=int((support==1).sum()),tags_support_2=int((support==2).sum()),
        tags_support_1_or_2=int(((support>=1)&(support<=2)).sum()),
        tags_support_at_least_3=int((support>=3).sum()),
        clusters=len(groups),visible_clusters=sum(g["problem_count"]>=2 for g in groups),
        singleton_tag_clusters=sum(len(g["tag_ids"])==1 for g in groups),
        multi_tag_clusters=sum(len(g["tag_ids"])>1 for g in groups),
        cophenetic_correlation=float(cophenet(z,d)[0]),
        silhouette=float(silhouette_score(squareform(d),labels,metric="precomputed")) if 1<len(set(labels))<len(active) else None)
    return dict(support=support,active=active,d=d,z=z,labels=labels,groups=groups,summary=summary)

def build():
    OUT.mkdir(exist_ok=True)
    protected=[ROOT.parent/"all_problems.csv",ROOT.parent/"tags.md",ROOT/"output/summary.json",ROOT/"output/problem_tag_matrix.csv",ROOT/"output/problems_tagged.jsonl"]
    protected_hashes={p:sha(p) for p in protected}
    rows=read_csv(ROOT/"output_v2_uniform/problems.csv")
    matrix=read_csv(ROOT/"output_v2_uniform/problem_tag_matrix.csv")
    taxonomy=load_json(ROOT/"taxonomy.json")
    tids=[t["tag_id"] for t in taxonomy];names={t["tag_id"]:t["tag"] for t in taxonomy}
    by={r["problem_id"]:r for r in rows}
    ids=[r["problem_id"] for r in matrix]
    x=np.array([[int(r[t]) for t in tids] for r in matrix],dtype=np.uint8)
    difficulty=np.array([float(by[pid]["difficulty"]) if by[pid]["difficulty"]!="" else np.nan for pid in ids])
    masks=dict(under_2000=difficulty<2000,all_known=np.isfinite(difficulty),all_difficulties=np.ones(len(ids),bool))
    titles=dict(under_2000="2000未満",all_known="全難易度（既知のみ）",all_difficulties="全難易度（不明含む）")
    models={}
    for key,mask in masks.items():
        subids=[pid for pid,include in zip(ids,mask) if include]
        m=model(x[mask],tids,subids);models[key]=m
        folder=OUT/key;folder.mkdir(exist_ok=True)
        csv_write(folder/"problems.csv",list(rows[0]),[by[pid] for pid in subids])
        csv_write(folder/"problem_tag_matrix.csv",["problem_id",*tids],[r for r,include in zip(matrix,mask) if include])
        flat=[]
        for g in m["groups"]:
            for tid in g["tag_ids"]:
                flat.append(dict(cluster_id=g["cluster_id"],tag_id=tid,tag=names[tid],tag_problem_count=int(m["support"][tids.index(tid)]),cluster_problem_count=g["problem_count"],visible=int(g["problem_count"]>=2)))
        csv_write(folder/"cluster_members.csv",["cluster_id","tag_id","tag","tag_problem_count","cluster_problem_count","visible"],flat)
        save_json(folder/"clusters.json",dict(cut=CUT,distance="jaccard",linkage="average",clusters=m["groups"]))
        np.savetxt(folder/"linkage.csv",m["z"],delimiter=",",header="left,right,distance,leaf_count",comments="")
    # Exact identity of tag vectors on every common problem, not separate annotation runs.
    lowrows=read_csv(OUT/"under_2000/problem_tag_matrix.csv")
    allrows={r["problem_id"]:r for r in read_csv(OUT/"all_difficulties/problem_tag_matrix.csv")}
    assert all(r==allrows[r["problem_id"]] for r in lowrows)
    assert len(lowrows)==2473 and len(ids)==3012 and int(np.isnan(difficulty).sum())==23
    common=sorted(set(models["under_2000"]["active"])&set(models["all_difficulties"]["active"]))
    low=model(x[masks["under_2000"]][:,common],[tids[i] for i in common],[pid for pid,b in zip(ids,masks["under_2000"]) if b])
    full=model(x[:,common],[tids[i] for i in common],ids)
    def restricted_labels(m):
        lookup=dict(zip(m["active"],m["labels"]))
        return [int(lookup[i]) for i in common]
    lo_labels=restricted_labels(models["under_2000"]);all_labels=restricted_labels(models["all_difficulties"])
    pair_changes=[];distance_changes=[]
    oldsame=set();newsame=set()
    for a in range(len(common)):
        for b in range(a+1,len(common)):
            t1,t2=tids[common[a]],tids[common[b]]
            if lo_labels[a]==lo_labels[b]:oldsame.add((t1,t2))
            if all_labels[a]==all_labels[b]:newsame.add((t1,t2))
    for pair in sorted(oldsame^newsame):
        pair_changes.append(dict(tag_id_1=pair[0],tag_1=names[pair[0]],tag_id_2=pair[1],tag_2=names[pair[1]],change="split" if pair in oldsame else "joined"))
    csv_write(OUT/"common_tag_cluster_changes.csv",["tag_id_1","tag_1","tag_id_2","tag_2","change"],pair_changes)
    dslo=squareform(low["d"]);dsfull=squareform(full["d"])
    for a in range(len(common)):
        for b in range(a+1,len(common)):
            distance_changes.append(dict(tag_id_1=tids[common[a]],tag_1=names[tids[common[a]]],tag_id_2=tids[common[b]],tag_2=names[tids[common[b]]],under_2000_distance=float(dslo[a,b]),all_distance=float(dsfull[a,b]),distance_change=float(dsfull[a,b]-dslo[a,b])))
    distance_changes.sort(key=lambda r:abs(r["distance_change"]),reverse=True)
    csv_write(OUT/"common_tag_distance_changes.csv",list(distance_changes[0]),distance_changes)
    stability=dict(common_tags=len(common),ari_restricting_complete_clusterings=float(adjusted_rand_score(lo_labels,all_labels)),
        ari_reclustering_only_common_tags=float(adjusted_rand_score(low["labels"],full["labels"])),
        co_clustered_pairs_under_2000=len(oldsame),co_clustered_pairs_all=len(newsame),
        co_clustered_pairs_retained=len(oldsame&newsame),pairs_split=len(oldsame-newsame),pairs_joined=len(newsame-oldsame),
        mean_absolute_jaccard_distance_change=float(np.abs(low["d"]-full["d"]).mean()))
    # Counts by tag, including absent tags, make lack of evidence explicit.
    tagrows=[]
    high=(difficulty>=2000)
    unknown=np.isnan(difficulty)
    for j,t in enumerate(tids):
        tagrows.append(dict(tag_id=t,tag=names[t],under_2000=int(x[masks["under_2000"],j].sum()),
            at_least_2000=int(x[high,j].sum()),unknown=int(x[unknown,j].sum()),all_difficulties=int(x[:,j].sum()),
            first_observed_above_2000=int(x[masks["under_2000"],j].sum()==0 and x[high,j].sum()>0)))
    csv_write(OUT/"tag_support_comparison.csv",list(tagrows[0]),tagrows)
    bandrows=[]
    for label,mask in [("2000未満",masks["under_2000"]),("2000以上",high),("難易度不明",unknown)]:
        inds=np.flatnonzero(mask)
        scoped_source_ids={r["problem_id"] for r in read_csv(ROOT/"output_v2_uniform/source_scope_audit.csv") if r["reason"]=="shared_unsegmented_editorial"}
        bandrows.append(dict(band=label,problem_count=len(inds),tagged_problem_count=int(x[mask].any(axis=1).sum()),
            tagged_rate=float(x[mask].any(axis=1).mean()),with_raw_editorial=sum(int(by[ids[i]]["editorial_count"])>0 for i in inds),
            affected_by_quarantined_source=sum(ids[i] in scoped_source_ids for i in inds)))
    csv_write(OUT/"band_coverage.csv",list(bandrows[0]),bandrows)
    # Equal sample size: composition changes while problem count is held at 2473.
    # Sampling without replacement, fixed published seeds; not a causal estimate.
    sample_rows=[]
    known_idx=np.flatnonzero(masks["all_known"])
    for seed in range(30):
        take=np.random.default_rng(seed).choice(known_idx,size=int(masks["under_2000"].sum()),replace=False)
        counts=x[take].sum(axis=0)
        sample_rows.append(dict(seed=seed,problem_count=len(take),high_difficulty_problems=int(high[take].sum()),
            active_tags=int((counts>0).sum()),tags_support_at_least_3=int((counts>=3).sum()),
            tags_support_1_or_2=int(((counts>=1)&(counts<=2)).sum())))
    csv_write(OUT/"equal_size_subsamples.csv",list(sample_rows[0]),sample_rows)
    equal_size={key:dict(mean=float(np.mean([r[key] for r in sample_rows])),minimum=min(r[key] for r in sample_rows),maximum=max(r[key] for r in sample_rows)) for key in ["active_tags","tags_support_at_least_3","tags_support_1_or_2","high_difficulty_problems"]}
    # Sensitivity at unchanged cut/policy with prior inherited tags and targeted reviews.
    hybrid=read_csv(ROOT/"output_v2/problem_tag_matrix.csv")
    hx=np.array([[int(r[t]) for t in tids] for r in hybrid],dtype=np.uint8)
    assert [r["problem_id"] for r in hybrid]==ids
    hybrid_summary={}
    for key in ["under_2000","all_difficulties"]:
        mask=masks[key]
        hybrid_summary[key]=model(hx[mask],tids,[pid for pid,include in zip(ids,mask) if include])["summary"]
    # Audit changes from prior HYBRID version to corrected HYBRID version.
    with (ROOT/"output/problems_tagged.jsonl").open(encoding="utf-8") as f: old={r["problem_id"]:r for r in map(json.loads,f)}
    with (ROOT/"output_v2/problems_tagged.jsonl").open(encoding="utf-8") as f: corrected={r["problem_id"]:r for r in map(json.loads,f)}
    audit=[];removed=added=0;changed=set()
    scopes=read_csv(ROOT/"output_v2/source_scope_audit.csv")
    for pid in ids:
        before=set(old[pid]["tag_ids"]);after=set(corrected[pid]["tag_ids"])
        for tid in sorted(before^after):
            change="removed" if tid in before else "added"
            removed+=change=="removed";added+=change=="added";changed.add(pid)
            reasons=sorted({e["reason"] for e in corrected[pid]["rejected_name_hits"] if e["tag_id"]==tid})
            prior_ev=old[pid]["labels"].get(tid,[])
            previous_urls={e.get("url","") for e in prior_ev}
            reasons+=sorted({a["reason"] for a in scopes if a["problem_id"]==pid and a["url"] in previous_urls})
            if not reasons:
                reasons=["positive_context_or_fallback_changed" if change=="added" else "conservative_scope_or_title_policy"]
            audit.append(dict(problem_id=pid,title=by[pid]["title"],tag_id=tid,tag=names[tid],change=change,
                reason=" | ".join(sorted(set(reasons))),before_methods=" | ".join(sorted({e["method"] for e in prior_ev})),
                previous_context=" | ".join(e.get("context",e.get("note","")) for e in prior_ev),
                evidence_urls=" | ".join(sorted(u for u in previous_urls if u))))
    csv_write(OUT/"correction_audit.csv",list(audit[0]),audit)
    confirmed=[r for r in audit if r["change"]=="removed" and ((r["tag_id"]=="T111" and "inverse_ackermann" in r["reason"]) or (r["tag_id"]=="T159" and r["problem_id"].startswith("abc262_")))]
    assert len([r for r in confirmed if r["tag_id"]=="T111"])==8
    assert len([r for r in confirmed if r["tag_id"]=="T159"])==5
    for pid,tid in [("abc222_h","T091"),("abc370_g","T135"),("abc476_g","T105")]:
        assert tid in old[pid]["tag_ids"] and tid not in corrected[pid]["tag_ids"]
    assert "T101" in corrected["abc476_g"]["tag_ids"]
    assert all("T111" not in r["tag_ids"] for r in corrected.values())
    assert all("T159" not in r["tag_ids"] for r in corrected.values())
    correction=dict(previous_pairs=sum(len(r["tag_ids"]) for r in old.values()),
        corrected_pairs=sum(len(r["tag_ids"]) for r in corrected.values()),removed_pairs=removed,added_pairs=added,
        changed_problems=len(changed),confirmed_ackermann_removals=8,confirmed_montgomery_removals=5,confirmed_additional_background_removals=3,
        note="Not every removed pair is a proven error: conservative source/code/title policy can also withhold valid alternatives.")
    # Figures: clear comparison and readable full trees, plus a separate upper tree.
    available={f.name for f in font_manager.fontManager.ttflist}
    font=next((n for n in ["Yu Gothic","Meiryo","Noto Sans CJK JP","MS Gothic"] if n in available),"DejaVu Sans")
    matplotlib.rcParams.update({"font.family":[font,"DejaVu Sans"],"axes.unicode_minus":False,"svg.fonttype":"none"})
    fig,axes=plt.subplots(1,3,figsize=(13,4.6))
    keys=["under_2000","all_known","all_difficulties"]
    for ax,metric,title in zip(axes,["active_tags","tags_support_1_or_2","visible_clusters"],["使用タグ数","1〜2問のみのタグ数","表示対象クラスタ数（2問以上）"]):
        vals=[models[k]["summary"][metric] for k in keys]
        ax.bar(range(3),vals,color=["#4878a8","#59a08a","#d6994b"])
        ax.set_xticks(range(3),["2000未満","全難易度\n既知のみ","全難易度\n不明含む"])
        ax.set_title(title);ax.set_ylim(0,max(vals)*1.2)
        ax.bar_label(ax.containers[0]);ax.spines[["top","right"]].set_visible(False)
    fig.suptitle("同じ自動付与ルール・266タグ / Jaccard距離・平均連結法 / cut=0.7",fontsize=13)
    fig.tight_layout(rect=(0,0,1,.91));fig.savefig(OUT/"comparison.png",dpi=160);fig.savefig(OUT/"comparison.svg");plt.close(fig)
    for key in ["under_2000","all_difficulties"]:
        m=models[key]
        labels=[tids[j]+" "+names[tids[j]]+" (n="+str(int(m["support"][j]))+")" for j in m["active"]]
        fig,ax=plt.subplots(figsize=(17,max(16,len(labels)*.17)))
        dendrogram(m["z"],labels=labels,orientation="left",leaf_font_size=8,color_threshold=CUT,ax=ax)
        ax.axvline(CUT,color="#b52a2a",ls="--",lw=1)
        ax.set_xlabel("Jaccard distance / average linkage");ax.set_title(titles[key]+"：全タグの樹形図（n=タグの問題数）")
        fig.tight_layout();fig.savefig(OUT/(key+"_dendrogram.png"),dpi=130);fig.savefig(OUT/(key+"_dendrogram.svg"));plt.close(fig)
        fig,ax=plt.subplots(figsize=(14,5))
        dendrogram(m["z"],truncate_mode="level",p=3,show_leaf_counts=True,color_threshold=CUT,ax=ax,
            leaf_label_func=lambda i: tids[m["active"][i]] if i<len(m["active"]) else "("+str(int(m["z"][i-len(m["active"]),3]))+"タグ)")
        ax.axhline(CUT,color="#b52a2a",ls="--")
        ax.set_title(titles[key]+"：上位の結合（括弧内は省略したタグ数）")
        ax.set_ylabel("Jaccard distance");ax.text(.5,-.16,"距離1.0で同率の結合が多く、左右の順序には意味がありません。",transform=ax.transAxes,ha="center",fontsize=9);fig.tight_layout();fig.savefig(OUT/(key+"_upper_tree.png"),dpi=160);plt.close(fig)
    assert all(sha(p)==digest for p,digest in protected_hashes.items())
    stats=dict(as_of="2026-11-05",annotation_policy="uniform_automatic",distance="jaccard",linkage="average",distance_cut=CUT,
        taxonomy_count=266,unknown_difficulty_problems=int(unknown.sum()),
        datasets={k:m["summary"] for k,m in models.items()},common_tag_stability=stability,
        equal_size_sampling=equal_size,hybrid_sensitivity=hybrid_summary,correction_audit=correction,
        paid_api_calls=0,independent_human_review=False,
        protected_input_sha256={str(p):digest for p,digest in protected_hashes.items()},
        checks=dict(common_problem_vectors_identical=True,old_inputs_preserved=True,confirmed_false_tags_removed=True),
        input_sha256={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/"taxonomy.json",ROOT/"tag_rules.json",ROOT/"evidence_scope.py",ROOT/"tag_all.py",ROOT/"compare_difficulty.py",ROOT/"corpus_sources.jsonl",ROOT/"output_v2_uniform/problem_tag_matrix.csv"]})
    save_json(OUT/"comparison_summary.json",stats)
    report(stats,tagrows,bandrows,names)
    # Deliver a compact review bundle. Large source texts stay local.
    package()
    print(json.dumps(stats,ensure_ascii=True,default=native),flush=True)

def package():
    with zipfile.ZipFile(OUT/"comparison_results.zip","w",zipfile.ZIP_DEFLATED) as z:
        for f in OUT.rglob("*"):
            if f.is_file() and f.suffix in {".csv",".json",".md",".png",".svg"}:z.write(f,f.relative_to(OUT))
        for folder in ["output_v2_uniform","output_v2"]:
            for name in ["problems.csv","all_problems_tagged.csv","problem_tag_matrix.csv","unresolved_problems.csv","tag_catalog.csv","summary.json","verification.json","README.md","source_scope_audit.csv","rejected_evidence.csv"]:
                f=ROOT/folder/name
                if f.exists():z.write(f,Path(folder)/name)
        for name in ["tag_all.py","compare_difficulty.py","verify_comparison.py","test_evidence_scope.py","tag_rules.json","taxonomy.json","verify_dataset.py","evidence_scope.py","collect_statements.py","collect_editorials.py","test_pipeline.py","requirements.txt"]:
            z.write(ROOT/name,Path("reproduce")/name)

def report(s,tagrows,bandrows,names):
    d=s["datasets"];lo=d["under_2000"];full=d["all_difficulties"];known=d["all_known"]
    c=s["correction_audit"];a=s["common_tag_stability"];eq=s["equal_size_sampling"]
    new=[r for r in tagrows if r["first_observed_above_2000"]]
    lines=[
    "# 背景説明由来の誤付与修正と難易度範囲の比較",
    "",
    "作成日：2026-11-05。ABC全3,012問・481コンテスト、タグ候補266種類を使用。",
    "",
    "## 結果",
    "",
    f"同じ自動付与ルールでは、2000未満で{lo['active_tags']}種類、全難易度で{full['active_tags']}種類のタグを観測した。1〜2問しか付かないタグは{lo['tags_support_1_or_2']}種類から{full['tags_support_1_or_2']}種類になった。問題範囲の拡張により観測は増えたが、タグの粒度やクラスタの意味がそろったとは判断できない。",
    "",
    "| 指標 | 2000未満 | 全難易度（既知のみ） | 全難易度（不明含む） |",
    "|---|---:|---:|---:|"]
    for label,key in [("対象問題","problem_count"),("1種類以上のタグが付いた問題","tagged_problem_count"),("自動では付与できなかった問題","untagged_problem_count"),("問題–タグ対応","assigned_pairs"),("観測されたタグ","active_tags"),("未使用タグ","unused_tags"),("1〜2問のみのタグ","tags_support_1_or_2"),("3問以上のタグ","tags_support_at_least_3"),("cut=0.7のクラスタ","clusters"),("2問以上を含む表示対象クラスタ","visible_clusters"),("複数タグをまとめたクラスタ","multi_tag_clusters")]:
        lines.append(f"| {label} | {lo[key]:,} | {known[key]:,} | {full[key]:,} |")
    lines += ["","![難易度範囲の比較](comparison.png)","",
    "未付与は「該当するアルゴリズムがない」という意味ではない。単純な算術や条件分岐に対応するタグの不足、暗黙の解法、解説取得・抽出の不足、ルールの拾い漏れが含まれる。",
    "",
    "## 比較で固定した条件","",
    "- タグ語彙266種類、問題文・解説の凍結スナップショット、名前・説明・コードの検出ルール、背景節の除外条件を固定した。",
    "- 全3,012問を一度だけ自動付与し、その行列から2000未満を抽出した。同じ問題の266列の値が両条件で完全一致することを確認した。",
    "- 主比較には旧898問の引継ぎタグも27問の個別AIレビューも使っていない。難易度帯による手修正の偏りを抑えるためである。",
    "- クラスタリングは問題集合のJaccard距離、平均連結法、distance cut=0.7。0件タグをクラスタリングから除外し、各条件で観測されたタグだけを使った。",
    "- 表示対象はクラスタ内の問題IDの和集合が2問以上のもの。タグごとの件数を単純に足していない。",
    "- 難易度不明23問は2000未満に含めず、全難易度には含めた。既知のみ2,989問の結果も併記した。",
    "- 未付与問題の行は保存したが、全0行はJaccard距離の交差・和集合を変えない。問題数が増えただけでは距離は変わらない。",
    "",
    "## 修正内容","",
    "アッカーマン関数8対応とMontgomery法5対応について、背景説明・他問題の節からの誤付与を削除した。アッカーマン関数はUnion-Findの計算量に登場する逆関数の説明であり、その問題で関数を計算する解法ではなかった。Montgomery法はABC262の複数問題に同じ総合解説が紐付いたことに由来していた。",
    "",
    "ABC222 Hの説明用のカタラン数の例題、ABC370 Gの計算量評価での素数定理、ABC476 Gの参考記事名のSpernerの定理という3対応も、原文を点検して除外した。ABC476 Gで上界の証明に実際に使っているLYM不等式は残した。",
    "",
    "加えて、次の出典・根拠を保守的に扱うようにした。",
    "",
    "- 同じURL・同じ本文が複数問題に丸ごと紐付いた解説を、問題ごとの範囲を確認するまで自動付与から隔離する。PDFは冒頭の問題名が対象のタイトルと完全一致する場合だけその対象で利用する。",
    "- 「この問題の解説」の前にまとまった前提説明がある文書は、実際の問題解説部分を使う。ABC265 HのOR/AND畳み込みの他問題例を拾わず、実際の節にあるXOR畳み込みとFFTは保持した。",
    "- 例題から元の問題に戻る区切りや参考文献・関連問題の節を除外する。",
    "- 不可能・時間不足を述べる節を負例として扱う。同じ文の「全探索では間に合わないため二分探索を使う」では、後半の二分探索を残す。",
    "- コードはC++等のmain内、Pythonのトップレベルとそこから呼ぶ関数に検出範囲を限定する。未使用ライブラリ・定義だけの断片を唯一の根拠にしない。",
    "- タイトルだけに現れる名前を、解法を使った根拠にしない。",
    "",
    f"旧版との修正前後比較には、引継ぎ・個別AIレビューを双方で同じように含む補助データを別途作成した。{c['changed_problems']}問で対応が変わり、削除{c['removed_pairs']}対応・追加{c['added_pairs']}対応、対応総数は{c['previous_pairs']}→{c['corrected_pairs']}になった。",
    "",
    "**削除件数すべてを「確認済みの誤付与」とは数えていない。** 出典・コードの範囲を保守的に限定したため、実行可能な別解を保留したものや補助技法の拾い漏れもあり得る。旧タグの引継ぎ自体も全件検証済みではない。修正前後の差分は [correction_audit.csv](correction_audit.csv)、根拠の除外は各出力フォルダーの rejected_evidence.csv / source_scope_audit.csv に記録した。",
    "",
    "## 高難易度で初めて観測したタグ","",
    "| タグ | 2000未満 | 2000以上 | 不明 |",
    "|---|---:|---:|---:|"]
    for r in new:lines.append(f"| {r['tag_id']} {r['tag']} | {r['under_2000']} | {r['at_least_2000']} | {r['unknown']} |")
    lines += ["",
    "これらは現ルールでの観測候補であり、全件の正付与を保証するものではない。少数例では、誤付与1件の影響も大きい。",
    "",
    "## 共通タグのまとまりは変わったか","",
    f"両条件で観測された共通{a['common_tags']}タグで比較すると、クラスタ分割のARIは{a['ari_restricting_complete_clusterings']:.3f}だった。ARIはラベル番号によらず分割の一致を測り、1は同一を示す。共通タグだけを両条件で再クラスタリングした場合のARIは{a['ari_reclustering_only_common_tags']:.3f}だった。",
    "",
    f"2000未満で同じクラスタだったタグ対{a['co_clustered_pairs_under_2000']}組のうち、全難易度でも同じだったものは{a['co_clustered_pairs_retained']}組。分離は{a['pairs_split']}組、新しく同じクラスタになったものは{a['pairs_joined']}組。共通タグ間のJaccard距離の平均絶対変化は{a['mean_absolute_jaccard_distance_change']:.4f}だった。",
    "",
    "樹形図の上位には距離1.0の同率結合が多い。共通の付与問題を持たないタグ対は距離1となり、そこでの結合順序・左右の配置に意味を読み取らない。上位図と、拡大可能な全体SVGを併用する。",
    "",
    "この一致度は正しさの評価ではない。単独タグのクラスタが多数あり、ARIだけでは少数の結合・分離の内容が分かりにくいため、具体的な変化を [common_tag_cluster_changes.csv](common_tag_cluster_changes.csv) で併せて確認する。",
    "",
    "## 問題数と難易度の影響を切り分ける補助比較","",
    f"全難易度の既知2,989問から、2000未満と同じ2,473問を非復元抽出した（乱数seed 0〜29、30回）。観測タグ数は平均{eq['active_tags']['mean']:.1f}種類、範囲{eq['active_tags']['minimum']}〜{eq['active_tags']['maximum']}種類。2000未満の{lo['active_tags']}種類と比べられる。",
    "",
    f"3問以上のタグは平均{eq['tags_support_at_least_3']['mean']:.1f}種類（{eq['tags_support_at_least_3']['minimum']}〜{eq['tags_support_at_least_3']['maximum']}）。各標本に2000以上の問題を平均{eq['high_difficulty_problems']['mean']:.1f}問含む。",
    "",
    "これは同じ問題数での構成比較であり、無作為実験・精度検証ではない。全体の増加を単純に「問題数が増えた効果」だけと解釈できないことを確認するための補助資料である。",
    "",
    "## 残る制約","",
    "| 難易度帯 | 問題数 | タグ付与済み | 付与率 | 元の解説あり | 総合解説の隔離に影響された問題 |",
    "|---|---:|---:|---:|---:|---:|"]
    for b in bandrows:lines.append(f"| {b['band']} | {b['problem_count']} | {b['tagged_problem_count']} | {b['tagged_rate']:.1%} | {b['with_raw_editorial']} | {b['affected_by_quarantined_source']} |")
    lines += ["",
    "難易度帯で付与率や解説の入手状況が異なる。自動付与は簡単な問題で技法名を拾いにくく、高難易度ほど名前付き技法が説明されやすい可能性がある。また、出典には既存チーム収集分、公式Web、ユーザー解説、PDFが混在し、解説件数・品質・PDFの抽出精度は一定ではない。同じルールを使っても、これらの偏りは残る。",
    "",
    "語彙には、アルゴリズム・データ構造・数学的概念・上位分類が混在する。問題数の拡張だけで粒度はそろわず、Jaccardの共起も学習単位としての同義を保証しない。全件の主解・別解・補助の判定と独立した人手評価は未実施。",
    "",
    "次は、新しく観測したタグと少数例のタグを優先して人手で確認し、主解・実行可能な別解・補助・背景の役割を分けるとよい。クラスタは候補として扱い、可視化用のタグ数を決める根拠にこの実験だけを使わない。",
    "",
    "## データ・図・再実行","",
    "- [全266タグの件数比較](tag_support_comparison.csv)",
    "- [比較条件・集計値・入力ハッシュ](comparison_summary.json)",
    "- [2000未満のクラスタ内訳](under_2000/cluster_members.csv)",
    "- [全難易度のクラスタ内訳](all_difficulties/cluster_members.csv)",
    "- [2000未満の全体樹形図（SVG・拡大可）](under_2000_dendrogram.svg)",
    "- [全難易度の全体樹形図（SVG・拡大可）](all_difficulties_dendrogram.svg)",
    "- [2000未満の上位結合](under_2000_upper_tree.png) / [全難易度の上位結合](all_difficulties_upper_tree.png)",
    "- [結果一式ZIP](comparison_results.zip)",
    "",
    "全問題の解説本文を含む corpus_sources.jsonl はローカルに保存し、ZIPには含めていない。ZIP単体で元のタグ付与を再実行するには、この凍結入力とmanifest.json等が別途必要。ZIPには比較に使った行列、結果、修正ルール、検証コードを収録した。",
    "",
    "旧 output/ と従来の898問用データは保存。修正版の引継ぎありデータは ../output_v2/、主比較用の統一自動付与データは ../output_v2_uniform/。主比較と補助データのタグ数は混同しない。",
    "",
    "再実行（abc_allディレクトリ、既存仮想環境で実行）：",
    "",
    "~~~powershell",
    "..\\.venv-clustering\\Scripts\\python.exe -X utf8 tag_all.py --uniform --output-dir output_v2_uniform",
    "..\\.venv-clustering\\Scripts\\python.exe -X utf8 tag_all.py --output-dir output_v2",
    "..\\.venv-clustering\\Scripts\\python.exe -X utf8 verify_dataset.py output_v2_uniform",
    "..\\.venv-clustering\\Scripts\\python.exe -X utf8 verify_dataset.py output_v2",
    "..\\.venv-clustering\\Scripts\\python.exe -X utf8 compare_difficulty.py",
    "..\\.venv-clustering\\Scripts\\python.exe -X utf8 verify_comparison.py",
    "~~~",
    "",
    "外部AI APIは利用していない。追加API費用0円。アプリケーションへの反映はこの比較には含めていない。",
    ""]
    (OUT/"README.md").write_text("\n".join(lines),encoding="utf-8")

if __name__=="__main__":build()
