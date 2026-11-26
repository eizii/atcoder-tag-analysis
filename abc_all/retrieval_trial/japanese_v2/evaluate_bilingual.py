"""Separate label evaluation of bilingual seeds, expansion, and equal-size controls."""
import csv,hashlib,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;OUT=BASE/'bilingual_output';JA=BASE/'output';OLD=BASE.parent/'output';ROOT=BASE.parent.parent
sys.path.insert(0,str(BASE));from evaluate import fill_to_budget
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    en=np.load(OLD/'retrieval_scores.npz');ja=np.load(JA/'retrieval_scores.npz');ids=ja['problem_ids'].tolist();tags=ja['tag_ids'].tolist();erank=[[tags[j] for j in r] for r in np.argsort(-en['definition_scores'],axis=1,kind='stable')];jrank=[[tags[j] for j in r] for r in np.argsort(-ja['definition_scores'],axis=1,kind='stable')];rules=json.loads((OLD/'rule_candidates.json').read_text(encoding='utf-8'));sets={name:{} for name in ('bilingual_seed20_each','bilingual_expanded20_each','en_budget_matched','ja_budget_matched','interleaved_budget_matched')};added=Counter();i=0
    for r in map(json.loads,(OUT/'candidates.jsonl').open(encoding='utf-8')):
        pid=r['problem_id'];assert ids[i]==pid;expanded=set(r['expanded_tag_ids']);seeds=set(r['seed_tag_ids']);sets['bilingual_seed20_each'][pid]=seeds;sets['bilingual_expanded20_each'][pid]=expanded;n=len(expanded)
        sets['en_budget_matched'][pid]=fill_to_budget(rules[pid],erank[i],n);sets['ja_budget_matched'][pid]=fill_to_budget(rules[pid],jrank[i],n)
        interleaved=[t for pair in zip(erank[i],jrank[i]) for t in pair];sets['interleaved_budget_matched'][pid]=fill_to_budget(rules[pid],interleaved,n);added.update(expanded-seeds);i+=1
    assert i==3012
    refs={r['problem_id']:r for r in map(json.loads,(ROOT/'output_v4/problems_tagged.jsonl').open(encoding='utf-8'))};gold={p:set(r['tag_ids']) for p,r in refs.items()};support=Counter(t for g in gold.values() for t in g);names={p['tag_id']:p['tag'] for p in json.loads((JA/'tag_profiles.json').read_text(encoding='utf-8'))};summary=[];tagrows=[];problemrows=[];role_rows=[]
    for method,collection in sets.items():
        hits=Counter();selected=Counter();roles=Counter();rh=Counter();sizes=[];whole=0
        for pid,c in collection.items():
            g=gold[pid];hits.update(c&g);selected.update(c);sizes.append(len(c));whole+=bool(g) and g<=c
            for t in g:role=refs[pid]['labels'][t][0]['role'];roles[role]+=1;rh[role]+=t in c
            problemrows.append(dict(method=method,problem_id=pid,candidate_count=len(c),reference_pairs=len(g),covered_pairs=len(c&g),missing_tag_ids=' | '.join(sorted(g-c))))
        summary.append(dict(method=method,candidate_count_mean=float(np.mean(sizes)),candidate_count_p95=float(np.quantile(sizes,.95)),candidate_count_max=max(sizes),reference_pairs=sum(support.values()),covered_reference_pairs=sum(hits.values()),micro_candidate_recall=sum(hits.values())/sum(support.values()),macro_seen_tag_recall=float(np.mean([hits[t]/n for t,n in support.items()])),all_tags_covered_nonempty_problems=whole,all_tags_covered_nonempty_fraction=whole/sum(bool(g) for g in gold.values())))
        for t in tags:tagrows.append(dict(method=method,tag_id=t,tag=names[t],reference_pairs=support[t],covered_pairs=hits[t],recall=hits[t]/support[t] if support[t] else '',selected_problems=selected[t]))
        for role,n in roles.items():role_rows.append(dict(method=method,role=role,reference_pairs=n,covered_pairs=rh[role],recall=rh[role]/n))
    comparisons=[]
    for baseline in ('en_budget_matched','ja_budget_matched','interleaved_budget_matched'):
        c=sets[baseline];final=sets['bilingual_expanded20_each'];assert all(len(c[p])==len(final[p]) for p in ids)
        comparisons.append(dict(baseline=baseline,gained_reference_pairs=sum(len((final[p]-c[p])&gold[p]) for p in ids),lost_reference_pairs=sum(len((c[p]-final[p])&gold[p]) for p in ids),exact_candidate_count_match_every_problem=True))
    missing=[]
    for pid in ids:
        absent=gold[pid]-sets['bilingual_expanded20_each'][pid]
        if absent:missing.append(dict(problem_id=pid,title=refs[pid]['title'],missing_tag_ids=' | '.join(sorted(absent)),reference_reason=refs[pid]['reviews'][0]['reason']))
    write(OUT/'candidate_metrics.csv',summary);write(OUT/'tag_metrics.csv',tagrows);write(OUT/'coverage_by_problem.csv',problemrows);write(OUT/'role_metrics.csv',role_rows);write(OUT/'candidate_misses.csv',missing)
    save(OUT/'silver_evaluation.json',dict(reference='V4 AI silver, not independent human gold or final LLM accuracy',reference_sha256=hashlib.sha256((ROOT/'output_v4/problems_tagged.jsonl').read_bytes()).hexdigest(),metrics=summary,matched_budget_comparisons=comparisons,development_iteration_after_Japanese_only_diagnostics=True))
    print(json.dumps(dict(metrics=summary,priority=[r for r in tagrows if r['tag_id'] in ('T026','T029') and r['method']=='bilingual_expanded20_each'],comparisons=comparisons),ensure_ascii=False))
if __name__=='__main__':main()
