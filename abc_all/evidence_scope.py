"""Conservative, auditable evidence scope filters. No API calls."""
import ast
import hashlib
import re
from collections import defaultdict

POLICY_VERSION="solution-scope-v1"
NEGATIVE=re.compile(r"使え(?:ない|ません)|使うこと(?:は|が)できない|適用でき(?:ない|ません)|間に合(?:わない|いません)|時間制限(?:を|に).{0,25}超|TLE|計算量が大きすぎ|不適切|採用しません|cannot be used|too slow",re.I)

def shared_body_keys(docs):
    groups=defaultdict(set)
    for pid,doc in docs.items():
        for e in doc.get("editorials",[]):
            if e.get("url") and bool(e.get("text","").strip()):
                groups[(e["url"],hashlib.sha256(e["text"].encode()).hexdigest())].add(pid)
    return {k:sorted(v) for k,v in groups.items() if len(v)>1}

def source_scope(e, shared, title=None):
    text=e.get("text","")
    key=(e.get("url",""),hashlib.sha256(text.encode()).hexdigest())
    exact_pdf_title=(e.get("source","").startswith("official_pdf_") and title and text.splitlines()[0].strip()==title.strip())
    if key in shared and not exact_pdf_title:
        return "",[],[dict(reason="shared_unsegmented_editorial",url=e.get("url",""),
            problem_ids=shared[key],context=text[:220],note="Same URL and complete body assigned to multiple tasks; quarantine until per-task segmentation is checked.")]
    audit=[]
    codes=e.get("codes",[])
    # A quoted mention in the introduction is not the actual solution heading.
    # Last occurrence handles the introductory quotation and the later heading.
    marker="この問題の解説"
    if text.count(marker)>=2:
        cut=text.rfind(marker)
        audit.append(dict(reason="preface_before_explicit_solution_heading",url=e.get("url",""),
            context=text[:220],excluded_chars=cut))
        text=text[cut:]
        # Snippet positions in flattened legacy text are unavailable.
        codes=[]
    worked=re.compile(r"例題\s*[:：].*?(?=さて、.{0,30}元の問題.{0,10}適用|元の問題に戻|本題に戻)",re.S)
    def remove_example(m):
        audit.append(dict(reason="worked_example_not_target_problem",url=e.get("url",""),context=m.group()[:220],excluded_chars=len(m.group())))
        return " "
    text=worked.sub(remove_example,text)
    refs=re.search(r"(?:参考文献|参考資料|関連記事|関連問題|References|Related problems)(?=\s|[:：])",text,re.I)
    if refs:
        audit.append(dict(reason="references_or_related_problem_section",url=e.get("url",""),context=text[refs.start():refs.start()+220],excluded_chars=len(text)-refs.start()))
        text=text[:refs.start()]
    return text,codes,audit

def local_context(text,start,end):
    # Japanese mathematical text contains many newlines within a single phrase.
    # Sentence/clause boundaries are more useful than PDF line boundaries.
    bounds=[0,len(text)]
    for m in re.finditer(r"。|[;；]|(?:ので|ため|ですが|しかし|一方|代わりに|そこで|が、)",text):
        bounds.append(m.end())
    left=max(b for b in bounds if b<=start)
    right=min(b for b in bounds if b>=end)
    return text[max(left,start-120):min(right,end+180)].strip()

def rejection_reason(tid,context):
    if re.search(r"次の(?:記事|文献|資料).{0,20}参照.{0,15}[:：]",context):
        return "reference_link_title_only"
    if tid=="T135" and re.search(r"個あり|計算量|回である|オーダー",context) and re.search(r"mathrm|O\s*\(",context):
        return "prime_number_theorem_complexity_bound"
    if re.search(r"の例としては.{0,120}(?:挙げられ|知られ)",context):
        return "example_of_general_class_not_application"
    if NEGATIVE.search(context):
        return "negative_or_infeasible_context"
    if tid in {"T111","T140"} and re.search(r"逆関数|逆アッカーマン",context) and re.search(r"α|alpha|計算量|ここで|但し|ただし",context,re.I):
        return "inverse_ackermann_complexity_background"
    if re.search(r"(?:と呼ばれる|という)(?:方法|手法).{0,12}存在",context):
        return "mentioned_method_without_application"
    return None

def executable_code(code):
    """Conservative direct-use evidence; this is not a full program analyser."""
    # Only the main function of a braced program; helper declarations and
    # unused bundled libraries must not count as execution evidence.
    main=re.search(r"\b(?:main|Main)\s*\([^)]*\)[^{;]*\{",code)
    if main:
        start=main.end()
        depth=1
        i=start
        # Ignore braces in strings/comments while preserving positions.
        masked=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                      lambda m:" "*(m.end()-m.start()),code)
        while i<len(masked) and depth:
            depth += (masked[i]=="{")-(masked[i]=="}")
            i+=1
        return code[start:i-1] if depth==0 else ""
    try:
        tree=ast.parse(code)
    except (SyntaxError,ValueError):
        # Unscoped C++/Java/Rust snippets may just be library definitions.
        return ""
    functions={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    roots=[n for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Import,ast.ImportFrom))]
    nodes=list(roots); seen=set()
    for n in nodes:
        for sub in ast.walk(n):
            if isinstance(sub,ast.Call) and isinstance(sub.func,ast.Name) and sub.func.id in functions and sub.func.id not in seen:
                seen.add(sub.func.id); nodes.append(functions[sub.func.id])
    lines=code.splitlines()
    return "\n".join("\n".join(lines[n.lineno-1:n.end_lineno]) for n in nodes)
