"""Collect every completed ABC statement, without difficulty filtering or model APIs."""
import argparse
import hashlib
import json
import math
import pathlib
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from bs4 import BeautifulSoup

ROOT=pathlib.Path(__file__).resolve().parent

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))

def save_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+".tmp")
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(p)

def manifest():
    contests=load_json(ROOT/"metadata/contests.json")
    cutoff=datetime.fromisoformat("2026-11-05T23:59:59+09:00").timestamp()
    abc={c["id"]:c for c in contests if re.fullmatch(r"abc[0-9]+",c["id"]) and c["start_epoch_second"]+c["duration_second"]<=cutoff}
    problems={p["id"]:p for p in load_json(ROOT/"metadata/problems.json")}
    models=load_json(ROOT/"metadata/problem-models.json")
    grouped={}
    for pair in load_json(ROOT/"metadata/contest-problem.json"):
        cid=pair["contest_id"]
        if cid not in abc: continue
        pid=pair["problem_id"]
        p=problems[pid]
        raw=models.get(pid,{}).get("difficulty")
        difficulty=None if raw is None else round(raw if raw>=400 else 400*math.exp(raw/400-1))
        grouped.setdefault(pid,dict(problem_id=pid,title=p.get("name",p["title"]),contests=[],difficulty=difficulty,raw_difficulty=raw))
        grouped[pid]["contests"].append(dict(contest_id=cid,problem_index=pair["problem_index"]))
    items=[]
    for p in grouped.values():
        p["contests"].sort(key=lambda a:(abc[a["contest_id"]]["start_epoch_second"],a["problem_index"]))
        p.update(p["contests"][0])
        p["url"]="https://atcoder.jp/contests/{contest_id}/tasks/{problem_id}".format(**p)
        items.append(p)
    items.sort(key=lambda p:(abc[p["contest_id"]]["start_epoch_second"],p["problem_index"]))
    out=dict(as_of="2026-11-05",source="AtCoder Problems public metadata",difficulty_filter=None,
        contest_count=len(abc),problem_count=len(items),contests=sorted(abc.values(),key=lambda c:c["start_epoch_second"]),problems=items,
        metadata_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/"metadata").glob("*.json")})
    save_json(ROOT/"manifest.json",out)
    return out

def parse_print(html,expected):
    soup=BeautifulSoup(html,"html.parser")
    found={}
    expected_indices={p["problem_index"]:p for p in expected}
    nodes=soup.select("#task-statement")
    for node in nodes:
        # Older tasks nest a second element with the same id. Parse the outer task once.
        if node.find_parent(id="task-statement") is not None: continue
        title=node.find_previous("span",class_="h2")
        if title is None: raise ValueError("Task title missing")
        label=title.get_text(" ",strip=True)
        match=re.match(r"^(.+?)\s*[-.\u2013]\s*(.+)$",label)
        if not match: raise ValueError("Unrecognized task title: "+label)
        index=match.group(1).strip()
        if index not in expected_indices: raise ValueError("Unexpected task index: "+index)
        info=expected_indices[index]
        ja=node.select_one(".lang-ja")
        language="ja"
        if ja is None:
            if node.select_one(".lang-en") is not None: raise ValueError("Japanese statement missing")
            ja=node
        for unwanted in ja.select("script, style, .lang-en"):
            unwanted.decompose()
        text=ja.get_text(" ",strip=True)
        if len(text)<30: raise ValueError("Statement unexpectedly short: "+info["problem_id"])
        sections=[]
        for part in ja.select(".part"):
            heading=part.find(["h2","h3","h4"])
            sections.append({"heading":heading.get_text(" ",strip=True) if heading else "", "text":part.get_text(" ",strip=True)})
        pid=info["problem_id"]
        if pid in found: raise ValueError("Duplicate task: "+pid)
        found[pid]=dict(info,statement=text,sections=sections,language=language,statement_source="official_tasks_print",
            source_url="https://atcoder.jp/contests/"+info["contest_id"]+"/tasks_print?lang=ja",
            retrieved_at=datetime.now(timezone.utc).isoformat(),statement_sha256=hashlib.sha256(text.encode()).hexdigest(),editorials=[])
    if set(found)!={p["problem_id"] for p in expected}:
        raise ValueError("Printed tasks differ from metadata: "+str(sorted({p["problem_id"] for p in expected}-set(found))))
    return found

class Client:
    def __init__(self): self.last=0
    def get(self,url):
        for attempt in range(3):
            time.sleep(max(0,1.25-(time.monotonic()-self.last)))
            self.last=time.monotonic()
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"AtCompassResearch/1.0"})
                with urllib.request.urlopen(req,timeout=45) as response: return response.read()
            except urllib.error.HTTPError as e:
                if e.code in (401,403): raise
                if e.code not in (429,500,502,503,504) or attempt==2: raise
                time.sleep(min(30,max(5,int(e.headers.get("Retry-After","5")))))
            except (OSError,TimeoutError):
                if attempt==2: raise
                time.sleep(3*(attempt+1))
        raise RuntimeError("Request failed")

def collect(data,limit=None):
    by_contest={}
    for p in data["problems"]: by_contest.setdefault(p["contest_id"],[]).append(p)
    client=Client()
    errors=[]
    processed=0
    successes=0
    consecutive_errors=0
    for cid,expected in by_contest.items():
        if limit is not None and processed>=limit: break
        cache=ROOT/"cache"/(cid+"_tasks.html")
        if cache.exists(): raw=cache.read_bytes()
        else:
            try: raw=client.get("https://atcoder.jp/contests/"+cid+"/tasks_print?lang=ja")
            except Exception as e:
                errors.append({"contest_id":cid,"error":str(e)})
                consecutive_errors+=1
                print(json.dumps(errors[-1],ensure_ascii=True),flush=True)
                if consecutive_errors>=3: break
                continue
            cache.parent.mkdir(parents=True,exist_ok=True)
            cache.write_bytes(raw)
        try:
            parsed=parse_print(raw,expected)
            for pid,item in parsed.items(): save_json(ROOT/"problems"/(pid+".json"),item)
            successes+=len(parsed)
            consecutive_errors=0
        except Exception as e:
            errors.append({"contest_id":cid,"error":str(e)})
            print(json.dumps(errors[-1],ensure_ascii=True),flush=True)
        processed+=1
        if processed%10==0 or processed==len(by_contest):
            print(json.dumps({"contests_processed":processed,"contests_total":len(by_contest),"problems_written":successes,"last":cid,"errors":len(errors)}),flush=True)
        save_json(ROOT/"collection_progress.json",dict(contests_processed=processed,contests_total=len(by_contest),problems_written=successes,errors=errors,updated_at=datetime.now(timezone.utc).isoformat()))
    save_json(ROOT/"collection_errors.json",errors)
    print(json.dumps({"finished":True,"contests_processed":processed,"problems_written":successes,"errors":len(errors)}),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest-only",action="store_true")
    parser.add_argument("--limit",type=int)
    args=parser.parse_args()
    data=manifest()
    print(json.dumps({"contests":data["contest_count"],"problems":data["problem_count"]}),flush=True)
    if not args.manifest_only: collect(data,args.limit)
