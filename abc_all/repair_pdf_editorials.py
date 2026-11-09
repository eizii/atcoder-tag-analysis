"""Repair legacy PDF redirects and re-extract complete problem sections from cached PDFs."""
import json
from collect_statements import ROOT,Client,load_json,save_json
from collect_editorials import links_for_tasks,pdf_fragments

m=load_json(ROOT/"manifest.json")
by={}
for p in m["problems"]: by.setdefault(p["contest_id"],[]).append(p)
client=Client()
fixed=0
failures=[]
for cid,ps in by.items():
    pdf=ROOT/"cache"/(cid+"_editorial.pdf")
    if not pdf.exists(): continue
    raw=pdf.read_bytes()
    index=ROOT/"cache"/(cid+"_editorial.html")
    if not index.exists(): continue
    _,urls=links_for_tasks(index.read_bytes())
    if not urls: continue
    url=urls[0]
    try:
        if not raw.startswith(b"%PDF-"):
            raw=client.get(url)
            if not raw.startswith(b"%PDF-"): raise ValueError("Not a PDF")
            pdf.write_bytes(raw)
        parts=pdf_fragments(raw,ps,url,cid)
        for pid,part in parts.items():
            dest=ROOT/"editorials"/(pid+".json")
            obj=load_json(dest)
            before=obj["editorials"]
            after=[e for e in before if not e.get("source","").startswith("official_pdf_")]
            after.append(part)
            save_json(dest,dict(problem_id=pid,editorials=after,status="available"))
            fixed+=1
    except Exception as e: failures.append(dict(contest_id=cid,error=str(e),url=url))
save_json(ROOT/"pdf_repair_summary.json",dict(refreshed_problem_editorials=fixed,errors=failures))
print(json.dumps(dict(refreshed_problem_editorials=fixed,errors=failures),ensure_ascii=True),flush=True)
