import hashlib,json,urllib.request,zipfile
from pathlib import Path
from build_dataset import ROOT,APP,load,save,sha
manifest=load(ROOT/"change_manifest.json")
assert all(sha(APP/rel)==entry["staged_sha256"] for rel,entry in manifest.items())
assert all(entry["before_sha256"] is None or sha(ROOT/"app_backup"/rel)==entry["before_sha256"] for rel,entry in manifest.items())
live={}
try:
    with urllib.request.urlopen("http://localhost:5173/all_problems.csv",timeout=5) as r:body=r.read()
    live={"server":"http://localhost:5173","csv_matches_current_file":hashlib.sha256(body).hexdigest()==sha(APP/"public/all_problems.csv")}
    assert live["csv_matches_current_file"]
except (OSError,urllib.error.URLError) as e:
    live={"server_check":"unavailable","error":type(e).__name__}
save(ROOT/"check_status.json",dict(build="passed",lint="passed with one pre-existing unused-variable warning",
    format_check="unavailable: prettier is not installed",data_and_ssr_checks=load(ROOT/"verification.json"),
    browser_ui="Computer Use stopped: browser URL could not be determined on Windows with enough confidence",
    live_server=live,applied_files_match=True,backups_intact=True,published=False,additional_api_cost_yen=0))
text="""
## アプリへの反映・確認結果

- C:/Users/ejham/theme2026-kaziru のアプリへ反映済み。公開・コミットはしていない。
- [検証結果](verification.json)：67個の円グラフのReact描画、15個の単件分類の非表示、898問の保持、MDSの座標、選択カードの説明・題材・個別手法名、本人の進捗、旧同レート帯データの除外を確認。
- npm run build は成功。npm run lint はエラー0、変更前からの未使用変数警告1件。
- npm run format:check はPrettierが未導入のため実行不可。
- 実画面の操作はWindowsのブラウザーURLを十分な確度で取得できずComputer Useが停止したため未確認。レスポンシブ表示・クリック操作の実画面検証は残る。
- [チェック状況](check_status.json) に詳細を保存。
- app_backup/ に今回の変更直前のファイルを保存。元からある未コミットの変更を含む状態を保持した。
- [結果一式ZIP](semantic_tag_results.zip) に整理方針、対応表、差し替え用データ、検証結果を収録。
"""
p=ROOT/"README.md"
s=p.read_text(encoding="utf-8")
if "## アプリへの反映・確認結果" not in s:p.write_text(s+text,encoding="utf-8")
with zipfile.ZipFile(ROOT/"semantic_tag_results.zip","w",zipfile.ZIP_DEFLATED) as z:
    for name in ["README.md","policy.json","verification.json","check_status.json","build_dataset.py","verify_app.mjs"]:
        z.write(ROOT/name,name)
    for f in (ROOT/"output").iterdir():
        if f.is_file():z.write(f,Path("output")/f.name)
with zipfile.ZipFile(ROOT/"semantic_tag_results.zip") as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))
print(json.dumps(dict(applied_files=len(manifest),backup_integrity="passed",archive_integrity="passed",live=live),ensure_ascii=True))
