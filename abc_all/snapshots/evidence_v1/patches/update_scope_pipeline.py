from pathlib import Path
p=Path(__file__).parent/"tag_all.py"
s=p.read_text(encoding="utf-8")
s=s.replace('import csv\n','import argparse\nimport csv\n',1)
s=s.replace('from collect_statements import ROOT, load_json, save_json','from collect_statements import ROOT, load_json, save_json\nfrom evidence_scope import (NEGATIVE, POLICY_VERSION, shared_body_keys, source_scope, local_context, rejection_reason, executable_code)')
s=s.replace('VERSION="abc-all-266-evidence-v1"','VERSION="abc-all-266-evidence-v2"')
start=s.index('NEGATIVE=re.compile(')
end=s.index('REFERENCE=',start)
s=s[:start]+s[end:]
a=s.index('                left=max(text.rfind(')
b=s.index('    filtered=[]',a)
s=s[:a]+'''                context=local_context(text,m.start(),m.end())
                hit=dict(tag_id=tid,matched=alias,start=m.start(),end=m.end(),context=context)
                reason=rejection_reason(tid,context)
                if reason: rejected.append(dict(hit,reason=reason))
                else: occurrences.append(hit)
'''+s[b:]
s=s.replace('def build():','def build(uniform=False, output_dir="output_v2"):')
s=s.replace('    baseline=baseline_labels(taxonomy)','    baseline={} if uniform else baseline_labels(taxonomy)')
s=s.replace('    manual=load_json(manual_path) if manual_path.exists() else {}','    manual=load_json(manual_path) if manual_path.exists() and not uniform else {}')
needle='    for p in manifest["problems"]:\n'
s=s.replace(needle,'    shared=shared_body_keys(source_docs)\n    source_audits=[]\n'+needle,1)
s=s.replace('        labels={}\n        rejected=[]','''        scoped_eds=[]
        for editorial in eds:
            scoped_text,scoped_codes,audits=source_scope(editorial,shared)
            source_audits.extend(dict(problem_id=pid,**a) for a in audits)
            scoped_eds.append(dict(editorial,text=scoped_text,codes=scoped_codes))
        labels={}
        rejected=[]''',1)
s=s.replace('        for e in eds:\n','        for e in scoped_eds:\n')
s=s.replace('reason="negative_or_infeasible_context"','reason=hit["reason"]')
# dict(hit,reason=...) is fine, override same key using constructor keyword.
a=s.index('            code="\\n".join',0) if '            code="\\n".join' in s else s.index('            code="\\\\n".join')
# Actual source text has backslash-n, handled below with a block slice.
b=s.index('        # Descriptions of actual solution steps',a)
s=s[:a]+'''            raw_code="\\n".join(e.get("codes",[]))
            code=executable_code(raw_code)
            for tid,regex in CODE_RULES.items():
                m=re.search(regex,code)
                if m:
                    add(tid,dict(method="editorial_code_rule",role="unresolved",validation_status="not_reviewed",url=e.get("url",""),source=e.get("source",""),matched=m.group(),context=code[max(0,m.start()-50):m.end()+90]))
                elif re.search(regex,raw_code):
                    rejected.append(dict(tag_id=tid,matched=re.search(regex,raw_code).group(),url=e.get("url",""),reason="code_not_in_directly_executable_scope",context="Helper/library declaration or unscoped snippet; not sufficient as sole evidence."))
'''.replace('raw_code="\n".join','raw_code="\\n".join')+s[b:]
a=s.index('                m=re.search(pattern,text)')
b=s.index('        # A/B elementary',a)
s=s[:a]+'''                for m in re.finditer(pattern,text):
                    context=local_context(text,m.start(),m.end())
                    reason=rejection_reason(tid,context)
                    evidence=dict(tag_id=tid,matched=m.group(),context=context,url=e.get("url",""))
                    if not reason:
                        add(tid,dict(method="solution_description_rule",role="unresolved",validation_status="not_reviewed",source=e.get("source",""),**{k:v for k,v in evidence.items() if k!="tag_id"}))
                    else:
                        rejected.append(dict(evidence,reason=reason))
'''+s[b:]
# Title-only names are candidate hints rather than evidence of solution use.
a=s.index('        # The problem title')
b=s.index('        if pid in manual:',a)
s=s[:a]+'''        # A name in a title can be a metaphor or the topic of the input.
        # Keep it as an audit hint; require evidence of solution use.
        title_hits,_=named_evidence(p["title"],rules)
        for hit in title_hits:
            if hit["tag_id"] in labels: continue
            rejected.append(dict(hit,url=p["url"],reason="title_only_not_solution_evidence"))
'''+s[b:]
s=s.replace('    out=ROOT/"output"','    out=ROOT/output_dir')
s=s.replace('    out.mkdir(exist_ok=True)','    out.mkdir(parents=True,exist_ok=True)')
s=s.replace('    save_json(out/"summary.json",stats)','''    stats.update(annotation_policy="uniform_automatic" if uniform else "hybrid_with_prior_and_assistant_reviews",
        evidence_scope_policy=POLICY_VERSION, shared_unsegmented_source_bodies=len(shared),
        scoped_source_exclusions=len(source_audits),
        source_corpus_sha256=hashlib.sha256(snapshot_file.read_bytes()).hexdigest())
    csv_write(out/"source_scope_audit.csv",["problem_id","reason","url","problem_ids","context","note","excluded_chars"],source_audits)
    rejection_rows=[dict(problem_id=r["problem_id"],**hit) for r in records for hit in r["rejected_name_hits"]]
    csv_write(out/"rejected_evidence.csv",["problem_id","tag_id","matched","reason","context","url","start","end"],rejection_rows)
    save_json(out/"summary.json",stats)''')
s=s.replace('if __name__=="__main__": build()','''if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--uniform",action="store_true",help="No inherited tags or targeted manual reviews; identical rules for all tasks.")
    parser.add_argument("--output-dir",default="output_v2")
    args=parser.parse_args()
    build(args.uniform,args.output_dir)''')
p.write_text(s,encoding="utf-8")
