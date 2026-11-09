import json, pathlib, time, urllib.request
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parent
for name,url in [("abc001_tasks", "https://atcoder.jp/contests/abc001/tasks_print?lang=ja"),("abc482_tasks","https://atcoder.jp/contests/abc482/tasks_print?lang=ja"),("abc482_editorial","https://atcoder.jp/contests/abc482/editorial?lang=ja")]:
    req=urllib.request.Request(url,headers={"User-Agent":"AtCompassResearch/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r: raw=r.read()
        (ROOT / (name+".html")).write_bytes(raw)
        soup=BeautifulSoup(raw,"html.parser")
        print(json.dumps({"name":name,"bytes":len(raw),"statements":len(soup.select("#task-statement")),"h2":[x.get_text(" ",strip=True) for x in soup.select("h2")[:10]],"editorial_links":[{"text":a.get_text(" ",strip=True),"href":a.get("href")} for a in soup.select("a[href]") if "/editorial/" in a.get("href","")][:15]},ensure_ascii=True),flush=True)
    except Exception as e: print(json.dumps({"name":name,"error":str(e)}),flush=True)
    time.sleep(1.2)
