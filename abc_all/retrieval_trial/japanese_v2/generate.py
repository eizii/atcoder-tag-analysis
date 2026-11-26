"""Japanese profiles and typed candidate expansion. Does NOT read V4 labels.

Reuse identical frozen corpus vectors so the language change is controlled and
the 19,814 corpus chunks need not be embedded again.
"""
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;TRIAL=BASE.parent;ROOT=TRIAL.parent;OLD=TRIAL/'output';OUT=BASE/'output'
sys.path.insert(0,str(TRIAL));sys.path.insert(0,str(BASE))
from encoder import Encoder
from candidate_policy import load_profiles,load_relations,collect_guards,Expander,freeze_configuration
from policy import GLOBAL_ADOPT,GLOBAL_EXCLUDE

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    start=time.perf_counter();OUT.mkdir(exist_ok=True);config=freeze_configuration();profiles=load_profiles();tagids=[p['tag_id'] for p in profiles];relations=load_relations(set(tagids));expander=Expander(relations)
    save(OUT/'configuration_frozen_before_evaluation.json',dict(configuration_sha256=config,scope='development experiment; design informed by prior English diagnostics, not untouched test',reference_assignments_used=False))
    summary=json.loads((OLD/'generation_summary.json').read_text(encoding='utf-8'))
    # Check unchanged model and corpus inputs, not assignment labels.
    for name,expected in summary['input_sha256'].items():
        path=TRIAL/name if name in ('encoder.py','generate.py','tag_descriptions.tsv') else ROOT/name
        assert sha(path)==expected,('baseline_input_changed',name)
    for name,info in summary['model']['files'].items():assert sha(ROOT/'retrieval_model_cache'/name)==info['sha256']
    cache=np.load(TRIAL/'cache'/f"{summary['cache_key']}.npz");cv=cache['chunks'];z=np.load(OLD/'retrieval_scores.npz');ids=z['problem_ids'].tolist();assert z['tag_ids'].tolist()==tagids
    chunks=[json.loads(l) for l in (OLD/'chunks.jsonl').open(encoding='utf-8')];assert len(chunks)==len(cv);index={p:i for i,p in enumerate(ids)}
    encoder=Encoder();texts=[p['tag']+'。'+p['definition']+'。別名: '+', '.join(p['aliases']) for p in profiles]
    lengths=[encoder.token_length('passage: '+t) for t in texts];assert max(lengths)<=encoder.max_length,('profile_too_long',[(tagids[i],n) for i,n in enumerate(lengths) if n>encoder.max_length])
    tv=encoder.encode(texts,prefix='passage: ');encoding=encoder.last_stats
    scores=np.full((len(ids),266),-np.inf,dtype=np.float32);best=np.full((len(ids),266),-1,dtype=np.int32)
    for offset in range(0,len(chunks),512):
        block=cv[offset:offset+512]@tv.T
        for j,values in enumerate(block):
            pi=index[chunks[offset+j]['problem_id']];take=values>scores[pi];scores[pi,take]=values[take];best[pi,take]=offset+j
    assert np.isfinite(scores).all() and (best>=0).all();rank=np.argsort(-scores,axis=1,kind='stable')
    np.savez_compressed(OUT/'retrieval_scores.npz',definition_scores=scores,best_chunk=best,problem_ids=np.array(ids),tag_ids=np.array(tagids),tag_vectors=tv)
    save(OUT/'tag_profiles.json',profiles);save(OUT/'relations.json',relations);pmap={p['tag_id']:p for p in profiles};tagindex={t:j for j,t in enumerate(tagids)}
    rules=json.loads((OLD/'rule_candidates.json').read_text(encoding='utf-8'));pilot=set(json.loads((OLD/'pilot_selection.json').read_text(encoding='utf-8'))['problem_ids']);save(OUT/'pilot_selection.json',json.loads((OLD/'pilot_selection.json').read_text(encoding='utf-8')))
    guard_records={};counts=[];seedcounts=[];n=0
    with (OUT/'candidates.jsonl').open('w',encoding='utf-8') as cf,(OUT/'llm_requests_scoped.jsonl').open('w',encoding='utf-8') as rf,(OUT/'pilot_requests_scoped.jsonl').open('w',encoding='utf-8') as pf:
        for r in map(json.loads,(OLD/'llm_requests_scoped.jsonl').open(encoding='utf-8')):
            pid=r['custom_id'];i=index[pid];payload=json.loads(r['messages'][1]['content']);guards=collect_guards(payload['source_texts']);guard_records[pid]=guards
            ranked=[dict(tag_id=tagids[j],score=float(scores[i,j]),best_chunk_id=int(best[i,j])) for j in rank[i]];seeds=set(rules[pid])|{x['tag_id'] for x in ranked[:20]};expanded,reasons=expander.expand(seeds,guards);counts.append(len(expanded));seedcounts.append(len(seeds))
            record=dict(problem_id=pid,rule_tag_ids=sorted(rules[pid]),embedding_ranking=ranked,hybrid_top20_tag_ids=sorted(seeds),expanded_tag_ids=sorted(expanded),expansion_reasons=reasons)
            cf.write(json.dumps(record,ensure_ascii=False)+'\n');by_source={s['source_id']:s['text'] for s in payload['source_texts']};offered=[]
            for t in sorted(expanded):
                hint=chunks[int(best[i,tagindex[t]])]
                if hint['text'] not in by_source.get(hint['source_id'],''):hint=dict(excluded=True,reason='not_in_judge_scoped_source')
                offered.append(dict(pmap[t],rule_evidence=[dict(h,quote_admissible=False) for h in rules[pid].get(t,[]) if h['source_id'] in by_source],retrieval_evidence=hint,relation_evidence=reasons.get(t,[])))
            payload.update(candidate_policy='Japanese positive definition top20 plus frozen V3 rules; one-hop related candidates and parent closure; no automatic assignment',candidates=offered)
            r['messages'][0]['content']+=' 共通採用基準: '+GLOBAL_ADOPT+' 共通除外条件: '+GLOBAL_EXCLUDE+' 関連タグの追加理由は候補生成の理由であり、採用の証拠ではありません。BFSとDFSを同一視しないでください。'
            r['messages'][1]['content']=json.dumps(payload,ensure_ascii=False);line=json.dumps(r,ensure_ascii=False)+'\n';rf.write(line)
            if pid in pilot:pf.write(line)
            n+=1
    assert n==3012
    save(OUT/'guard_evidence.json',guard_records);save(OUT/'artifact_paths.json',{'chunks.jsonl':'../../output/chunks.jsonl','rule_candidates.json':'../../output/rule_candidates.json'})
    save(OUT/'generation_summary.json',dict(created='2026-11-26',problem_count=n,taxonomy_count=266,model=summary['model'],baseline_generation_summary_sha256=sha(OLD/'generation_summary.json'),configuration_sha256=config,input_sha256={'chunks.jsonl':sha(OLD/'chunks.jsonl'),'scoped_requests':sha(OLD/'llm_requests_scoped.jsonl'),'rules':sha(OLD/'rule_candidates.json'),'baseline_scores':sha(OLD/'retrieval_scores.npz')},corpus_vectors_reused=summary['cache_key'],corpus_chunks=len(chunks),embedding_prefix='passage: ',positive_retrieval_view='same tag name and aliases as English baseline; only definition replaced by Japanese; exclusion text not embedded',encoding=encoding,max_profile_tokens=max(lengths),relation_count=len(relations),expansion_policy='one hop support and possible_variant from initial seeds; transitive parent closure; guarded by unlabelled scoped text; never final assignments',candidate_counts=dict(seed_mean=float(np.mean(seedcounts)),expanded_mean=float(np.mean(counts)),expanded_p95=float(np.quantile(counts,.95)),expanded_max=max(counts)),reference_assignments_used_for_generation=False,external_llm_api_calls=0,elapsed_seconds=time.perf_counter()-start))
    print(json.dumps(dict(problems=n,profiles=266,relations=len(relations),seed_mean=float(np.mean(seedcounts)),expanded_mean=float(np.mean(counts)),elapsed_seconds=round(time.perf_counter()-start,2))))
if __name__=='__main__':main()
