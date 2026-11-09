import json,re
from collect_statements import ROOT,load_json
from collect_editorials import pdf_fragments
m=load_json(ROOT/"manifest.json")
for cid in ["abc015","abc101"]:
    ps=[p for p in m["problems"] if p["contest_id"]==cid]
    raw=(ROOT/"cache"/(cid+"_editorial.pdf")).read_bytes()
    got=pdf_fragments(raw,ps,"source",cid)
    print(json.dumps({"contest":cid,"fragments":{p:{"length":len(e["text"]),"first":e["text"][:100],"last":e["text"][-100:]} for p,e in got.items()}},ensure_ascii=False))
