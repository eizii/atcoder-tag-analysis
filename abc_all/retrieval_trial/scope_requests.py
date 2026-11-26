"""Apply V3 editorial scope plus an additional PDF heading guard to judge inputs.

Original corpus is preserved. Quarantined sources are listed as metadata, never
silently supplied as target evidence. Generated retrieval results are unchanged.
"""
import argparse, hashlib, json, sys, re, unicodedata
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from generate import load_unlabelled, scoped_editorial, shared_body_keys

def pdf_target_scope(e, p):
    """Recognize Japanese/English PDF headings missed by legacy V3 filters."""
    text=e.get('text','')
    if not re.search(r'\.pdf(?:$|\?)', e.get('url',''), re.I): return e, []
    pattern=re.compile(r'^\s*(?:(?:Problem|問題)\s*([A-H])\s*[:：.．\-–－]?\s*([^\n]*)|([A-H])\s*[:：.．\-–－]\s*([^\n]*))',re.M|re.I)
    heads=list(pattern.finditer(text))
    if not heads:return e, []
    norm=lambda s:re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).lower()
    title=norm(p['title'])
    matches=[h for h in heads if title and title in norm(h.group(2) or h.group(4) or '')]
    if matches:
        # Score tables can repeat task titles before the actual solution.
        target=matches[-1]; start=target.start(); end=next((h.start() for h in heads if h.start()>start),len(text))
    else:
        target=next((h for h in heads if (h.group(1) or h.group(3)).upper()==p['problem_index']),None)
        if target:start=target.start();end=next((h.start() for h in heads if h.start()>start),len(text))
        else:start=0;end=heads[0].start()
    if start==0 and end==len(text):return e, []
    return dict(e,text=text[start:end],codes=[]),[dict(reason='judge_pdf_target_heading_guard',excluded_chars=len(text)-(end-start))]

def scoped_sources():
    manifest, docs, _, supplements = load_unlabelled()
    shared = shared_body_keys(docs)
    result = {}
    for p in manifest['problems']:
        pid = p['problem_id']; d = docs[pid]
        replacement = {e['url']: e for e in supplements.get(pid, [])}
        es = [replacement.pop(e.get('url'), e) for e in d['editorials']]
        es.extend(replacement.values())
        sources = [dict(source_id='statement', url=p['url'], text=d['statement'], codes=[])]
        excluded = []
        for j, e in enumerate(es):
            raw = e.get('text', ''); sid = f'editorial_{j}'
            key = (e.get('url', ''), hashlib.sha256(raw.encode()).hexdigest())
            exact = e.get('source', '').startswith('official_pdf_') and raw.splitlines() and raw.splitlines()[0].strip() == p['title'].strip()
            if key in shared and not exact:
                excluded.append(dict(source_id=sid, url=e.get('url'), reason='shared_unsegmented_editorial'))
                continue
            guarded, audit = pdf_target_scope(e, p)
            text, codes, legacy_audit = scoped_editorial(guarded, shared, p)
            audit.extend(legacy_audit)
            if text.strip():
                sources.append(dict(source_id=sid, url=e.get('url') or p['url'], text=text, codes=codes, scope_policy='retrieval_v3_plus_judge_pdf_heading_guard'))
            excluded.extend(dict(source_id=sid, reason=a['reason']) for a in audit)
        result[pid] = (sources, excluded)
    return result

def main():
    a = argparse.ArgumentParser(); a.add_argument('--input', type=Path, required=True); a.add_argument('--output', type=Path, required=True); args = a.parse_args()
    sources = scoped_sources(); n = 0
    with args.input.open(encoding='utf-8') as src, args.output.open('w', encoding='utf-8') as dest:
        for line in src:
            r = json.loads(line); payload = json.loads(r['messages'][1]['content'])
            extra=' reviewedとする場合は全候補を採用またはrejectedへ記載してください。missing_conceptsが空でなければcandidate_insufficient=trueにしてください。'
            if extra not in r['messages'][0]['content']:r['messages'][0]['content']+=extra
            payload['source_texts'], payload['source_scope_exclusions'] = sources[r['custom_id']]
            by_source={s['source_id']:s['text'] for s in payload['source_texts']}
            for candidate in payload['candidates']:
                hint=candidate.get('retrieval_evidence',{})
                if hint.get('text') not in by_source.get(hint.get('source_id'),''):
                    candidate['retrieval_evidence']=dict(excluded=True,reason='not_in_judge_scoped_source')
                # Rule excerpts are normalized hints, not admissible quotes.
                candidate['rule_evidence']=[dict(h,quote_admissible=False) for h in candidate.get('rule_evidence',[]) if h['source_id'] in by_source]
            payload['source_policy'] = 'Only scoped source_texts are admissible quotes. Exclusions can reduce evidence; defer when insufficient.'
            r['messages'][1]['content'] = json.dumps(payload, ensure_ascii=False)
            dest.write(json.dumps(r, ensure_ascii=False) + '\n'); n += 1
    print(json.dumps(dict(scoped_requests=n, output=str(args.output))))
if __name__ == '__main__': main()
