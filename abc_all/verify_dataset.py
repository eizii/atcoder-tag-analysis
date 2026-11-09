"""Independently reconcile all ABC outputs and disclose unresolved labels."""
import csv,hashlib,json
from collections import Counter
from collect_statements import ROOT,load_json,save_json

def read_csv(p):
    with p.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def verify(output_dir="output"):
    out=ROOT/output_dir
    manifest=load_json(ROOT/"manifest.json")
    expected={p["problem_id"] for p in manifest["problems"]}
    rows=read_csv(out/"problems.csv")
    catalog=read_csv(out/"tag_catalog.csv")
    assignments=read_csv(out/"all_problems_tagged.csv")
    matrix=read_csv(out/"problem_tag_matrix.csv")
    assert len(rows)==len(expected)==len(set(r["problem_id"] for r in rows))
    assert {r["problem_id"] for r in rows}==expected
    assert {r["problem_id"] for r in matrix}==expected
    assert len(catalog)==266 and len(set(r["tag_id"] for r in catalog))==266
    names={r["tag_id"]:r["tag"] for r in catalog}
    by={r["problem_id"]:r for r in rows}
    pairs={(r["problem_id"],r["tag_id"]) for r in assignments}
    assert len(pairs)==len(assignments)
    for r in assignments:
        assert r["problem_id"] in expected
        assert r["tag"]==names[r["tag_id"]]
        assert r["related"]=="1"
    rebuilt=set()
    for r in matrix:
        for tid in names:
            assert r[tid] in {"0","1"}
            if r[tid]=="1": rebuilt.add((r["problem_id"],tid))
    assert pairs==rebuilt
    counts=Counter(t for p,t in pairs)
    assert all(int(r["problem_count"])==counts[r["tag_id"]] for r in catalog)
    rowcounts=Counter(p for p,t in pairs)
    assert all(int(r["tag_count"])==rowcounts[r["problem_id"]] for r in rows)
    jsonl_ids=[]
    for line in (out/"problems_tagged.jsonl").open(encoding="utf-8"):
        obj=json.loads(line)
        pid=obj["problem_id"]
        jsonl_ids.append(pid)
        assert obj["statement"]
        assert hashlib.sha256(obj["statement"].encode()).hexdigest()==obj["statement_sha256"]
        assert set(obj["tag_ids"])=={t for p,t in pairs if p==pid}
        assert not obj["independent_human_review"]
    assert len(jsonl_ids)==len(expected) and set(jsonl_ids)==expected
    queue=read_csv(out/"unresolved_problems.csv")
    assert {r["problem_id"] for r in queue}=={r["problem_id"] for r in rows if r["tagging_status"].startswith("unresolved_")}
    summary=load_json(out/"summary.json")
    assert summary["problem_count"]==len(expected)
    assert summary["assigned_pairs"]==len(assignments)
    assert summary["unresolved_problem_count"]==len(queue)
    assert summary["paid_api_calls"]==0
    coverage=dict(problem_count=len(expected),tagged_problem_count=sum(rowcounts[p]>0 for p in expected),unresolved_problem_count=len(queue),untagged_problem_count=sum(rowcounts[p]==0 for p in expected),used_tags=len(counts),assigned_pairs=len(pairs),checks_passed=True)
    save_json(out/"verification.json",coverage)
    print(json.dumps(coverage,ensure_ascii=True))

if __name__=="__main__":
    import sys
    verify(sys.argv[1] if len(sys.argv)>1 else "output")
