import hashlib,json,zipfile,urllib.request
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from build_dataset import ROOT,APP,load,save,sha
change=load(ROOT/"display_all_update/change_summary.json")
assert sha(APP/"public/all_problems.csv")==change["csv_sha256"]
catalog=load(APP/"src/data/tagCatalog.json")
assert catalog["visible_unit_count"]==82 and all(g["visible"] for g in catalog["clusters"])
status=load(ROOT/"check_status.json")
status["data_and_ssr_checks"]=load(ROOT/"verification.json")
status["display_update"]=change
status["current_app_sha256"]={rel:sha(APP/rel) for rel in change["changed_app_files"]}
status["browser_ui"]="Not rechecked: browser URL confidence limitation encountered during the preceding task."
save(ROOT/"check_status.json",status)
save(ROOT/"display_all_update/verification.json",status)
note="""
## 2026-11-05：最小問題数による表示制限の解除

1問の分類も含め、全82分類を表示するように変更済み。表示数は67→82。
898問・1,648対応のCSVはハッシュが一致しており、タグ付与は変更していない。
カタログ、表示件数、アプリの説明、再生成時の表示条件も更新した。

ビルドと82個のReact描画、15個の単件分類の表示、配置座標、進捗集計を確認済み。
lintはエラー0、変更前からの未使用変数警告1件。
書式検査はPrettier未導入で実行不可。実画面の手動確認は未実施。
[検証結果](verification.json) / [チェック状況](check_status.json)。
変更直前の4ファイルは display_all_update/before/ に保存。
"""
p=ROOT/"README.md";p.write_text(p.read_text(encoding="utf-8")+note,encoding="utf-8")
with zipfile.ZipFile(ROOT/"semantic_tag_results.zip","w",zipfile.ZIP_DEFLATED) as z:
    for name in ["README.md","policy.json","verification.json","check_status.json","build_dataset.py","verify_app.mjs"]:
        z.write(ROOT/name,name)
    for f in (ROOT/"output").iterdir():
        if f.is_file():z.write(f,Path("output")/f.name)
with zipfile.ZipFile(ROOT/"semantic_tag_results.zip") as z:
    assert z.testzip() is None
print(json.dumps({"displayed_units":82,"single_problem_units_displayed":15,"csv_unchanged":True,"archive":"verified"}))
