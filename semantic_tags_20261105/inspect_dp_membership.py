import csv,io,json,subprocess
from pathlib import Path
app=Path("C:/Users/ejham/theme2026-kaziru")
for ref in ["main","origin/main"]:
    raw=subprocess.check_output(["git","show",ref+":public/all_problems.csv"],cwd=app)
    rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    names=sorted({r["tag"] for r in rows if "dp" in r["tag"].lower()})
    groups={t:{r["problem_id"] for r in rows if r["tag"]==t} for t in names}
    result=dict(ref=ref,dp_tags={t:len(p) for t,p in groups.items()},tree_vs_basic=[])
    for t in names:
        if "木" not in t:continue
        for b in names:
            if "基礎" not in b:continue
            result["tree_vs_basic"].append(dict(tree_tag=t,basic_tag=b,tree_count=len(groups[t]),basic_count=len(groups[b]),overlap=len(groups[t]&groups[b]),tree_also_basic=sorted(groups[t]&groups[b]),tree_only=sorted(groups[t]-groups[b])))
    print(json.dumps(result,ensure_ascii=True))
