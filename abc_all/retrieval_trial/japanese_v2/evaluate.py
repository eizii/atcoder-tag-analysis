"""Separate silver-label diagnostics, including exactly matched candidate budgets."""
import csv,hashlib,json,sys
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;OUT=BASE/'output';OLD=BASE.parent/'output';ROOT=BASE.parent.parent
sys.path.insert(0,str(BASE))
from candidate_policy import load_relations,Expander,freeze_configuration

def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,rs):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def fill_to_budget(rules,ranking,n):
    c=set(rules)
    for t in ranking:
        if len(c)>=n:break
        c.add(t)
    assert len(c)==n
    return c

def main():
    frozen=json.loads((OUT/'configuration_frozen_before_evaluation.json').read_text(encoding='utf-8'))
    assert frozen['configuration_sha256']==freeze_configuration(),'Configuration changed after generation'
    old=np.load(OLD/'retrieval_scores.npz');ja=np.load(OUT/'retrieval_scores.npz');ids=ja['problem_ids'].tolist();tags=ja['tag_ids'].tolist();assert old['problem_ids'].tolist()==ids and old['tag_ids'].tolist()==tags
    enrank=[[tags[j] for j in r] for r in np.argsort(-old['definition_scores'],axis=1,kind='stable')];jarank=[[tags[j] for j in r] for r in np.argsort(-ja['definition_scores'],axis=1,kind='stable')]
    rules={p:set(v) for p,v in json.loads((OLD/'rule_candidates.json').read_text(encoding='utf-8')).items()};guards=json.loads((OUT/'guard_evidence.json').read_text(encoding='utf-8'));expander=Expander(load_relations(set(tags)))
    sets={}
    for k in (5,10,20,40):
        methods=defaultdict(dict)
        for i,pid in enumerate(ids):
            en=rules[pid]|set(enrank[i][:k]);j=rules[pid]|set(jarank[i][:k]);expanded,_=expander.expand(j,guards[pid]);expanded_en,_=expander.expand(en,guards[pid])
            for name,c in [('en_hybrid',en),('ja_embedding',set(jarank[i][:k])),('ja_hybrid',j),('ja_expanded',expanded),('en_expanded',expanded_en),('ja_budget_matched',fill_to_budget(rules[pid],jarank[i],len(expanded))),('en_budget_matched',fill_to_budget(rules[pid],enrank[i],len(expanded)))]:methods[f'{name}_top{k}'][pid]=c
        sets.update(methods)
    # Candidate construction above has not opened any problem assignment labels.
    refs={r['problem_id']:r for r in map(json.loads,(ROOT/'output_v4/problems_tagged.jsonl').open(encoding='utf-8'))};gold={p:set(r['tag_ids']) for p,r in refs.items()};assert set(gold)==set(ids)
    support=Counter(t for g in gold.values() for t in g);profiles={p['tag_id']:p for p in json.loads((OUT/'tag_profiles.json').read_text(encoding='utf-8'))};summary=[];per=[];pertag=[];roles=[]
    for method,collection in sets.items():
        hit=Counter();selected=Counter();role=Counter();rh=Counter();sizes=[];whole=0
        for pid,c in collection.items():
            g=gold[pid];hit.update(c&g);selected.update(c);sizes.append(len(c));whole+=bool(g) and g<=c
            for t in g:
                r=refs[pid]['labels'][t][0]['role'];role[r]+=1;rh[r]+=t in c
            per.append(dict(method=method,problem_id=pid,candidate_count=len(c),reference_pairs=len(g),covered_pairs=len(c&g),missed_tag_ids=' | '.join(sorted(g-c))))
        total=sum(support.values());summary.append(dict(method=method,reference='V4_AI_silver_not_human_gold',candidate_count_mean=float(np.mean(sizes)),candidate_count_p95=float(np.quantile(sizes,.95)),candidate_count_max=max(sizes),reference_pairs=total,covered_reference_pairs=sum(hit.values()),micro_candidate_recall=sum(hit.values())/total,macro_seen_tag_recall=float(np.mean([hit[t]/n for t,n in support.items()])),all_tags_covered_nonempty_problems=whole,all_tags_covered_nonempty_fraction=whole/sum(bool(g) for g in gold.values())))
        for t in tags:pertag.append(dict(method=method,tag_id=t,tag=profiles[t]['tag'],reference_pairs=support[t],covered_pairs=hit[t],recall=hit[t]/support[t] if support[t] else '',selected_problems=selected[t]))
        for r,n in role.items():roles.append(dict(method=method,role=r,reference_pairs=n,covered_pairs=rh[r],recall=rh[r]/n))
    write(OUT/'candidate_metrics.csv',summary);write(OUT/'coverage_by_problem.csv',per);write(OUT/'tag_metrics.csv',pertag);write(OUT/'role_metrics.csv',roles)
    pairs=[]
    for pid in ids:
        oldc=sets['en_hybrid_top20'][pid];seed=sets['ja_hybrid_top20'][pid];new=sets['ja_expanded_top20'][pid];g=gold[pid];matched=sets['ja_budget_matched_top20'][pid]
        pairs.append(dict(problem_id=pid,title=refs[pid]['title'],old_candidate_count=len(oldc),ja_seed_count=len(seed),ja_expanded_count=len(new),reference_pairs=len(g),old_covered=len(g&oldc),ja_seed_covered=len(g&seed),new_covered=len(g&new),regained_vs_old=' | '.join(sorted((new-oldc)&g)),lost_vs_old=' | '.join(sorted((oldc-new)&g)),relation_gains_vs_matched=' | '.join(sorted((new-matched)&g)),relation_losses_vs_matched=' | '.join(sorted((matched-new)&g)),remaining_missing=' | '.join(sorted(g-new))))
    write(OUT/'paired_changes_top20.csv',pairs)
    priority=[r for r in pertag if r['tag_id'] in ('T026','T029','T066','T067','T055','T022') and r['method'].endswith('top20')]
    save(OUT/'priority_tags.json',priority)
    def compare(a,b):
        gains=sum(len((sets[b][p]-sets[a][p])&gold[p]) for p in ids);losses=sum(len((sets[a][p]-sets[b][p])&gold[p]) for p in ids)
        return dict(from_method=a,to_method=b,gained_reference_pairs=gains,lost_reference_pairs=losses,net=gains-losses,exactly_same_candidates_per_problem=all(len(sets[a][p])==len(sets[b][p]) for p in ids))
    comparisons=[compare('en_hybrid_top20','ja_hybrid_top20'),compare('ja_hybrid_top20','ja_expanded_top20'),compare('ja_budget_matched_top20','ja_expanded_top20'),compare('en_budget_matched_top20','ja_expanded_top20')]
    result=dict(reference='V4 AI silver, not human gold or final LLM precision/F1',problem_count=len(ids),reference_pairs=sum(support.values()),reference_sha256=hashlib.sha256((ROOT/'output_v4/problems_tagged.jsonl').read_bytes()).hexdigest(),configuration_sha256=frozen['configuration_sha256'],metrics=summary,paired_comparisons=comparisons,limitations=['Development experiment on the same 3012 problems, with policy informed by prior diagnostics; not an untouched test.','Relations generate hypotheses only; feasibility and final precision remain unmeasured.','Same frozen text chunks, model, prefixes and rule candidates reused; corpus-scope limitations remain.'])
    save(OUT/'silver_evaluation.json',result)
    print(json.dumps(dict(metrics=[r for r in summary if r['method'].endswith('top20')],priority_tags=[r for r in priority if r['tag_id'] in ('T026','T029')],paired_comparisons=comparisons),ensure_ascii=False))
if __name__=='__main__':main()
