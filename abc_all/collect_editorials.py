"""Reuse local editorials and fetch missing public editorials. No AI APIs."""
import hashlib
import json
import pathlib
import re
import sys
import unicodedata
from urllib.parse import urljoin, urlparse, parse_qs
import fitz
from bs4 import BeautifulSoup
from collect_statements import ROOT, Client, load_json, save_json

WORKSPACE=ROOT.parent
SOURCES=[WORKSPACE/"repository_update/ac_analyze_test",WORKSPACE/"validation_sources/ac_analyze_test"]

def prefill(data):
    wanted={p["problem_id"] for p in data["problems"]}
    found={pid:[] for pid in wanted}
    for source in SOURCES:
        for file in sorted((source/"data").glob("abc*/*.json")):
            obj=load_json(file)
            pid=obj.get("task_id")
            if pid not in wanted: continue
            for e in obj.get("editorials",[]):
                if len(e.get("text","").strip())<20: continue
                digest=hashlib.sha256(e["text"].encode()).hexdigest()
                if any(x["text_sha256"]==digest or (e.get("url") and x.get("url")==e["url"]) for x in found[pid]): continue
                found[pid].append(dict(e,text_sha256=digest,source="existing_team_cache",source_path=file.relative_to(WORKSPACE).as_posix(),official_status="not_recorded"))
    for pid,entries in found.items():
        dest=ROOT/"editorials"/(pid+".json")
        if dest.exists():
            old=load_json(dest)
            for e in old.get("editorials",[]):
                if e.get("source","").startswith("official_pdf_"): continue
                if not any(x.get("text_sha256")==e.get("text_sha256") for x in entries): entries.append(e)
        save_json(dest,dict(problem_id=pid,editorials=entries,status="available" if entries else "missing"))
    return found

def cached_get(client,key,url):
    file=ROOT/"cache"/key
    if not file.exists(): file.write_bytes(client.get(url))
    return file.read_bytes()

def links_for_tasks(raw):
    soup=BeautifulSoup(raw,"html.parser")
    tasks={}
    for section in soup.select(".editorial-section"):
        heading=section.find_previous("h3")
        task=heading.select_one('a[href*="/tasks/"]') if heading else None
        if task is None: continue
        pid=task["href"].rstrip("/").split("/")[-1]
        links=[]
        for li in section.select("li"):
            if "lang-other" in li.get("class",[]): continue
            link=li.select_one('a[href*="/editorial/"]')
            if link is None or not re.search(r"/editorial/[0-9]+$",link.get("href","")): continue
            label=li.select_one(".label")
            official=label is not None and "公式" in label.get_text()
            links.append(dict(url=urljoin("https://atcoder.jp",link["href"]),official=official))
        tasks[pid]=sorted(links,key=lambda e:not e["official"])
    pdfs=[]
    main=soup.select_one("#main-container") or soup
    for a in main.select("a[href]"):
        url=urljoin("https://atcoder.jp",a.get("href",""))
        parsed=urlparse(url)
        if parsed.path=="/jump":
            original=parse_qs(parsed.query).get("url",[""])[0]
            legacy=re.match(r"https?://([a-z]+[0-9]+)\.contest\.atcoder\.jp/data/[a-z]+/[0-9]+/editorial\.pdf$",original)
            if legacy: url="https://img.atcoder.jp/"+legacy.group(1)+"/editorial.pdf"
        url=url.replace("https://atcoder.jp/img/","https://img.atcoder.jp/").replace("http://atcoder.jp/img/","https://img.atcoder.jp/")
        if re.search(r"\.pdf(?:$|\?)",url,re.I) and urlparse(url).hostname in {"atcoder.jp","img.atcoder.jp"}:
            if url not in pdfs: pdfs.append(url)
    return tasks,pdfs

def parse_editorial(raw,url,official):
    soup=BeautifulSoup(raw,"html.parser")
    main=soup.select_one("#main-container")
    if main is None: raise ValueError("Editorial main missing")
    h3=main.select_one("h2.mt-1") or main.select_one("h2") or main.select_one("h3")
    if h3 is None: raise ValueError("Editorial heading missing")
    content=h3.find_next_sibling("div")
    if content is None: raise ValueError("Editorial body missing")
    for detail in content.select("details"):
        summary=detail.select_one("summary")
        if summary and "初心者の方へ" in summary.get_text(): detail.decompose()
    codes=[p.get_text("\n",strip=False) for p in content.select("pre")]
    for code in content.select("pre"): code.decompose()
    for junk in content.select("script,style"): junk.decompose()
    text=content.get_text(" ",strip=True)
    if len(text)<20: raise ValueError("Editorial body too short")
    return dict(url=url,text=text,codes=codes,source="official_web" if official else "user_web",official_status="official" if official else "user",text_sha256=hashlib.sha256(text.encode()).hexdigest())

def normalized(text):
    return re.sub(r"[^a-z0-9\u3040-\u30ff\u3400-\u9fff]","",unicodedata.normalize("NFKC",text).lower())

def pdf_fragments(raw,expected,url,cid):
    doc=fitz.open(stream=raw,filetype="pdf")
    pages=[p.get_text(sort=True) for p in doc]
    text="\n\f\n".join(pages)
    (ROOT/"pdf_text").mkdir(exist_ok=True)
    (ROOT/"pdf_text"/(cid+".txt")).write_text(text,encoding="utf-8")
    lines=text.splitlines(keepends=True)
    offset=0
    title_starts={}
    boundaries=[]
    for line in lines:
        clean=normalized(line)
        for p in expected:
            name=normalized(p["title"])
            if name and len(name)>=3 and name in clean and p["problem_id"] not in title_starts:
                title_starts[p["problem_id"]]=offset
        header=re.match(r"^\s*(?:問題\s*)?([A-H])(?:[.:：．]|\s+[-–－]|\s*問題|\s*問)",line)
        if header: boundaries.append((offset,header.group(1)))
        offset+=len(line)
    joint=any(not p["problem_id"].startswith(cid+"_") for p in expected)
    result={}
    for p in expected:
        pid=p["problem_id"]
        index=p["problem_index"]
        start=title_starts.get(pid)
        method="title_anchored"
        if start is None and not joint:
            start=next((pos for pos,letter in boundaries if letter==index),None)
            method="letter_anchored"
        if start is None: continue
        next_titles=[v for key,v in title_starts.items() if key!=pid and v>start]
        next_headers=[pos for pos,letter in boundaries if pos>start and letter>index]
        end=min(next_titles+next_headers+[len(text)])
        fragment=text[start:end].strip()
        if len(fragment)<50: continue
        result[pid]=dict(url=url,text=fragment,codes=[],source="official_pdf_"+method,official_status="official",extraction_needs_review=True,text_sha256=hashlib.sha256(fragment.encode()).hexdigest())
    return result

def collect():
    data=load_json(ROOT/"manifest.json")
    found=prefill(data)
    by_contest={}
    for p in data["problems"]: by_contest.setdefault(p["contest_id"],[]).append(p)
    client=Client()
    errors=[]
    processed=0
    for cid,expected in by_contest.items():
        missing=[p for p in expected if not found[p["problem_id"]]]
        if not missing: continue
        try:
            raw=cached_get(client,cid+"_editorial.html","https://atcoder.jp/contests/"+cid+"/editorial?lang=ja")
            task_links,pdf_urls=links_for_tasks(raw)
            for url in pdf_urls[:1]:
                try:
                    pdf_raw=cached_get(client,cid+"_editorial.pdf",url)
                    if not pdf_raw.startswith(b"%PDF-"):
                        pdf_raw=client.get(url)
                        (ROOT/"cache"/(cid+"_editorial.pdf")).write_bytes(pdf_raw)
                    if not pdf_raw.startswith(b"%PDF-"): raise ValueError("Expected PDF")
                    fragments=pdf_fragments(pdf_raw,expected,url,cid)
                    for pid,fragment in fragments.items():
                        if not found[pid]: found[pid].append(fragment)
                except Exception as e: errors.append(dict(contest_id=cid,stage="pdf",error=str(e)))
            for p in missing:
                pid=p["problem_id"]
                if found[pid]: continue
                for link in task_links.get(pid,[])[:2]:
                    try:
                        eid=link["url"].rsplit("/",1)[-1]
                        page=cached_get(client,"editorial_"+eid+".html",link["url"]+"?lang=ja")
                        entry=parse_editorial(page,link["url"],link["official"])
                        found[pid].append(entry)
                        break
                    except Exception as e: errors.append(dict(problem_id=pid,stage="web",url=link["url"],error=str(e)))
            for p in expected:
                pid=p["problem_id"]
                save_json(ROOT/"editorials"/(pid+".json"),dict(problem_id=pid,editorials=found[pid],status="available" if found[pid] else "missing"))
        except Exception as e:
            errors.append(dict(contest_id=cid,stage="index",error=str(e)))
        processed+=1
        progress=dict(contests_with_missing_processed=processed,problems_with_editorial=sum(bool(v) for v in found.values()),total_problems=len(found),errors=len(errors),last=cid)
        save_json(ROOT/"editorial_progress.json",progress)
        save_json(ROOT/"editorial_errors.json",errors)
        if processed%5==0: print(json.dumps(progress),flush=True)
    print(json.dumps(dict(finished=True,problems_with_editorial=sum(bool(v) for v in found.values()),total_problems=len(found),errors=len(errors))),flush=True)

if __name__=="__main__": collect()
