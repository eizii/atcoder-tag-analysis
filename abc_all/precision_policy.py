"""V3 evidence policy. Keep the v2 experimental pipeline reproducible."""
import hashlib,re,unicodedata
from evidence_scope import source_scope,local_context,rejection_reason,executable_code
from tag_all import normalize,alias_regex,OVERLAP_PARENTS

POLICY_VERSION='solution-scope-v3'
# Suppress only an overlapping name span, never an independently supported tag.
OVERLAPS={**OVERLAP_PARENTS}
for child,parents in {'T010':{'T011'},'T007':{'T011'},'T043':{'T077'},'T049':{'T077'},'T014':{'T064'},'T015':{'T003'}}.items():
 OVERLAPS[child]=OVERLAPS.get(child,set())|parents
PDF_HEADER=re.compile(r'^\s*([A-H])\s*(?:[:：．.]|[-–－]|問題|問(?=\s|$))\s*(\S[^\n]*)',re.M)

def scoped_editorial(e,shared,p):
 text=e.get('text',''); audit=[]
 if e.get('source','').startswith('official_pdf_'):
  headers=list(PDF_HEADER.finditer(text))
  # The PDF uses the joint contest's original letter, not the task ID suffix.
  letter=headers[0].group(1) if headers and headers[0].start()<180 else p['problem_index']
  other=next((h for h in headers if h.group(1)!=letter and (h.group(1)>letter or re.match(r'^\s*[A-H]\s*[:：．.\-–－]',h.group()))),None)
  if other:
   cut=other.start()
   audit.append(dict(reason='pdf_next_problem_boundary',url=e.get('url',''),context=text[cut:cut+220],excluded_chars=len(text)-cut))
   text=text[:cut]
  # Remove partial-score sections with an explicit full-score heading later.
  partial=re.search(r'(?m)^\s*(?:[A-H]\s*問題\s*)?部分点[^\n]*',text)
  full=re.search(r'(?m)^\s*(?:[A-H]\s*問題\s*)?(?:完答|満点|満点解法)[^\n]*',text)
  if partial and full and partial.start()<full.start():
   audit.append(dict(reason='partial_score_section',url=e.get('url',''),context=text[partial.start():partial.start()+200],excluded_chars=full.start()-partial.start()))
   text=text[:partial.start()]+text[full.start():]
  e=dict(e,text=text,codes=[])
 # Shared-body detection must use the original fingerprint, before any cuts.
 # Delegate reference/example removal; shared inputs are checked by the caller.
 text,codes,rest=source_scope(e,{},p['title'])
 return text,codes,audit+rest

def extra_rejection(tid,text,hit):
 start,end=hit['start'],hit['end']; context=hit['context']
 if tid=='T234' and re.match(r'\s*(?:法\s*)?(?:(?:の)?よう(?:な|に)|に似)',text[end:]):
  return 'analogy_to_prim_not_prim_algorithm'
 if tid=='T086' and re.search(r'累積和の要領',context) and re.search(r'木|複製|直線|永続',context):
  return 'prefix_sum_analogy_for_persistent_versions'
 if tid=='T038' and re.match(r'\s*定理',text[end:]):
  return 'minimax_theorem_is_not_minimax_search'
 if tid=='T011' and re.search(r'優先(?:度|順位)付きキュー|priority\s*queue|ヒープ',text,re.I) and not re.search(r'FIFO|先入れ先出し|通常のキュー|幅優先|\bBFS\b',text,re.I):
  return 'bare_queue_in_heap_explanation'
 if re.search(r'(?:使わず|用いず|利用せず|必要(?:は|が)?(?:ない|ありません))',context) and re.search(r'(?:使わず|用いず|利用せず)',text[end:end+18]):
  return 'method_explicitly_not_required'
 if re.search(r'(?:参考|関連)(?:\s*[:：])',context[:max(0,context.find(hit['matched']))]):
  return 'reference_title_not_solution'
 return None

def named_evidence_v3(raw,rules):
 text=normalize(raw)
 text=re.sub(r'https?://[^\s]+','',text)
 hits=[];rejected=[]
 for tid,aliases in rules.items():
  for alias,pattern in aliases:
   for m in pattern.finditer(text):
    hit=dict(tag_id=tid,matched=alias,start=m.start(),end=m.end(),context=local_context(text,m.start(),m.end()))
    reason=rejection_reason(tid,hit['context']) or extra_rejection(tid,text,hit)
    if reason: rejected.append(dict(hit,reason=reason))
    else: hits.append(hit)
 filtered=[]
 for hit in hits:
  specific=next((h for h in hits if hit['tag_id'] in OVERLAPS.get(h['tag_id'],set()) and h['start']<=hit['start'] and h['end']>=hit['end']),None)
  if specific: rejected.append(dict(hit,reason='name_inside_specific_method',specific_tag_id=specific['tag_id']))
  else: filtered.append(hit)
 return filtered,rejected

def description_rejection(tid,context,matched):
 if tid=='T077' and re.search(r'(?:並び替え|並べ替え)方',context):
  return 'counting_permutations_not_sorting'
 if tid=='T076' and re.search(r'問題文(?:の|で)(?:通り|とおり).{0,15}(?:DP|動的計画)',context,re.I):
  return 'deriving_dp_from_statement_not_simulation'
 return rejection_reason(tid,context)
