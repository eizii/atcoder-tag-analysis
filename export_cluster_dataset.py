# -*- coding: utf-8 -*-
"""Export problem tags for any generated hierarchy cut (no network or LLM calls)."""
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def read_csv(file):
    with file.open(encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))

def save_csv(file,rows,columns):
    with file.open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=columns,extrasaction="ignore",lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def save_json(file,obj):
    file.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clustering-dir",default="clustering")
    parser.add_argument("--input-dir",default="validation/revised")
    args=parser.parse_args()
    output=(ROOT/args.clustering_dir).resolve()
    inputs=(ROOT/args.input_dir).resolve()
    summary=json.loads((output/"summary.json").read_text(encoding="utf-8"))
    threshold=summary["default_distance_threshold"]
    assignments=read_csv(inputs/"all_problems_tagged.csv")
    assert hashlib.sha256((inputs/"all_problems_tagged.csv").read_bytes()).hexdigest()==summary["source_sha256"]["all_problems_tagged.csv"]
    membership=read_csv(output/"clusters_all.csv")
    assert len(membership)==summary["used_tags"]
    assert all(float(r["distance_threshold"])==threshold for r in membership)
    group_rows=defaultdict(list)
    by_tag={}
    for row in membership:
        group_rows[row["cluster_id"]].append(row)
        assert row["tag_id"] not in by_tag
        by_tag[row["tag_id"]]=row
    count=len(group_rows)
    assert count==summary["models"][0]["cluster_count"]
    version=f"hc{count}-jaccard-average-d{threshold:g}-v1"
    labels={cid:cid+": "+rows[0]["representative_tag"] for cid,rows in group_rows.items()}
    problem_rows=defaultdict(list)
    for row in assignments:
        assert by_tag[row["tag_id"]]["tag"]==row["tag"]
        problem_rows[row["problem_id"]].append(row)
    assert len(problem_rows)==summary["problem_count"]
    columns=["tag","problem_id","title","difficulty","diff_band","url"]
    exported,matrix,problems=[],[],[]
    cluster_problems=defaultdict(set)
    for pid,rows in sorted(problem_rows.items()):
        meta={key:rows[0][key] for key in columns if key!="tag"}
        assert all({key:r[key] for key in columns if key!="tag"}==meta for r in rows)
        cids=sorted({by_tag[r["tag_id"]]["cluster_id"] for r in rows})
        for cid in cids:
            exported.append(dict(meta,tag=labels[cid]))
            cluster_problems[cid].add(pid)
        ordered=sorted(rows,key=lambda r:r["tag_id"])
        problems.append(dict(problem_id=pid,title=meta["title"],
            cluster_ids=";".join(cids),cluster_labels=" | ".join(labels[cid] for cid in cids),
            algorithm_tag_ids=";".join(r["tag_id"] for r in ordered),
            algorithm_tags=" | ".join(r["tag"] for r in ordered),
            needs_review=int(any(r["needs_review"]=="1" for r in rows)),tagging_version=version))
        matrix.append(dict(problem_id=pid,**{cid:int(cid in cids) for cid in sorted(labels)}))
    assert len({(r["problem_id"],r["tag"]) for r in exported})==len(exported)
    assert {r["tag"] for r in exported}==set(labels.values())
    save_csv(output/"all_problems_clustered.csv",exported,columns)
    save_csv(output/"problem_cluster_matrix.csv",matrix,["problem_id"]+sorted(labels))
    save_csv(output/"problem_clusters.csv",problems,list(problems[0]))
    clusters,mapping=[],[]
    for cid,rows in sorted(group_rows.items()):
        assert len(cluster_problems[cid])==int(rows[0]["cluster_problem_union_count"])
        clusters.append(dict(cluster_id=cid,label=labels[cid],
            representative=rows[0]["representative_tag"],
            member_tags=[dict(tag_id=r["tag_id"],tag=r["tag"]) for r in rows],
            algorithm_count=len(rows),problem_count=len(cluster_problems[cid])))
        mapping.extend(dict(tag_id=r["tag_id"],tag=r["tag"],cluster_id=cid,cluster_label=labels[cid]) for r in rows)
    catalog=dict(version=version,source_problem_count=len(problem_rows),
        distance="jaccard",linkage="average",distance_threshold=threshold,clusters=clusters,
        problemCatalog="public/all_problems.csv",
        problemCatalogSha256=hashlib.sha256((output/"all_problems_clustered.csv").read_bytes()).hexdigest(),
        source_sha256=summary["source_sha256"])
    save_json(output/"cluster_catalog.json",catalog)
    save_csv(output/"algorithm_to_cluster.csv",mapping,["tag_id","tag","cluster_id","cluster_label"])
    result=dict(version=version,distance_cut=threshold,problem_count=len(problem_rows),
        fine_tag_count=len(membership),fine_tag_pairs=len(assignments),
        cluster_count=count,cluster_problem_pairs=len(exported),
        multi_tag_clusters=sum(len(rows)>1 for rows in group_rows.values()),
        singleton_clusters=sum(len(rows)==1 for rows in group_rows.values()))
    save_json(output/"dataset_summary.json",result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
