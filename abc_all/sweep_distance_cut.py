"""Count flat clusters at fixed cuts using the already-frozen average-linkage trees."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy.cluster.hierarchy import fcluster,is_valid_linkage
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"comparison_20261105"
summary=json.loads((OUT/"comparison_summary.json").read_text(encoding="utf-8"))
models={}
for key in ["all_difficulties","under_2000"]:
    p=OUT/key/"linkage.csv"
    z=np.loadtxt(p,delimiter=",",skiprows=1)
    assert is_valid_linkage(z,throw=True)
    n=len(z)+1
    assert n==summary["datasets"][key]["active_tags"]
    assert np.all(np.diff(z[:,2])>=-1e-12)
    models[key]=(z,n)
rows=[]
for i in range(1,11):
    cut=i/10
    row={"distance_cut":f"{cut:.1f}"}
    for key,(z,n) in models.items():
        labels=fcluster(z,cut,criterion="distance")
        count=len(set(labels))
        assert count==n-int(np.count_nonzero(z[:,2]<=cut))
        if i==7:assert count==summary["datasets"][key]["clusters"]
        row[key]=count
    rows.append(row)
for key in models:
    assert all(rows[i][key]>=rows[i+1][key] for i in range(len(rows)-1))
    assert rows[-1][key]==1
with (OUT/"distance_cut_sweep.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
result=dict(distance="jaccard",linkage="average",cut_rule="merge distance <= distance_cut",
    count_definition="flat clusters including single-tag and single-problem clusters; no minimum problem-count filter",
    input_tag_counts={k:n for k,(z,n) in models.items()},results=rows,
    source_linkage_sha256={k:hashlib.sha256((OUT/k/"linkage.csv").read_bytes()).hexdigest() for k in models},
    checks=["valid_linkage","leaf_counts_match_original_results","merge_count_reconciliation","cut_0.7_matches_existing_summary","monotonic_counts","cut_1.0_single_cluster"])
(OUT/"distance_cut_sweep.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,ensure_ascii=True))
