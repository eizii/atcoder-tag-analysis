"""Read public AtCoder editorials and repair short cached extracts in a separate overlay."""
import argparse,hashlib,json,re,time,urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parent

def parse(raw,url):
 soup=BeautifulSoup(raw,'html.parser')
 # AtCoder stores prose and examples together in the language-specific editorials.
 heading=soup.select_one('#main-container h2.mt-1') or soup.select_one('#main-container h2')
 task_ids=[link['href'].rstrip('/').split('/')[-1] for link in heading.select('a[href*="/tasks/"]')] if heading else []
 official=bool(heading and heading.parent.select_one('.label') and '公式' in heading.parent.select_one('.label').get_text())
 node=soup.select_one('#editorial-body')
 if node is None:
  heading=soup.select_one('#main-container h2') or soup.select_one('#main-container h3')
  node=heading.parent if heading else None
  if heading:heading.decompose()
 if node is None:raise ValueError('Missing editorial body')
 for item in node.select('script,style,.a2a_kit,.label,.btn,time'):item.decompose()
 codes=[pre.get_text('\n',strip=False) for pre in node.select('pre')]
 for pre in node.select('pre'):pre.decompose()
 text=node.get_text(' ',strip=True)
 return dict(url=url,text=text,codes=codes,source='official_web_refetched_v3' if official else 'user_web_refetched_v3',official_status='official' if official else 'user',task_ids=task_ids,text_sha256=hashlib.sha256(text.encode()).hexdigest())

def main():
 p=argparse.ArgumentParser();p.add_argument('--one',action='store_true');p.add_argument('--offline',action='store_true');p.add_argument('--threshold',type=int,default=160);a=p.parse_args()
 cache=R/'precision_cache';cache.mkdir(exist_ok=True)
 ds=list(map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8')))
 todo={}
 for d in ds:
  for e in d['editorials']:
   url=e.get('url') or ''
   if len(e['text'])<a.threshold and re.fullmatch(r'https://atcoder.jp/contests/[a-z0-9_]+/editorial/[0-9]+',url):todo.setdefault(url,[]).append(d['problem_id'])
 if a.one:todo={'https://atcoder.jp/contests/abc209/editorial/2229':['abc209_d']}
 overlay=[];errors=[]
 dest=R/('precision_sources_probe.jsonl' if a.one else 'precision_sources.jsonl')
 for n,(url,pids) in enumerate(sorted(todo.items())):
  path=cache/('editorial_'+url.rsplit('/',1)[-1]+'.html')
  try:
   if not path.exists():
    if a.offline:raise ValueError('Missing cached HTML')
    request=urllib.request.Request(url+'?lang=ja',headers={'User-Agent':'AtCoderTagReview/3 (public editorial research)'})
    raw=urllib.request.urlopen(request,timeout=25).read();path.write_bytes(raw);time.sleep(.3)
   else:raw=path.read_bytes()
   e=parse(raw,url)
   if len(e['text'])<20:raise ValueError('Parsed text too short')
   for pid in pids:
    if pid not in e['task_ids']:
     errors.append(dict(url=url,problem_id=pid,error='editorial_task_link_mismatch'));continue
    overlay.append(dict(problem_id=pid,editorial=e,retrieved_at='2026-11-23',raw_sha256=hashlib.sha256(raw).hexdigest()))
   if (n+1)%25==0 or a.one:print(json.dumps(dict(processed=n+1,total=len(todo),chars=len(e['text'])),ensure_ascii=False),flush=True)
  except Exception as exc:errors.append(dict(url=url,error=str(exc)))
  dest.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in overlay),encoding='utf-8')
 (R/'precision_fetch_report.json').write_text(json.dumps(dict(requested_urls=len(todo),overlay_rows=len(overlay),errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
 print('DONE',len(overlay),len(errors),flush=True)
if __name__=='__main__':main()
