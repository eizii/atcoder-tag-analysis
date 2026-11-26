# -*- coding: utf-8 -*-
"""Create identical source inputs with a different deterministic candidate set."""
import argparse,json
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE/'output'
def main():
 a=argparse.ArgumentParser();a.add_argument('--method',choices=['all266','rules','embedding','names','hybrid','expanded'],required=True);a.add_argument('--experiment-dir',type=Path,default=OUT);a.add_argument('--k',type=int,default=20);a.add_argument('--pilot',action='store_true');a.add_argument('--problem-id',action='append');a.add_argument('--problem-ids-file',type=Path);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
 if args.problem_ids_file:args.problem_id=json.loads(args.problem_ids_file.read_text(encoding='utf-8'))
 exp=args.experiment_dir;mapping=json.loads((exp/'artifact_paths.json').read_text(encoding='utf-8')) if (exp/'artifact_paths.json').exists() else {}
 def artifact(name):return exp/mapping.get(name,name)
 if args.method=='expanded' and args.k!=20:a.error('expanded requests use the frozen top20 expansion; choose --k 20')
 profiles={r['tag_id']:r for r in json.loads(artifact('tag_profiles.json').read_text(encoding='utf-8'))};cs={r['problem_id']:r for r in map(json.loads,artifact('candidates.jsonl').open(encoding='utf-8'))};rules=json.loads(artifact('rule_candidates.json').read_text(encoding='utf-8'));chunks=[json.loads(l) for l in artifact('chunks.jsonl').open(encoding='utf-8')];pilot=set(json.loads(artifact('pilot_selection.json').read_text(encoding='utf-8'))['problem_ids']) if args.pilot else None
 with args.output.open('w',encoding='utf-8') as f:
  for r in map(json.loads,artifact('llm_requests_scoped.jsonl').open(encoding='utf-8')):
   pid=r['custom_id']
   if pilot is not None and pid not in pilot:continue
   if args.problem_id is not None and pid not in args.problem_id:continue
   c=cs[pid];payload=json.loads(r['messages'][1]['content']);ranked=c['embedding_ranking'];embed={v['tag_id'] for v in ranked[:args.k]};ids=set(c['expanded_tag_ids']) if args.method=='expanded' else set(profiles) if args.method=='all266' else set(c['rule_tag_ids']) if args.method=='rules' else embed if args.method=='embedding' else set(c['name_ranking'][:args.k]) if args.method=='names' else embed|set(c['rule_tag_ids']);by={v['tag_id']:v for v in ranked}
   payload['candidate_policy']=args.method+f'_k{args.k}';payload['candidates']=[dict(profiles[t],seed_origins=c.get('seed_origins',{}).get(t,[]),rule_evidence=rules[pid].get(t,[]),retrieval_evidence=chunks[c.get('evidence_chunk_overrides',{}).get(t,by[t]['best_chunk_id'])],relation_evidence=c.get('expansion_reasons',{}).get(t,[])) for t in sorted(ids)]
   by_source={s['source_id']:s['text'] for s in payload['source_texts']}
   for candidate in payload['candidates']:
    hint=candidate['retrieval_evidence']
    if hint['text'] not in by_source.get(hint['source_id'],''):candidate['retrieval_evidence']=dict(excluded=True,reason='not_in_judge_scoped_source')
    candidate['rule_evidence']=[dict(h,quote_admissible=False) for h in candidate['rule_evidence'] if h['source_id'] in by_source]
   r['messages'][1]['content']=json.dumps(payload,ensure_ascii=False);f.write(json.dumps(r,ensure_ascii=False)+'\n')
 print(str(args.output))
if __name__=='__main__':main()
