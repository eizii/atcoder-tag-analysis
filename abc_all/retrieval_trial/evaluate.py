# -*- coding: utf-8 -*-
"""Evaluate candidate coverage against frozen AI silver labels, never human gold."""
import json,csv,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;OUT=BASE/'output'
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 candidates=[json.loads(l) for l in (OUT/'candidates.jsonl').open(encoding='utf-8')];refs=[json.loads(l) for l in (ROOT/'output_v4/problems_tagged.jsonl').open(encoding='utf-8')];gold={r['problem_id']:set(r['tag_ids']) for r in refs};refmap={r['problem_id']:r for r in refs};assert set(gold)=={r['problem_id'] for r in candidates}
 support=Counter(t for labels in gold.values() for t in labels);methods={'rules':lambda r:set(r['rule_tag_ids'])}
 for k in (5,10,20,40):
  methods[f'names_top{k}']=lambda r,k=k:set(r['name_ranking'][:k]);methods[f'definitions_top{k}']=lambda r,k=k:{v['tag_id'] for v in r['embedding_ranking'][:k]};methods[f'hybrid_top{k}']=lambda r,k=k:set(r['rule_tag_ids'])|{v['tag_id'] for v in r['embedding_ranking'][:k]}
 methods['all266']=lambda r:{f'T{i:03d}' for i in range(1,267)};summary=[];perproblem=[];misses=[];roletable=[];buckets=[]
 for name,method in methods.items():
  hit=Counter();total=Counter();sizes=[];covered=0;nonempty=0;nonemptycovered=0;roles=Counter();rolehits=Counter();freq=Counter();freqhits=Counter()
  for r in candidates:
   pid=r['problem_id'];c=method(r);g=gold[pid];sizes.append(len(c));covered+=g<=c;nonempty+=bool(g);nonemptycovered+=bool(g) and g<=c
   for t in g:
    total[t]+=1;hit[t]+=t in c;role=refmap[pid]['labels'][t][0]['role'];roles[role]+=1;rolehits[role]+=t in c;bucket='1' if support[t]==1 else '2-5' if support[t]<=5 else '6-20' if support[t]<=20 else '21+';freq[bucket]+=1;freqhits[bucket]+=t in c
   perproblem.append(dict(method=name,problem_id=pid,candidate_count=len(c),reference_tag_count=len(g),covered_tags=len(c&g),missed_tag_ids=' | '.join(sorted(g-c)),all_reference_tags_covered=g<=c))
   if name in ('rules','definitions_top20','hybrid_top20') and g-c:
    misses.append(dict(method=name,problem_id=pid,title=refmap[pid]['title'],missed_tag_ids=' | '.join(sorted(g-c)),reference_reason=refmap[pid]['reviews'][0]['reason']))
  count=sum(total.values());summary.append(dict(method=name,reference='V4_AI_silver_not_human_gold',candidate_count_mean=float(np.mean(sizes)),candidate_count_median=float(np.median(sizes)),candidate_count_p95=float(np.quantile(sizes,.95)),candidate_count_max=max(sizes),label_space_reduction=1-float(np.mean(sizes))/266,reference_pairs=count,covered_reference_pairs=sum(hit.values()),micro_candidate_recall=sum(hit.values())/count,macro_seen_tag_recall=float(np.mean([hit[t]/n for t,n in total.items()])),all_tags_covered_problems=covered,all_tags_covered_fraction=covered/len(candidates),reference_nonempty_problems=nonempty,all_tags_covered_nonempty_problems=nonemptycovered,all_tags_covered_nonempty_fraction=nonemptycovered/nonempty))
  roletable.extend(dict(method=name,role=role,reference_pairs=n,covered_pairs=rolehits[role],recall=rolehits[role]/n) for role,n in roles.items());buckets.extend(dict(method=name,frequency_bucket=bucket,reference_pairs=n,covered_pairs=freqhits[bucket],recall=freqhits[bucket]/n) for bucket,n in freq.items())
 write(OUT/'candidate_metrics.csv',summary);write(OUT/'candidate_coverage_by_problem.csv',perproblem);write(OUT/'candidate_misses.csv',misses);write(OUT/'candidate_role_metrics.csv',roletable);write(OUT/'candidate_frequency_metrics.csv',buckets)
 result=dict(reference='V4 AI semantic-review labels; not independent human gold',reference_sha256=hashlib.sha256((ROOT/'output_v4/problems_tagged.jsonl').read_bytes()).hexdigest(),problem_count=len(candidates),reference_pairs=sum(map(len,gold.values())),methods=summary,limitations=['These are candidate-coverage diagnostics, not final LLM precision or F1.','Definitions and rule engineering were not frozen before all historical review work; no untouched-test generalization claim.','No candidate threshold or model was optimized using a held-out human gold set.'])
 (OUT/'silver_evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps([r for r in summary if r['method'] in ('rules','names_top20','definitions_top20','hybrid_top20','all266')],ensure_ascii=False))
if __name__=='__main__':main()
