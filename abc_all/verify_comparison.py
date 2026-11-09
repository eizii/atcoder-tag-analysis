"""Independent reconciliation of comparison subsets, distances and cluster members."""
import csv,hashlib,json
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.cluster.hierarchy import linkage,fcluster
from scipy.spatial.distance import pdist
from sklearn.metrics import adjusted_rand_score
from collect_statements import ROOT,load_json,save_json
def read(p):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def verify():
    out=ROOT/"comparison_20261105"
    summary=load_json(out/"comparison_summary.json")
    taxonomy=load_json(ROOT/"taxonomy.json");tids=[r["tag_id"] for r in taxonomy]
    full=read(ROOT/"output_v2_uniform/problem_tag_matrix.csv")
    by={r["problem_id"]:r for r in full}
    problems={r["problem_id"]:r for r in read(ROOT/"output_v2_uniform/problems.csv")}
    all_pairs=read(ROOT/"output_v2_uniform/all_problems_tagged.csv")
    assert len({(r["problem_id"],r["tag_id"]) for r in all_pairs})==len(all_pairs)
    partitions={}
    for key,stats in summary["datasets"].items():
        rows=read(out/key/"problem_tag_matrix.csv")
        ids=[r["problem_id"] for r in rows]
        expect={pid for pid,p in problems.items() if key=="all_difficulties" or (p["difficulty"]!="" and (key=="all_known" or float(p["difficulty"])<2000))}
        assert set(ids)==expect and len(ids)==len(expect)==stats["problem_count"]
        assert all(r==by[r["problem_id"]] for r in rows)
        x=np.array([[int(r[t]) for t in tids] for r in rows],dtype=int)
        counts=x.sum(axis=0);active=[t for t,n in zip(tids,counts) if n]
        assert int(x.sum())==stats["assigned_pairs"]
        assert int(x.any(axis=1).sum())==stats["tagged_problem_count"]
        assert len(active)==stats["active_tags"]
        assert sum(1<=n<=2 for n in counts)==stats["tags_support_1_or_2"]
        members=read(out/key/"cluster_members.csv")
        assert len(members)==len(active) and {r["tag_id"] for r in members}==set(active)
        assert len({r["tag_id"] for r in members})==len(members)
        groups=load_json(out/key/"clusters.json")["clusters"]
        assert len(groups)==stats["clusters"]
        assign={r["tag_id"]:r["cluster_id"] for r in members}
        for g in groups:
            j=[tids.index(t) for t in g["tag_ids"]]
            support={pid for pid,row in zip(ids,x[:,j].any(axis=1)) if row}
            assert support==set(g["problem_ids"]) and len(support)==g["problem_count"]
            assert all(assign[t]==g["cluster_id"] for t in g["tag_ids"])
        assert sum(g["problem_count"]>=2 for g in groups)==stats["visible_clusters"]
        d=pdist(x[:,counts>0].T.astype(bool),metric="jaccard")
        z=linkage(d,method="average")
        rebuilt=fcluster(z,.7,criterion="distance")
        supplied=[assign[t] for t in active]
        assert adjusted_rand_score(rebuilt,supplied)==1.0
        partitions[key]=assign
    changes=read(out/"common_tag_cluster_changes.csv")
    common=sorted(set(partitions["under_2000"])&set(partitions["all_difficulties"]))
    expected=set()
    for i,t in enumerate(common):
        for u in common[i+1:]:
            a=partitions["under_2000"][t]==partitions["under_2000"][u]
            b=partitions["all_difficulties"][t]==partitions["all_difficulties"][u]
            if a!=b:expected.add((t,u,"split" if a else "joined"))
    assert expected=={(r["tag_id_1"],r["tag_id_2"],r["change"]) for r in changes}
    for filename,digest in summary["input_sha256"].items():
        assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==digest
    for filename,digest in summary["protected_input_sha256"].items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest()==digest
    assert summary["paid_api_calls"]==0
    checks=dict(checks_passed=True,subsets=3,common_problem_vectors_identical=True,
        pair_and_matrix_consistent=True,cluster_members_and_problem_unions_consistent=True,
        partitions_reproduced=True,cluster_changes_reconciled=True,input_hashes_match=True,
        paid_api_calls=0)
    save_json(out/"verification.json",checks)
    from compare_difficulty import package
    package()
    print(json.dumps(checks))
if __name__=="__main__":verify()
