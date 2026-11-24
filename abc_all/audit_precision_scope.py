import json,re,collections
from pathlib import Path
from precision_policy import scoped_editorial,PDF_HEADER
R=Path(__file__).resolve().parent
ds=list(map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8')))
for d in ds:
 for e in d['editorials']:
  if e.get('source','').startswith('official_pdf_'):
   text,codes,audit=scoped_editorial(e,{},d)
   if audit: print(d['problem_id'],d['title'],len(e['text']),'->',len(text),[(a['reason'],a.get('context','')[:75]) for a in audit])
