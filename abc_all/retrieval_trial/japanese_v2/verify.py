"""Verify preserved seeds, bounded expansion, provenance and final request inputs."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent;JA=BASE/'output';OUT=BASE/'bilingual_output';OLD=BASE.parent/'output'
sys.path.insert(0,str(BASE));sys.path.insert(0,str(BASE.parent))
from candidate_policy import Expander,load_profiles,load_relations,freeze_configuration,GUARDS
from judge import validate

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    frozen=json.loads((JA/'configuration_frozen_before_evaluation.json').read_text(encoding='utf-8'));assert frozen['configuration_sha256']==freeze_configuration()
    config=json.loads((OUT/'configuration_frozen_before_evaluation.json').read_text(encoding='utf-8'));assert config['parent_configuration_sha256']==frozen['configuration_sha256'] and config['bilingual_script_sha256']==sha(BASE/'bilingual.py')
    profiles=load_profiles();assert len(profiles)==266 and all(p['definition'] and p['adopt_when'] and p['do_not_adopt_when'] for p in profiles)
    tags=[p['tag_id'] for p in profiles];edges=load_relations(set(tags));edge_by={e['relation_id']:e for e in edges};ex=Expander(edges)
    no={g:dict(passed=False) for g in GUARDS};no['always']=dict(passed=True)
    yes={g:dict(passed=True) for g in ['always',*GUARDS]}
    b,_=ex.expand({'T066'},no);assert b=={'T066','T011'} and 'T067' not in b
    b,_=ex.expand({'T066'},yes);assert 'T055' in b and 'T067' not in b
    d,_=ex.expand({'T067'},yes);assert {'T080','T013'}<=d and 'T066' not in d
    p,_=ex.expand({'T022'},no);assert not p&{'T026','T029'}
    p,_=ex.expand({'T022'},yes);assert {'T026','T029'}<=p
    e,_=ex.expand({'T065'},yes);assert {'T017','T029','T022','T060'}<=e and 'T026' not in e and 'T236' not in e,'optional links must not cascade'
    p,_=ex.expand({'T232'},no);assert {'T231','T032'}<=p,'transitive parent closure missing'
    z=np.load(JA/'retrieval_scores.npz');old=np.load(OLD/'retrieval_scores.npz');ids=z['problem_ids'].tolist();scores=z['definition_scores'];best=z['best_chunk'];er=np.argsort(-old['definition_scores'],axis=1,kind='stable');jr=np.argsort(-scores,axis=1,kind='stable');rules=json.loads((OLD/'rule_candidates.json').read_text(encoding='utf-8'));guards=json.loads((JA/'guard_evidence.json').read_text(encoding='utf-8'))
    original=json.loads((OLD/'generation_summary.json').read_text(encoding='utf-8'));vectors=np.load(BASE.parent/'cache'/f"{original['cache_key']}.npz");cv=vectors['chunks'];tv=z['tag_vectors'];chunks=[json.loads(l) for l in (OLD/'chunks.jsonl').open(encoding='utf-8')];cp=np.array([c['problem_id'] for c in chunks]);assert (cp[best]==np.array(ids)[:,None]).all();assert np.allclose(np.linalg.norm(tv,axis=1),1,atol=2e-6)
    for i in np.linspace(0,len(ids)-1,17,dtype=int):assert np.allclose((cv[cp==ids[i]]@tv.T).max(axis=0),scores[i],atol=1e-6)
    offered={};all_provenance=0
    for i,r in enumerate(map(json.loads,(OUT/'candidates.jsonl').open(encoding='utf-8'))):
        pid=r['problem_id'];assert pid==ids[i];en={tags[v] for v in er[i,:20]}|set(rules[pid]);jp={tags[v] for v in jr[i,:20]}|set(rules[pid]);seeds=en|jp;expected,reasons=ex.expand(seeds,guards[pid]);actual=set(r['expanded_tag_ids']);assert actual==expected and reasons==r['expansion_reasons'] and set(r['seed_tag_ids'])==seeds;assert en<=actual
        jp_expanded,_=ex.expand(jp,guards[pid]);assert jp_expanded<=actual
        for target,why in reasons.items():
            assert target not in seeds
            for proof in why:
                path=[edge_by[v] for v in proof['path']];assert path[0]['source_tag_id'] in seeds and path[-1]['target_tag_id']==target
                assert all(e['kind']=='parent' for e in path[1:])
                for before,after in zip(path,path[1:]):assert before['target_tag_id']==after['source_tag_id']
                assert all(e['candidate_only'] and guards[pid][e['guard']]['passed'] for e in path);all_provenance+=1
        offered[pid]=actual
    assert len(offered)==3012
    pmap={p['tag_id']:p for p in profiles};request_count=0;pilot={}
    for r in map(json.loads,(OUT/'llm_requests_scoped.jsonl').open(encoding='utf-8')):
        pid=r['custom_id'];payload=json.loads(r['messages'][1]['content']);cs=payload['candidates'];assert {c['tag_id'] for c in cs}==offered[pid] and len(cs)==len(offered[pid]);sources={s['source_id']:s['text'] for s in payload['source_texts']}
        for c in cs:
            assert c['definition']==pmap[c['tag_id']]['definition'] and c['do_not_adopt_when']==pmap[c['tag_id']]['do_not_adopt_when'];h=c['retrieval_evidence'];assert h.get('excluded') or h['text'] in sources[h['source_id']]
        if pid in {'abc007_3','abc263_e','abc319_c'}:pilot[pid]=r
        request_count+=1
    assert request_count==3012
    examples=list(map(json.loads,(OUT/'session_examples.jsonl').open(encoding='utf-8')))
    for r in examples:
        request=pilot[r['problem_id']];validate(r['result'],json.loads(request['messages'][1]['content']));assert r['prompt_sha256']==hashlib.sha256(json.dumps(request['messages'],ensure_ascii=False).encode()).hexdigest()
    reference=BASE.parent.parent/'output_v4/problems_tagged.jsonl';ev=json.loads((OUT/'silver_evaluation.json').read_text(encoding='utf-8'));assert sha(reference)==ev['reference_sha256']
    stats=json.loads((JA/'generation_summary.json').read_text(encoding='utf-8'));assert stats['encoding']['truncated']==0
    result=dict(passed=True,problems=3012,Japanese_profiles=266,typed_relations=len(edges),prior_English_seeds_preserved_all_problems=True,Japanese_expanded_candidates_preserved_all_problems=True,related_candidate_provenance_paths_checked=all_provenance,BFS_DFS_kept_distinct=True,optional_relations_do_not_cascade=True,parent_closure_checked=True,score_reconstruction_samples=17,scoped_requests_validated=request_count,session_examples_validated=len(examples),reference_unchanged=True,frozen_configuration_unchanged=True,external_llm_api_calls=0)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
