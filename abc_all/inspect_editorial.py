from collect_statements import ROOT,Client
from bs4 import BeautifulSoup
import json
client=Client()
for cid in ["abc001","abc050","abc100","abc175"]:
    raw=client.get("https://atcoder.jp/contests/"+cid+"/editorial?lang=ja")
    dest=ROOT/"cache"/(cid+"_editorial.html")
    dest.write_bytes(raw)
    soup=BeautifulSoup(raw,"html.parser")
    main=soup.select_one("#main-container")
    print(json.dumps({"contest":cid,"text":main.get_text(" ",strip=True)[:500],"pdfs":[a.get("href") for a in main.select("a[href]") if ".pdf" in a.get("href","")],"sections":len(main.select(".editorial-section"))},ensure_ascii=True),flush=True)
