"""Produce an auditable, provisional 266-tag dataset, without paid/model APIs."""
import csv
import hashlib
import json
import pathlib
import re
import unicodedata
from collections import Counter, defaultdict
from collect_statements import ROOT, load_json, save_json

WORKSPACE=ROOT.parent
VERSION="abc-all-266-evidence-v1"

CODE_RULES={
    "T001":r"(?i)fenwick(?:_tree)?|binary_indexed_tree",
    "T002":r"(?i)lazy_?seg(?:ment)?_?tree",
    "T003":r"(?i)(?:atcoder::)?segtree\s*[<(]|segment_?tree",
    "T005":r"(?i)union_?find|disjoint_?set|(?:atcoder::)?dsu\s*[<(]",
    "T007":r"(?:std::)?deque\s*[<(]|from collections import[^\n]*deque",
    "T008":r"(?:std::)?(?:unordered_)?map\s*<|(?:collections\.)?Counter\(",
    "T009":r"(?:std::)?multiset\s*<",
    "T010":r"priority_queue\s*<|heapq\.|heappush\(|heappop\(",
    "T011":r"(?<![A-Za-z_])(?:std::)?queue\s*<",
    "T012":r"(?:std::)?(?:unordered_)?set\s*<|(?<![A-Za-z_])set\(",
    "T013":r"(?:std::)?stack\s*<",
    "T064":r"(?:std::)?(?:lower_bound|upper_bound)\s*\(|bisect_(?:left|right)\s*\(",
    "T069":r"suffix_array\(",
    "T071":r"z_algorithm\(",
    "T077":r"(?<![A-Za-z_])(?:std::)?(?:stable_)?sort\s*\(|sorted\s*\(|\.sort\s*\(",
    "T117":r"__builtin_popcount|\.bit_count\(",
    "T132":r"(?:atcoder::)?convolution(?:_ll)?\(",
    "T169":r"two_sat\s*[<(]",
    "T170":r"(?i)aho_?corasick",
    "T176":r"pow_mod\s*\(|mod_pow\s*\(|binpow\s*\(",
    "T187":r"(?i)dijkstra\s*\(",
    "T196":r"(?<![A-Za-z_])(?:fft|ntt)\s*\(",
    "T208":r"(?i)warshall_floyd|floyd_warshall",
    "T032":r"mf_graph\s*<",
    "T229":r"(?i)dinic",
    "T236":r"\.inv\s*\(|mod_inv\s*\(|inv_mod\s*\(",
    "T253":r"(?i)eratosthenes|prime_sieve",
}

# Exclude a generic name when it is only part of a longer, specific name.
OVERLAP_PARENTS={"T002":{"T003"},"T095":{"T004"},"T089":{"T070"},"T144":{"T066"},"T046":{"T067"},"T194":{"T097"},"T087":{"T132"},"T103":{"T132"},"T108":{"T132"},"T109":{"T132"},"T225":{"T054"},"T226":{"T054"},"T227":{"T054"}}
NEGATIVE=re.compile(r"使え(?:ない|ません)|使うこと(?:は|が)できない|適用でき(?:ない|ません)|間に合(?:わない|いません)|時間制限(?:を|に).*超|TLE|実行時間制限に|計算量が大きすぎ|不適切|採用しません|cannot be used|too slow",re.I)
REFERENCE=re.compile(r"(?:参考文献|参考資料|References|Related problems)\s*[:：]",re.I)

def normalize(text):
    return re.sub(r"\s+"," ",unicodedata.normalize("NFKC",text))

def alias_regex(alias):
    text=normalize(alias)
    escaped=re.escape(text).replace(r"\ ",r"\s*")
    left=r"(?<![A-Za-z0-9_])" if re.match(r"[A-Za-z0-9]",text) else ""
    right=r"(?![A-Za-z0-9_])" if re.search(r"[A-Za-z0-9]$",text) else ""
    return re.compile(left+escaped+right,re.I)

def named_evidence(text,rules):
    text=normalize(text)
    text=re.sub(r"https?://[^\s]+","",text)
    cutoff=REFERENCE.search(text)
    if cutoff: text=text[:cutoff.start()]
    occurrences=[]
    rejected=[]
    for tid,aliases in rules.items():
        for alias,regex in aliases:
            for m in regex.finditer(text):
                left=max(text.rfind("。",0,m.start()),text.rfind("\n",0,m.start()))+1
                ends=[x for x in [text.find("。",m.end()),text.find("\n",m.end())] if x>=0]
                right=min(ends) if ends else min(len(text),m.end()+160)
                context=text[max(left,m.start()-100):min(right,m.end()+160)].strip()
                hit=dict(tag_id=tid,matched=alias,start=m.start(),end=m.end(),context=context)
                if NEGATIVE.search(context): rejected.append(hit)
                else: occurrences.append(hit)
    filtered=[]
    for hit in occurrences:
        if any(hit["tag_id"] in OVERLAP_PARENTS.get(other["tag_id"],set()) and other["start"]<=hit["start"] and other["end"]>=hit["end"] for other in occurrences): continue
        filtered.append(hit)
    return filtered,rejected

def csv_write(path,headers,rows):
    with path.open("w",encoding="utf-8-sig",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=headers,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def baseline_labels(taxonomy):
    result=defaultdict(dict)
    source=WORKSPACE/"validation/revised/all_problems_tagged.csv"
    with source.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            if row["tag_id"] not in taxonomy: raise ValueError("Unknown baseline tag")
            result[row["problem_id"]][row["tag_id"]]=dict(method="prior_revised_dataset",role=row.get("validated_role","unreviewed"),
                validation_status=row.get("validation_status","not_reviewed"),evidence_urls=row.get("validation_evidence_urls","").split(" | ") if row.get("validation_evidence_urls") else [],
                note=row.get("note","") or "Inherited prior provisional tag; not independently validated.")
    return result

def build():
    manifest=load_json(ROOT/"manifest.json")
    taxonomy_list=load_json(ROOT/"taxonomy.json")
    taxonomy={t["tag_id"]:t["tag"] for t in taxonomy_list}
    if len(taxonomy)!=266: raise ValueError("Expected 266 tags")
    config=load_json(ROOT/"tag_rules.json")
    rules={tid:[(alias,alias_regex(alias)) for alias in names] for tid,names in config["aliases"].items()}
    baseline=baseline_labels(taxonomy)
    old_aliases=load_json(WORKSPACE/"tagging_data.json")["aliases"]
    canonical_names={name:tid for tid,name in taxonomy.items()}
    seed_outputs={}
    manual_path=ROOT/"semantic_reviews.json"
    manual=load_json(manual_path) if manual_path.exists() else {}
    rows=[]
    pairs=[]
    matrix=[]
    records=[]
    review_queue=[]
    tag_counts=Counter()
    methods=Counter()
    rejected_total=0
    corpus_missing=[]
    vocabulary_gaps=Counter()
    snapshot_file=ROOT/"corpus_sources.jsonl"
    source_docs={}
    if snapshot_file.exists():
        with snapshot_file.open(encoding="utf-8") as f: source_docs={r["problem_id"]:r for r in (json.loads(line) for line in f)}
    for p in manifest["problems"]:
        pid=p["problem_id"]
        doc_file=ROOT/"problems"/(pid+".json")
        if pid not in source_docs and not doc_file.exists():
            corpus_missing.append(pid)
            continue
        doc=source_docs[pid] if pid in source_docs else load_json(doc_file)
        editorial_file=ROOT/"editorials"/(pid+".json")
        eds=doc.get("editorials",[]) if pid in source_docs else load_json(editorial_file).get("editorials",[]) if editorial_file.exists() else []
        labels={}
        rejected=[]
        def add(tid,evidence):
            if tid not in taxonomy: raise ValueError("Tag outside taxonomy: "+tid)
            labels.setdefault(tid,[])
            signature=(evidence["method"],evidence.get("url",""),evidence.get("matched",""))
            if not any((e["method"],e.get("url",""),e.get("matched",""))==signature for e in labels[tid]): labels[tid].append(evidence)
        for tid,prior in baseline.get(pid,{}).items(): add(tid,prior)
        if pid not in baseline:
            for name in seed_outputs.get(pid,{}).get("tags",[]):
                num=old_aliases.get(name)
                if num is None and name in canonical_names: num=int(canonical_names[name][1:])
                if num: add("T%03d"%num,dict(method="prior_original_tag",role="unreviewed",validation_status="not_reviewed",matched=name))
                else: vocabulary_gaps[name]+=1
        for e in eds:
            found,excluded=named_evidence(e.get("text",""),rules)
            for hit in found:
                add(hit["tag_id"],dict(method="editorial_name_rule",role="unresolved",validation_status="not_reviewed",url=e.get("url",""),source=e.get("source",""),matched=hit["matched"],context=hit["context"]))
            for hit in excluded:
                rejected.append(dict(hit,url=e.get("url",""),reason="negative_or_infeasible_context"))
            code="\n".join(e.get("codes",[]))
            for tid,regex in CODE_RULES.items():
                m=re.search(regex,code)
                if m:
                    add(tid,dict(method="editorial_code_rule",role="unresolved",validation_status="not_reviewed",url=e.get("url",""),source=e.get("source",""),matched=m.group(),context=code[max(0,m.start()-50):m.end()+90]))
        # Descriptions of actual solution steps, retained as provisional evidence.
        description_rules={
            "T022":r"メモ化(?:再帰)?",
            "T065":r"(?:すべて|全て|全部)(?:の)?(?:組み合わせ|組合せ|場合|パターン|候補).{0,35}(?:試|調べ|列挙)|(?:二重|三重|多重)(?:の)?ループで",
            "T076":r"問題文(?:の|で)(?:通り|とおり)|そのまま(?:実装|実行|処理|行う)|順番に(?:処理|更新)|シミュレート",
            "T077":r"(?:小さい|大きい|昇|降)順に並べ(?:替え|る)|並び替え",
            "T086":r"(?:区間|部分)(?:の)?和を前計算",
            "T162":r"素数(?:である|かどうか|か否か).{0,20}(?:判定|調べ)|(?:判定|調べ).{0,20}素数",
            "T264":r"(?:割った|割り算の)(?:ときの)?(?:余り|あまり)|割り切れるか|倍数かどうか",
        }
        for e in eds:
            text=normalize(e.get("text",""))
            for tid,pattern in description_rules.items():
                m=re.search(pattern,text)
                if m:
                    context=text[max(0,m.start()-70):m.end()+100]
                    if not NEGATIVE.search(context):
                        add(tid,dict(method="solution_description_rule",role="unresolved",validation_status="not_reviewed",url=e.get("url",""),source=e.get("source",""),matched=m.group(),context=context))
        # A/B elementary string operations can belong to the supplied broad string-processing tag.
        if not labels and p["problem_index"] in {"A","B"}:
            question=normalize(doc["statement"])
            question=question.split("制約")[0].split("入力例")[0]
            if "文字列" in question and re.search(r"取り除|除い|置き換|置換|連結|反転|文字数|文字目|先頭|末尾|辞書順|大文字|小文字|母音|回文|部分文字列",question):
                add("T073",dict(method="elementary_string_task_rule",role="concept",validation_status="not_reviewed",url=p["url"],matched="elementary string manipulation",note="Problem asks for a basic operation on strings; this is a broad supplied tag, not a claim of a specific string-search algorithm."))
        # The problem title can explicitly name a method, unlike arbitrary statement keywords.
        title_hits,_=named_evidence(p["title"],rules)
        for hit in title_hits: add(hit["tag_id"],dict(method="explicit_title_rule",role="unresolved",validation_status="not_reviewed",url=p["url"],matched=hit["matched"],context=p["title"]))
        if pid in manual:
            decision=manual[pid]
            if decision.get("replace",False): labels={}
            for tid in decision.get("remove",[]): labels.pop(tid,None)
            for tid in decision.get("tag_ids",[]): add(tid,dict(method="assistant_semantic_review",role=decision.get("roles",{}).get(tid,"unresolved"),validation_status="assistant_reviewed",url=decision.get("evidence_url",p["url"]),note=decision["reason"],independent_human_review=False))
        tids=sorted(labels)
        status=("assistant_reviewed_no_matching_tag" if not tids and manual[pid].get("disposition")=="no_matching_tag" else "assistant_reviewed") if pid in manual else "provisional_tagged" if tids else "unresolved_no_supported_tag"
        if not eds and not tids and pid not in manual: status="unresolved_no_editorial_or_tag"
        counts_by_method={m:sum(any(e["method"]==m for e in es) for es in labels.values()) for m in {e["method"] for es in labels.values() for e in es}}
        methods.update(counts_by_method)
        rejected_total+=len(rejected)
        for tid in tids:
            tag_counts[tid]+=1
            es=labels[tid]
            pairs.append(dict(tag=taxonomy[tid],problem_id=pid,title=p["problem_index"]+" - "+p["title"],difficulty=p["difficulty"] if p["difficulty"] is not None else "",diff_band="unknown" if p["difficulty"] is None else "0-1999" if p["difficulty"]<2000 else "2000+",url=p["url"],tag_id=tid,related=1,labeling_method=" | ".join(sorted({e["method"] for e in es})),role=" | ".join(sorted({e.get("role","unresolved") for e in es})),validation_status="assistant_reviewed" if any(e["method"]=="assistant_semantic_review" for e in es) else "not_independently_reviewed",needs_review=1,evidence_urls=" | ".join(sorted({e.get("url","") for e in es if e.get("url")})),tagging_version=VERSION))
        row=dict(problem_id=pid,contest_id=p["contest_id"],problem_index=p["problem_index"],title=p["title"],difficulty=p["difficulty"] if p["difficulty"] is not None else "",url=p["url"],tag_ids=" | ".join(tids),tags=" | ".join(taxonomy[t] for t in tids),tag_count=len(tids),tagging_status=status,editorial_count=len(eds),has_prior_tags=int(pid in baseline),tagging_version=VERSION)
        rows.append(row)
        matrix.append(dict(problem_id=pid,**{tid:int(tid in labels) for tid in taxonomy}))
        record=dict(p,statement=doc["statement"],statement_source=doc["source_url"],statement_sha256=doc["statement_sha256"],editorials=eds,tag_ids=tids,tags=[taxonomy[t] for t in tids],tagging_status=status,labels=labels,rejected_name_hits=rejected,tagging_version=VERSION,independent_human_review=False)
        records.append(record)
        if status.startswith("unresolved_"): review_queue.append(dict(row,review_reason="No supported tag found by the current methods; does not imply no applicable algorithm."))
        if len(rows)%200==0: print(json.dumps({"tagging_processed":len(rows),"total":manifest["problem_count"],"tagged":sum(r["tag_count"]>0 for r in rows)}),flush=True)
    if corpus_missing: raise ValueError("Missing problem statements: "+str(corpus_missing))
    if len(rows)!=manifest["problem_count"] or len({r["problem_id"] for r in rows})!=len(rows): raise ValueError("Problem coverage mismatch")
    if len({(r["problem_id"],r["tag_id"]) for r in pairs})!=len(pairs): raise ValueError("Duplicate assignment")
    if sum(sum(r[t] for t in taxonomy) for r in matrix)!=len(pairs): raise ValueError("Matrix reconciliation failed")
    out=ROOT/"output"
    out.mkdir(exist_ok=True)
    csv_write(out/"problems.csv",list(rows[0]),rows)
    csv_write(out/"all_problems_tagged.csv",list(pairs[0]),pairs)
    csv_write(out/"problem_tag_matrix.csv",["problem_id",*taxonomy],matrix)
    csv_write(out/"tag_catalog.csv",["tag_id","tag","problem_count"],[dict(tag_id=t,tag=name,problem_count=tag_counts[t]) for t,name in taxonomy.items()])
    csv_write(out/"unresolved_problems.csv",list(rows[0])+["review_reason"],review_queue)
    with (out/"problems_tagged.jsonl").open("w",encoding="utf-8") as f:
        for record in records: f.write(json.dumps(record,ensure_ascii=False)+"\n")
    stats=dict(version=VERSION,as_of=manifest["as_of"],problem_count=len(rows),contest_count=manifest["contest_count"],taxonomy_count=len(taxonomy),tagged_problem_count=sum(r["tag_count"]>0 for r in rows),unresolved_problem_count=len(review_queue),untagged_problem_count=sum(r["tag_count"]==0 for r in rows),no_matching_tag_after_review_count=sum(r["tagging_status"]=="assistant_reviewed_no_matching_tag" for r in rows),assigned_pairs=len(pairs),used_tags=sum(v>0 for v in tag_counts.values()),unused_tags=len(taxonomy)-len(tag_counts),problems_with_editorials=sum(r["editorial_count"]>0 for r in rows),assistant_semantic_reviewed_problems=len(manual),problems_with_prior_tags=sum(r["has_prior_tags"] for r in rows),method_pair_counts=dict(methods),rejected_name_hits=rejected_total,vocabulary_gaps=dict(vocabulary_gaps),difficulty_bands=dict(Counter("unknown" if r["difficulty"]=="" else "under_2000" if r["difficulty"]<2000 else "2000_or_higher" for r in rows)),paid_api_calls=0,independent_human_review=False,rule_version=config["version"],taxonomy_sha256=hashlib.sha256((ROOT/"taxonomy.json").read_bytes()).hexdigest(),checks=["complete_manifest_coverage","unique_problem_ids","unique_problem_tag_pairs","266_tag_membership","matrix_pair_reconciliation"])
    save_json(out/"summary.json",stats)
    print(json.dumps(stats,ensure_ascii=True),flush=True)

if __name__=="__main__": build()
