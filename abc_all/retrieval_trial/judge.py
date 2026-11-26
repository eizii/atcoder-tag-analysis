# -*- coding: utf-8 -*-
"""Validated, resumable OpenAI-compatible judge; makes calls only when run explicitly.

API credentials are read from an explicitly named environment variable and never logged.
"""
import argparse,json,os,time,hashlib,urllib.request,urllib.error
from pathlib import Path
ROLES={'primary','alternative','supporting'}
def validate(result,payload):
 assert isinstance(result,dict) and result.get('problem_id')==payload['problem_id'],'Wrong problem ID'
 assert result.get('review_status') in ('reviewed','needs_review'),'Missing status'
 assert isinstance(result.get('candidate_insufficient'),bool),'Missing candidate insufficiency flag'
 assert isinstance(result.get('missing_concepts'),list),'Missing concepts must be a list'
 assert isinstance(result.get('solutions'),list),'Missing solution list'
 candidates={c['tag_id'] for c in payload['candidates']};sources={s['source_id']:s['text'] for s in payload['source_texts']};sids=set()
 accepted=set(); rejected=set()
 for solution in result['solutions']:
  assert solution.get('solution_id') and solution['solution_id'] not in sids,'Duplicate solution ID';sids.add(solution['solution_id'])
  assert solution.get('summary') and solution.get('complexity'),'Missing explanation or complexity';seen=set()
  for tag in solution['tags']:
   t=tag['tag_id'];assert t in candidates and t not in seen,'Unknown or repeated candidate';seen.add(t);accepted.add(t);assert tag['role'] in ROLES,'Invalid role'
   assert tag['evidence_source'] in sources and len(tag.get('evidence_quote',''))>=10,'Missing source or quote'
   assert tag['evidence_quote'] in sources[tag['evidence_source']],'Quote not found verbatim'
   assert len(tag.get('reason',''))>=10,'Missing reason'
 assert isinstance(result.get('rejected'),list),'Missing rejected list'
 for r in result['rejected']:
  assert r['tag_id'] in candidates and r.get('reason') and r['tag_id'] not in accepted and r['tag_id'] not in rejected,'Invalid rejection'
  rejected.add(r['tag_id'])
 if result['review_status']=='reviewed':assert accepted|rejected==candidates,'Reviewed result must account for every candidate'
 assert result['candidate_insufficient']==bool(result['missing_concepts']),'Missing concepts and insufficiency disagree'
 return result

def main():
 a=argparse.ArgumentParser();a.add_argument('--input',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--base-url',required=True);a.add_argument('--model',required=True);a.add_argument('--api-key-env',default='OPENAI_API_KEY');a.add_argument('--limit',type=int);a.add_argument('--dry-run',action='store_true');a.add_argument('--max-tokens',type=int,default=5000);args=a.parse_args()
 requests=[json.loads(l) for l in args.input.open(encoding='utf-8')];requests=requests[:args.limit] if args.limit else requests
 print(json.dumps({'requests':len(requests),'model':args.model,'base_url':args.base_url,'dry_run':args.dry_run}),flush=True)
 if args.dry_run:
  for r in requests:assert json.loads(r['messages'][1]['content'])['problem_id']==r['custom_id']
  return
 key=os.environ.get(args.api_key_env,'');completed={}
 if args.output.exists():
  for r in map(json.loads,args.output.open(encoding='utf-8')):completed[r['problem_id']]=r
 args.output.parent.mkdir(parents=True,exist_ok=True)
 for r in requests:
  payload=json.loads(r['messages'][1]['content']);prompt_sha=hashlib.sha256(json.dumps(r['messages'],ensure_ascii=False).encode()).hexdigest();pid=r['custom_id']
  if pid in completed:
   assert completed[pid]['prompt_sha256']==prompt_sha and completed[pid]['model']==args.model,'Resume settings differ';continue
  body=json.dumps({'model':args.model,'messages':r['messages'],'temperature':0,'max_tokens':args.max_tokens,'response_format':{'type':'json_object'}}).encode();headers={'Content-Type':'application/json'}
  if key:headers['Authorization']='Bearer '+key
  url=args.base_url.rstrip('/')+'/chat/completions';request=urllib.request.Request(url,data=body,headers=headers);start=time.perf_counter()
  with urllib.request.urlopen(request,timeout=240) as response:raw=json.load(response)
  result=validate(json.loads(raw['choices'][0]['message']['content']),payload);record=dict(problem_id=pid,result=result,model=args.model,provider_model=raw.get('model'),prompt_sha256=prompt_sha,usage=raw.get('usage'),elapsed_seconds=time.perf_counter()-start,independent_gold=False)
  with args.output.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
  print(json.dumps({'completed':pid,'seconds':round(record['elapsed_seconds'],1)}),flush=True)
if __name__=='__main__':main()
