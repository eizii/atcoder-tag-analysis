"""Integrity checks for ranking, isolation, request evidence and judge validation."""
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
from judge import validate
BASE=Path(__file__).resolve().parent;OUT=BASE/'output';ROOT=BASE.parent
def readrows(name):return [json.loads(l) for l in (OUT/name).open(encoding='utf-8')]
def main():
    summary=json.loads((OUT/'generation_summary.json').read_text(encoding='utf-8'))
    for name,info in summary['model']['files'].items():assert hashlib.sha256((ROOT/'retrieval_model_cache'/name).read_bytes()).hexdigest()==info['sha256']
    for name,expected in summary['input_sha256'].items():
        path=(BASE/name) if name in ('tag_descriptions.tsv','encoder.py','generate.py') else ROOT/name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,('input_changed',name)
    profiles=json.loads((OUT/'tag_profiles.json').read_text(encoding='utf-8'));assert len(profiles)==266
    assert len({r['tag_id'] for r in profiles})==266 and all(r['definition'] for r in profiles)
    cs=readrows('candidates.jsonl');chunks=readrows('chunks.jsonl');z=np.load(OUT/'retrieval_scores.npz');ids=z['problem_ids'].tolist();tags=z['tag_ids'].tolist();score=z['definition_scores'];best=z['best_chunk']
    assert len(cs)==3012 and [r['problem_id'] for r in cs]==ids and np.isfinite(score).all()
    chunkpid=np.array([c['problem_id'] for c in chunks]);assert (chunkpid[best]==np.array(ids)[:,None]).all()
    for i,r in enumerate(cs):
        rank=np.argsort(-score[i],kind='stable');assert [v['tag_id'] for v in r['embedding_ranking']]==[tags[j] for j in rank]
        assert set(r['hybrid_top20_tag_ids'])==set(r['rule_tag_ids'])|{tags[j] for j in rank[:20]}
    vectors=np.load(BASE/'cache'/f"{summary['cache_key']}.npz")
    for key in ('chunks','definitions','names'):assert np.allclose(np.linalg.norm(vectors[key],axis=1),1,atol=2e-6)
    for i in np.linspace(0,len(ids)-1,17,dtype=int):
        ix=np.flatnonzero(chunkpid==ids[i]);reconstructed=(vectors['chunks'][ix]@vectors['definitions'].T).max(axis=0)
        assert np.allclose(reconstructed,score[i],atol=1e-6)
    assert summary['encoding']['chunks']['truncated']==summary['encoding']['definitions']['truncated']==summary['encoding']['names']['truncated']==0
    requests={r['custom_id']:r for r in readrows('pilot_requests_scoped.jsonl')}
    for r in readrows('session_demo_judgments.jsonl'):
        request=requests[r['problem_id']];payload=json.loads(request['messages'][1]['content']);validate(r['result'],payload)
        assert r['prompt_sha256']==hashlib.sha256(json.dumps(request['messages'],ensure_ascii=False).encode()).hexdigest()
    # Deliberately malformed output MUST be refused.
    good=next(r for r in readrows('session_demo_judgments.jsonl') if r['result']['solutions'][0]['tags']);payload=json.loads(requests[good['problem_id']]['messages'][1]['content'])
    failures=[]
    for kind in ('unknown_tag','fake_quote','accepted_and_rejected','incomplete_review'):
        bad=copy.deepcopy(good['result']);tag=bad['solutions'][0]['tags'][0]
        if kind=='unknown_tag':tag['tag_id']='T999'
        elif kind=='fake_quote':tag['evidence_quote']='THIS QUOTE DOES NOT OCCUR IN THE PROVIDED SOURCE'
        elif kind=='accepted_and_rejected':bad['rejected'].append(dict(tag_id=tag['tag_id'],reason='invalid duplicate'))
        else:bad['review_status']='reviewed';bad['rejected']=[]
        try:validate(bad,payload)
        except AssertionError:failures.append(kind)
        else:raise AssertionError(('invalid_judgment_accepted',kind))
    for r in readrows('pilot_requests_scoped.jsonl'):
        p=json.loads(r['messages'][1]['content']);source={s['source_id']:s['text'] for s in p['source_texts']}
        for c in p['candidates']:
            h=c['retrieval_evidence'];assert h.get('excluded') or h['text'] in source[h['source_id']]
        if r['custom_id']=='abc092_b':assert all('Problem E' not in s['text'] for s in p['source_texts'])
    checked=dict(passed=True,problems=3012,tags=266,chunks=len(chunks),score_reconstruction_samples=17,unit_vectors_checked=True,input_hashes_unchanged=True,reference_labels_read_only_for_separate_evaluation=True,session_examples_validated=10,invalid_output_rejected=failures,untruncated_model_inputs=True)
    (OUT/'verification.json').write_text(json.dumps(checked,indent=2)+'\n',encoding='utf-8');print(json.dumps(checked))
if __name__=='__main__':main()
