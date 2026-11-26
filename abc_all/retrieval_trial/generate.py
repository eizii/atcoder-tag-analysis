# -*- coding: utf-8 -*-
"""Candidate generation is deliberately independent from V4 assignment labels."""
import sys,csv,json,re,hashlib,time,os
from pathlib import Path
from collections import Counter
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;sys.path.insert(0,str(ROOT))
from tag_all import alias_regex,CODE_RULES,normalize
from tag_precision import EXTRA_ALIASES,DESCRIPTION_RULES,clean_code
from precision_policy import scoped_editorial,named_evidence_v3,description_rejection,POLICY_VERSION
from evidence_scope import shared_body_keys,local_context
from encoder import Encoder
OUT=BASE/'output';CACHE=BASE/'cache';KS=(5,10,20,40)
SYSTEM='''あなたは競技プログラミングの解法タグ判定者です。問題文、最大制約、解説、候補タグの定義を照合してください。主解・制約内で成立する別解・実際に使う補助手法を採用し、部分点だけ/速度不足/参考題名/証明だけの概念は採用しません。解法を分けてください。検索順位やルールの一致は正解を保証しません。候補外の必要手法に気付いたらcandidate_insufficient=trueとし、missing_conceptsに記録してください。確信できない場合は保留にします。出力JSON: {problem_id,solutions:[{solution_id,summary,complexity,tags:[{tag_id,role:primary|alternative|supporting,evidence_source,evidence_quote,reason}]}],rejected:[{tag_id,reason}],candidate_insufficient,missing_concepts:[],review_status:reviewed|needs_review}。引用は入力のsource_textsの本文の連続部分から正確に選んでください。'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,rows,fields=None):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def load_unlabelled():
 manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'));docs={d['problem_id']:d for d in map(json.loads,(ROOT/'corpus_sources.jsonl').open(encoding='utf-8'))};tax=json.loads((ROOT/'taxonomy.json').read_text(encoding='utf-8'));aliases=json.loads((ROOT/'tag_rules.json').read_text(encoding='utf-8'))['aliases']
 for t,extra in EXTRA_ALIASES.items():aliases[t]=sorted(set(aliases.get(t,[])+extra))
 definitions=dict(l.split('|',1) for l in (BASE/'tag_descriptions.tsv').read_text(encoding='utf-8-sig').splitlines() if l.strip());assert set(definitions)=={t['tag_id'] for t in tax}
 profiles=[dict(t,definition=definitions[t['tag_id']],aliases=aliases.get(t['tag_id'],[])) for t in tax]
 supplements={}
 for x in map(json.loads,(ROOT/'precision_sources.jsonl').open(encoding='utf-8')):supplements.setdefault(x['problem_id'],[]).append(x['editorial'])
 return manifest,docs,profiles,supplements

def chunk_text(text,encoder,max_chars=420,overlap=64):
 chunks=[];start=0
 while start<len(text):
  end=min(len(text),start+max_chars)
  while end-start>35 and encoder.token_length('query: '+text[start:end])>encoder.max_length:end=start+(end-start)*3//4
  if encoder.token_length('query: '+text[start:end])>encoder.max_length:raise ValueError('Cannot create a nontruncated chunk')
  snippet=text[start:end].strip()
  if len(snippet)>=15:chunks.append((start,end,snippet))
  if end==len(text):break
  start=max(start+1,end-overlap)
 return chunks

def prepare(encoder):
 manifest,docs,profiles,supplements=load_unlabelled();shared=shared_body_keys(docs);rules={t['tag_id']:[(a,alias_regex(a)) for a in sorted(set([t['tag'],*t['aliases']]))] for t in profiles};chunks=[];rules_by={};sources_by={};scope_audit=[]
 for pos,p in enumerate(manifest['problems']):
  pid=p['problem_id'];d=docs[pid];replacement={e['url']:e for e in supplements.get(pid,[])};editorials=[replacement.pop(e.get('url'),e) for e in d['editorials']];editorials.extend(replacement.values());sources=[];evidence={};seen_text=set()
  for j,e in enumerate(editorials):
   raw=e.get('text','');key=(e.get('url',''),hashlib.sha256(raw.encode()).hexdigest());source_id=f'editorial_{j}';sources.append(dict(source_id=source_id,url=e.get('url') or p['url'],text=raw,codes=e.get('codes',[])))
   if key in shared and not (e.get('source','').startswith('official_pdf_') and raw.splitlines()[0].strip()==p['title'].strip()):scope_audit.append(dict(problem_id=pid,source_id=source_id,reason='shared_unsegmented_editorial'));continue
   scoped,codes,audits=scoped_editorial(e,shared,p);scope_audit.extend(dict(problem_id=pid,source_id=source_id,reason=a['reason']) for a in audits)
   if not scoped.strip() or scoped in seen_text:continue
   seen_text.add(scoped)
   def add(tid,kind,excerpt):
    hit=dict(rule_id=kind,source_id=source_id,url=e.get('url') or p['url'],excerpt=excerpt[:400]);evidence.setdefault(tid,[])
    if hit not in evidence[tid] and len(evidence[tid])<4:evidence[tid].append(hit)
   hits,rejected=named_evidence_v3(scoped,rules)
   for h in hits:add(h['tag_id'],'name_v3',h['context'])
   code=clean_code('\n'.join(codes))
   for tid,pattern in CODE_RULES.items():
    m=re.search(pattern,code)
    if m:add(tid,'executable_code_v3',code[max(0,m.start()-70):m.end()+140])
   nt=normalize(scoped)
   for tid,pattern in DESCRIPTION_RULES.items():
    for m in re.finditer(pattern,nt):
     context=local_context(nt,m.start(),m.end())
     if not description_rejection(tid,context,m.group()):add(tid,'description_v3',context)
   for start,end,snippet in chunk_text(scoped,encoder):chunks.append(dict(problem_id=pid,source_id=source_id,url=e.get('url') or p['url'],start=start,end=end,text=snippet,scope_text_sha256=hashlib.sha256(scoped.encode()).hexdigest(),raw_source_sha256=hashlib.sha256(raw.encode()).hexdigest()))
  # Statement is an additional unlabelled view, never a gold-tag cue.
  statement=d['statement'].split('入力例')[0];sources.insert(0,dict(source_id='statement',url=p['url'],text=d['statement'],codes=[]))
  for start,end,snippet in chunk_text(statement,encoder):chunks.append(dict(problem_id=pid,source_id='statement',url=p['url'],start=start,end=end,text=snippet,scope_text_sha256=hashlib.sha256(statement.encode()).hexdigest(),raw_source_sha256=d['statement_sha256']))
  rules_by[pid]=evidence;sources_by[pid]=sources
  if pos%500==0:print(json.dumps({'prepared_problems':pos,'chunks':len(chunks)}),flush=True)
 return manifest,profiles,chunks,rules_by,sources_by,scope_audit

def main():
 OUT.mkdir(exist_ok=True);CACHE.mkdir(exist_ok=True);start=time.perf_counter();encoder=Encoder();manifest,profiles,chunks,rules_by,sources_by,audits=prepare(encoder);save(OUT/'tag_profiles.json',profiles);save(OUT/'rule_candidates.json',rules_by);save(OUT/'source_scope_audit.json',audits)
 with (OUT/'chunks.jsonl').open('w',encoding='utf-8') as f:
  for i,c in enumerate(chunks):c['chunk_id']=i;f.write(json.dumps(c,ensure_ascii=False)+'\n')
 sourcefiles=['manifest.json','taxonomy.json','corpus_sources.jsonl','precision_sources.jsonl','tag_rules.json','tag_all.py','tag_precision.py','precision_policy.py','evidence_scope.py'];hashes={n:sha(ROOT/n) for n in sourcefiles};hashes['tag_descriptions.tsv']=sha(BASE/'tag_descriptions.tsv');hashes['encoder.py']=sha(BASE/'encoder.py');hashes['generate.py']=sha(Path(__file__))
 cache_key=hashlib.sha256(json.dumps(dict(hashes=hashes,model=encoder.manifest,max_tokens=encoder.max_length),sort_keys=True).encode()).hexdigest();vecfile=CACHE/f'{cache_key}.npz'
 fulltexts=[p['tag']+'。'+p['definition']+'。別名: '+', '.join(p['aliases']) for p in profiles];nametexts=[p['tag'] for p in profiles]
 if vecfile.exists():
  z=np.load(vecfile);cv=z['chunks'];tv=z['definitions'];nv=z['names'];print('reusing cached embeddings',flush=True);encoding_stats=json.loads(vecfile.with_suffix('.json').read_text(encoding='utf-8'))
 else:
  tv=encoder.encode(fulltexts,prefix='passage: ');tstat=encoder.last_stats;nv=encoder.encode(nametexts,prefix='passage: ');nstat=encoder.last_stats;cv=encoder.encode([c['text'] for c in chunks],prefix='query: ');cstat=encoder.last_stats;encoding_stats={'definitions':tstat,'names':nstat,'chunks':cstat};np.savez_compressed(vecfile,chunks=cv,definitions=tv,names=nv);save(vecfile.with_suffix('.json'),encoding_stats)
 assert cv.shape==(len(chunks),384) and tv.shape==(266,384) and nv.shape==(266,384)
 ids=[p['problem_id'] for p in manifest['problems']];tagids=[p['tag_id'] for p in profiles];index={p:i for i,p in enumerate(ids)};scores=np.full((len(ids),266),-np.inf,dtype=np.float32);name_scores=scores.copy();best=np.full((len(ids),266),-1,dtype=np.int32)
 for offset in range(0,len(chunks),512):
  block=cv[offset:offset+512]@tv.T;bn=cv[offset:offset+512]@nv.T
  for j,vals in enumerate(block):
   ci=offset+j;pi=index[chunks[ci]['problem_id']];take=vals>scores[pi];scores[pi,take]=vals[take];best[pi,take]=ci;name_scores[pi]=np.maximum(name_scores[pi],bn[j])
 assert np.isfinite(scores).all() and (best>=0).all();np.savez_compressed(OUT/'retrieval_scores.npz',definition_scores=scores,name_scores=name_scores,best_chunk=best,problem_ids=np.array(ids),tag_ids=np.array(tagids));rankings=np.argsort(-scores,axis=1,kind='stable');nr=np.argsort(-name_scores,axis=1,kind='stable')
 profilemap={p['tag_id']:p for p in profiles};candidates=[];requests=[]
 for i,pid in enumerate(ids):
  ranked=[dict(tag_id=tagids[j],score=float(scores[i,j]),best_chunk_id=int(best[i,j])) for j in rankings[i]];ruleids=sorted(rules_by[pid]);hybrid=sorted(set(ruleids)|{r['tag_id'] for r in ranked[:20]});record=dict(problem_id=pid,rule_tag_ids=ruleids,embedding_ranking=ranked,name_ranking=[tagids[j] for j in nr[i]],hybrid_top20_tag_ids=hybrid);candidates.append(record)
  payload=dict(problem_id=pid,title=manifest['problems'][i]['title'],candidate_policy='top20 definitions plus rule union; no labelled-example retrieval',candidates=[dict(profilemap[t],rule_evidence=rules_by[pid].get(t,[]),retrieval_evidence=chunks[best[i,tagids.index(t)]]) for t in hybrid],source_texts=sources_by[pid])
  requests.append(dict(custom_id=pid,messages=[dict(role='system',content=SYSTEM),dict(role='user',content=json.dumps(payload,ensure_ascii=False))]))
 for name,data in [('candidates.jsonl',candidates),('llm_requests.jsonl',requests)]:
  with (OUT/name).open('w',encoding='utf-8') as f:
   for r in data:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 # A deliberately selected demonstration sample, not a random test or gold evaluation.
 selections=[('abc007','C'),('abc168','D'),('abc284','E'),('abc184','D'),('abc319','C'),('abc411','E'),('abc220','F'),('abc340','G'),('abc222','H'),('abc055','C'),('abc092','B'),('abc100','D'),('abc263','E'),('abc375','G'),('abc395','F'),('abc396','G'),('abc404','D'),('abc405','G'),('abc417','D'),('abc412','G')];bykey={(p['contest_id'],p['problem_index']):p['problem_id'] for p in manifest['problems']};pilot=[bykey[k] for k in selections];save(OUT/'pilot_selection.json',dict(problem_ids=pilot,selection='fixed illustrative cases chosen by contest and problem index before retrieval result inspection; not a representative accuracy sample'))
 with (OUT/'pilot_requests.jsonl').open('w',encoding='utf-8') as f:
  for r in requests:
   if r['custom_id'] in pilot:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 summary=dict(created='2026-11-26',task='candidate generation only; final acceptance requires LLM or human verification',problem_count=len(ids),taxonomy_count=266,chunks=len(chunks),model=encoder.manifest,encoding=encoding_stats,embedding_dimension=384,aggregation='maximum cosine similarity over per-source overlapping chunks; exact scan of all tags',chunking='420 characters; overlap64; shorten until query tokens <=256; no per-problem chunk cap',rule_policy=POLICY_VERSION,hybrid_policy='union of embedding top20 and all accepted V3 rule hits',input_sha256=hashes,cache_key=cache_key,elapsed_seconds=time.perf_counter()-start,candidate_counts={'rules':dict(mean=float(np.mean([len(r['rule_tag_ids']) for r in candidates])),maximum=max(len(r['rule_tag_ids']) for r in candidates)),'hybrid20':dict(mean=float(np.mean([len(r['hybrid_top20_tag_ids']) for r in candidates])),maximum=max(len(r['hybrid_top20_tag_ids']) for r in candidates))},remote_inference_calls=0,paid_api_calls=0,reference_labels_used_for_generation=False,pilot_size=len(pilot),limitations=['prototype uses hand-authored tag definitions and existing manually engineered rules; not an untouched held-out benchmark','V4 will be an AI-generated silver reference only','all source chunks and statement views may include explanatory or negative concepts; LLM must reject them','ONNX int8 quantized inference; absolute cosine values are not probabilities'])
 save(OUT/'generation_summary.json',summary);print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
