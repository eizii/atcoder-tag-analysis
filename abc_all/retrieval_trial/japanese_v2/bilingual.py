"""Non-destructive seed union: retain old English AND Japanese top20, then expand.

Added after the first Japanese-only diagnostic exposed losses. A development
iteration, not an independent test. No assignment-label file is opened here.
"""
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;JA=BASE/'output';OLD=BASE.parent/'output';OUT=BASE/'bilingual_output'
sys.path.insert(0,str(BASE))
from candidate_policy import Expander,load_relations,freeze_configuration

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    start=time.perf_counter();OUT.mkdir(exist_ok=True);frozen=json.loads((JA/'configuration_frozen_before_evaluation.json').read_text(encoding='utf-8'));assert frozen['configuration_sha256']==freeze_configuration()
    config=dict(parent_configuration_sha256=frozen['configuration_sha256'],bilingual_script_sha256=sha(Path(__file__)),seed_policy='union of English top20, Japanese top20 and original V3 rules',candidate_only=True,reference_assignments_used=False,development_iteration_after_Japanese_only_diagnostic=True)
    save(OUT/'configuration_frozen_before_evaluation.json',config)
    en=np.load(OLD/'retrieval_scores.npz');ja=np.load(JA/'retrieval_scores.npz');ids=ja['problem_ids'].tolist();tags=ja['tag_ids'].tolist();assert en['problem_ids'].tolist()==ids and en['tag_ids'].tolist()==tags
    es=en['definition_scores'];js=ja['definition_scores'];eb=en['best_chunk'];jb=ja['best_chunk']
    erank=np.argsort(-es,axis=1,kind='stable');jrank=np.argsort(-js,axis=1,kind='stable');idx={p:i for i,p in enumerate(ids)};ti={t:i for i,t in enumerate(tags)}
    profiles=json.loads((JA/'tag_profiles.json').read_text(encoding='utf-8'));pmap={p['tag_id']:p for p in profiles};edges=load_relations(set(tags));ex=Expander(edges);guards=json.loads((JA/'guard_evidence.json').read_text(encoding='utf-8'));rules=json.loads((OLD/'rule_candidates.json').read_text(encoding='utf-8'));chunks=[json.loads(l) for l in (OLD/'chunks.jsonl').open(encoding='utf-8')];pilot=json.loads((JA/'pilot_selection.json').read_text(encoding='utf-8'));counts=[];seedcounts=[]
    with (OUT/'candidates.jsonl').open('w',encoding='utf-8') as cf,(OUT/'llm_requests_scoped.jsonl').open('w',encoding='utf-8') as rf,(OUT/'pilot_requests_scoped.jsonl').open('w',encoding='utf-8') as pf:
        for r in map(json.loads,(JA/'llm_requests_scoped.jsonl').open(encoding='utf-8')):
            pid=r['custom_id'];i=idx[pid];payload=json.loads(r['messages'][1]['content']);e={tags[j] for j in erank[i,:20]};j={tags[v] for v in jrank[i,:20]};seeds=e|j|set(rules[pid]);expanded,reasons=ex.expand(seeds,guards[pid]);ja_expanded,_=ex.expand(j|set(rules[pid]),guards[pid]);assert ja_expanded<=expanded and e|set(rules[pid])<=expanded
            overrides={t:int(eb[i,ti[t]]) for t in e-j};origins={t:[origin for origin,s in [('english',e),('japanese',j),('rule',set(rules[pid]))] if t in s] for t in sorted(seeds)}
            ranked=[dict(tag_id=tags[v],score=float(js[i,v]),best_chunk_id=int(jb[i,v])) for v in jrank[i]]
            rec=dict(problem_id=pid,rule_tag_ids=sorted(rules[pid]),embedding_ranking=ranked,hybrid_top20_tag_ids=sorted(j|set(rules[pid])),seed_tag_ids=sorted(seeds),seed_origins=origins,expanded_tag_ids=sorted(expanded),expansion_reasons=reasons,evidence_chunk_overrides=overrides)
            cf.write(json.dumps(rec,ensure_ascii=False)+'\n');sources={s['source_id']:s['text'] for s in payload['source_texts']};offered=[]
            for t in sorted(expanded):
                ci=overrides.get(t,int(jb[i,ti[t]]));hint=chunks[ci]
                if hint['text'] not in sources.get(hint['source_id'],''):hint=dict(excluded=True,reason='not_in_judge_scoped_source')
                offered.append(dict(pmap[t],seed_origins=origins.get(t,[]),rule_evidence=[dict(h,quote_admissible=False) for h in rules[pid].get(t,[]) if h['source_id'] in sources],retrieval_evidence=hint,relation_evidence=reasons.get(t,[])))
            payload['candidates']=offered;payload['candidate_policy']='Retain English top20 AND Japanese top20 plus original V3 rules; one-hop related candidates and parent closure; no assignments';r['messages'][1]['content']=json.dumps(payload,ensure_ascii=False);line=json.dumps(r,ensure_ascii=False)+'\n';rf.write(line)
            if pid in pilot['problem_ids']:pf.write(line)
            counts.append(len(expanded));seedcounts.append(len(seeds))
    save(OUT/'tag_profiles.json',profiles);save(OUT/'pilot_selection.json',pilot);save(OUT/'relations.json',edges);save(OUT/'artifact_paths.json',{'chunks.jsonl':'../../output/chunks.jsonl','rule_candidates.json':'../../output/rule_candidates.json'})
    save(OUT/'generation_summary.json',dict(problem_count=len(ids),taxonomy_count=266,configuration=config,model=json.loads((JA/'generation_summary.json').read_text(encoding='utf-8'))['model'],input_sha256={'english_scores':sha(OLD/'retrieval_scores.npz'),'japanese_scores':sha(JA/'retrieval_scores.npz'),'Japanese_scoped_requests':sha(JA/'llm_requests_scoped.jsonl'),'guard_evidence':sha(JA/'guard_evidence.json')},candidate_counts=dict(seed_mean=float(np.mean(seedcounts)),expanded_mean=float(np.mean(counts)),expanded_p95=float(np.quantile(counts,.95)),expanded_max=max(counts)),prior_English_seeds_preserved_for_all_problems=True,Japanese_expanded_candidates_preserved_for_all_problems=True,reference_assignments_used_for_generation=False,external_llm_api_calls=0,elapsed_seconds=time.perf_counter()-start))
    print(json.dumps(dict(problems=len(ids),seed_mean=float(np.mean(seedcounts)),expanded_mean=float(np.mean(counts)))))
if __name__=='__main__':main()
