"""Exploratory E5 symmetric-prefix check; unchanged corpus vectors/rules.

The model card recommends query prefixes for semantic similarity. This is a
post-diagnostic ablation, not a model selected on untouched test data.
"""
import csv, hashlib, json, time
from pathlib import Path
import numpy as np
from encoder import Encoder
BASE=Path(__file__).resolve().parent;OUT=BASE/'output'
def main():
    start=time.perf_counter();summary=json.loads((OUT/'generation_summary.json').read_text(encoding='utf-8'))
    cache=np.load(BASE/'cache'/f"{summary['cache_key']}.npz");cv=cache['chunks']
    profiles=json.loads((OUT/'tag_profiles.json').read_text(encoding='utf-8'));chunks=[json.loads(l) for l in (OUT/'chunks.jsonl').open(encoding='utf-8')]
    candidates=[json.loads(l) for l in (OUT/'candidates.jsonl').open(encoding='utf-8')];ids=[r['problem_id'] for r in candidates];idx={p:i for i,p in enumerate(ids)};tagids=[p['tag_id'] for p in profiles]
    encoder=Encoder();tv=encoder.encode([p['tag']+'。'+p['definition']+'。別名: '+', '.join(p['aliases']) for p in profiles],prefix='query: ')
    scores=np.full((len(ids),266),-np.inf,dtype=np.float32)
    for offset in range(0,len(chunks),512):
        block=cv[offset:offset+512]@tv.T
        for j,val in enumerate(block):
            pi=idx[chunks[offset+j]['problem_id']];scores[pi]=np.maximum(scores[pi],val)
    assert np.isfinite(scores).all();np.savez_compressed(OUT/'symmetric_scores.npz',scores=scores,problem_ids=np.array(ids),tag_ids=np.array(tagids))
    # Reference assignments are only opened AFTER embeddings and rankings exist.
    gold={r['problem_id']:set(r['tag_ids']) for r in map(json.loads,(BASE.parent/'output_v4/problems_tagged.jsonl').open(encoding='utf-8'))};rank=np.argsort(-scores,axis=1,kind='stable');rows=[]
    for k in (5,10,20,40):
        for hybrid in (False,True):
            n=hit=allcovered=0;sizes=[]
            for i,r in enumerate(candidates):
                c={tagids[j] for j in rank[i,:k]}|(set(r['rule_tag_ids']) if hybrid else set());g=gold[r['problem_id']];n+=len(g);hit+=len(c&g);allcovered+=bool(g) and g<=c;sizes.append(len(c))
            rows.append(dict(method=('symmetric_hybrid' if hybrid else 'symmetric_definitions')+f'_top{k}',candidate_count_mean=float(np.mean(sizes)),reference_pairs=n,covered_reference_pairs=hit,micro_candidate_recall=hit/n,all_tags_covered_nonempty_fraction=allcovered/sum(bool(g) for g in gold.values()),reference='V4_AI_silver_not_human_gold'))
    with (OUT/'symmetric_candidate_metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/'prefix_variant_summary.json').write_text(json.dumps(dict(prefix='query: for both corpus and definitions',changed_only='tag definition prefix, reuses original corpus chunk vectors',model=summary['model'],encoding=encoder.last_stats,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),exploratory_after_primary_diagnostic=True,elapsed_seconds=time.perf_counter()-start,metrics=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(rows))
if __name__=='__main__':main()
