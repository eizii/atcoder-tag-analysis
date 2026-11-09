"""Show every nonempty semantic learning unit, including single-problem units."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from build_dataset import ROOT,APP,load,save,sha,build
backup=ROOT/"display_all_update"/"before"
backup.mkdir(parents=True,exist_ok=True)
targets=["src/utils/statistics.js","src/components/Main.jsx","src/data/tagCatalog.json","docs/SEMANTIC_TAGS.md"]
for rel in targets:
    dest=backup/rel
    assert not dest.exists(),"Preserve existing backup: "+str(dest)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes((APP/rel).read_bytes())
for name in ["policy.json","build_dataset.py","README.md","verification.json"]:
    dest=backup/"analysis"/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    if (ROOT/name).exists():dest.write_bytes((ROOT/name).read_bytes())
csv_sha=sha(APP/"public/all_problems.csv")
policy=load(ROOT/"policy.json")
policy["display_min_problem_count"]=1
save(ROOT/"policy.json",policy)
p=ROOT/"build_dataset.py"
s=p.read_text(encoding="utf-8")
s=s.replace('    policy=load(ROOT/"policy.json")','    policy=load(ROOT/"policy.json")\n    min_count=int(policy.get("display_min_problem_count",1))')
s=s.replace('visible=len(supports[uid])>=2','visible=len(supports[uid])>=min_count')
s=s.replace('visible=int(len(supports[uid])>=2)','visible=int(len(supports[uid])>=min_count)')
s=s.replace('display_min_problem_count=2,visible_unit_count=sum(len(supports[u])>=2 for u in groups)',
            'display_min_problem_count=min_count,visible_unit_count=sum(len(supports[u])>=min_count for u in groups)')
s=s.replace('| 2問以上を含む表示分類 |','| 画面に表示する分類 |')
s=s.replace('1問以下を非表示にする従来の設定を維持し、定義とデータは削除していない。',
            '1問の分類も含め、問題を持つすべての分類を表示する。定義とデータは削除していない。')
s=s.replace("'非表示（2問未満）'","'非表示（対象問題なし）'")
p.write_text(s,encoding="utf-8")
# Reload the changed generator; preserve the historical original input in before/.
import importlib,build_dataset
importlib.reload(build_dataset)
build_dataset.build()
generated=load(ROOT/"output/tagCatalog.json")
assert generated["visible_unit_count"]==82 and all(g["visible"] for g in generated["clusters"])
assert sha(ROOT/"output/all_problems.csv")==csv_sha,"Assignments must not change"
statistics=(APP/"src/utils/statistics.js").read_text(encoding="utf-8")
assert statistics.count("MIN_PROBLEMS_PER_TAG = 2;")==1
statistics=statistics.replace("MIN_PROBLEMS_PER_TAG = 2;","MIN_PROBLEMS_PER_TAG = 1;")
main=(APP/"src/components/Main.jsx").read_text(encoding="utf-8")
assert main.count('import { MIN_PROBLEMS_PER_TAG } from "../utils/statistics";')==1
main=main.replace('import { MIN_PROBLEMS_PER_TAG } from "../utils/statistics";\n',"")
old="{tagCatalog.source_problem_count}問（学習単位・{MIN_PROBLEMS_PER_TAG}問以上）"
assert main.count(old)==1
main=main.replace(old,"{tagCatalog.source_problem_count}問（学習単位）")
docs=(APP/"docs/SEMANTIC_TAGS.md").read_text(encoding="utf-8")
docs=docs.replace("2問以上の分類を表示するため、実際の円グラフは67個です。",
                  "1問の分類も含め、問題を持つ全82分類を円グラフに表示します。")
docs=docs.replace("1問以下の分類もCSVとカタログには保持します。","問題を持つ全分類を表示します。")
(APP/"src/utils/statistics.js").write_text(statistics,encoding="utf-8")
(APP/"src/components/Main.jsx").write_text(main,encoding="utf-8")
(APP/"src/data/tagCatalog.json").write_bytes((ROOT/"output/tagCatalog.json").read_bytes())
(APP/"docs/SEMANTIC_TAGS.md").write_text(docs,encoding="utf-8")
assert sha(APP/"public/all_problems.csv")==csv_sha
save(ROOT/"display_all_update/change_summary.json",dict(previous_visible=67,current_visible=82,
    single_problem_units_added=15,problem_count=898,assignments_unchanged=True,
    csv_sha256=csv_sha,changed_app_files=targets))
print(json.dumps({"visible_units":82,"added_single_problem_units":15,"csv_unchanged":True}))
