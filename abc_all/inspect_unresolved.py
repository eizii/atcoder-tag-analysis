import csv,json
from collections import Counter
from collect_statements import ROOT,load_json
with (ROOT/"output/unresolved_problems.csv").open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
print(json.dumps({"count":len(rows),"by_index":dict(Counter(r["problem_index"] for r in rows))},ensure_ascii=True))
for r in rows[:30]:
    obj=load_json(ROOT/"problems"/(r["problem_id"]+".json"))
    ed=load_json(ROOT/"editorials"/(r["problem_id"]+".json"))
    print(json.dumps({"id":r["problem_id"],"title":r["title"],"statement":obj["statement"][:500],"editorial":" ".join(x["text"] for x in ed["editorials"])[:700]},ensure_ascii=True))
