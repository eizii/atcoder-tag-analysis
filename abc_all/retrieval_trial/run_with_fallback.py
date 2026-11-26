"""Explicitly configured API experiment: hybrid -> all266 on insufficiency.

Never invoked by candidate generation. Dry run performs no API call. A single
fallback is allowed per problem; unresolved cases remain needs_review.
"""
import argparse,json,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE/'output'
def readrows(p):return list(map(json.loads,p.open(encoding='utf-8'))) if p.exists() else []
def main():
    a=argparse.ArgumentParser();a.add_argument('--base-url',required=True);a.add_argument('--model',required=True);a.add_argument('--api-key-env',default='TAGGER_API_KEY');a.add_argument('--output-dir',type=Path,required=True);a.add_argument('--experiment-dir',type=Path,default=OUT);a.add_argument('--pilot',action='store_true');a.add_argument('--limit',type=int);a.add_argument('--max-tokens',type=int,default=5000);a.add_argument('--fallback-max-tokens',type=int,default=20000);a.add_argument('--dry-run',action='store_true');args=a.parse_args()
    if args.limit is not None and args.limit<1:a.error('--limit must be positive')
    source=args.experiment_dir/('pilot_requests_scoped.jsonl' if args.pilot else 'llm_requests_scoped.jsonl')
    def run(script,extra):subprocess.run([sys.executable,'-X','utf8',str(BASE/script),*extra],check=True)
    common=['--base-url',args.base_url,'--model',args.model,'--api-key-env',args.api_key_env,'--max-tokens',str(args.max_tokens)]
    initial=args.output_dir/'initial.jsonl';initialargs=['--input',str(source),'--output',str(initial),*common]
    if args.limit:initialargs+=['--limit',str(args.limit)]
    if args.dry_run:run('judge.py',initialargs+['--dry-run']);return
    args.output_dir.mkdir(parents=True,exist_ok=True);run('judge.py',initialargs)
    selected=readrows(source);selected=selected[:args.limit] if args.limit else selected;ids={r['custom_id'] for r in selected};first={r['problem_id']:r for r in readrows(initial) if r['problem_id'] in ids}
    assert set(first)==ids,'Initial results are incomplete'
    fallback_ids=sorted(pid for pid,r in first.items() if r['result']['candidate_insufficient']);final=dict(first)
    if fallback_ids:
        idfile=args.output_dir/'fallback_ids.json';idfile.write_text(json.dumps(fallback_ids)+'\n',encoding='utf-8');requestfile=args.output_dir/'fallback_requests.jsonl';resultfile=args.output_dir/'fallback.jsonl'
        run('build_requests.py',['--method','all266','--experiment-dir',str(args.experiment_dir),'--problem-ids-file',str(idfile),'--output',str(requestfile)])
        fallback_common=list(common);fallback_common[fallback_common.index('--max-tokens')+1]=str(args.fallback_max_tokens)
        run('judge.py',['--input',str(requestfile),'--output',str(resultfile),*fallback_common])
        for r in readrows(resultfile):
            pid=r['problem_id']
            if pid not in fallback_ids:continue
            r['fallback_from_prompt_sha256']=first[pid]['prompt_sha256']
            if r['result']['candidate_insufficient']:r['result']['review_status']='needs_review'
            final[pid]=r
    with (args.output_dir/'merged.jsonl').open('w',encoding='utf-8') as f:
        for pid in sorted(final):f.write(json.dumps(final[pid],ensure_ascii=False)+'\n')
    print(json.dumps(dict(initial=len(first),fallback=len(fallback_ids),remaining_needs_review=sum(r['result']['review_status']=='needs_review' for r in final.values()))))
if __name__=='__main__':main()
