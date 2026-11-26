"""Unsupervised character TF-IDF control, added after the first diagnostic.

IDF uses all unlabelled target text (transductive exploratory setting). No tag
assignments are used to fit/rank. Silver assignments are loaded only to score.
"""
import csv,json,time
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
BASE=Path(__file__).resolve().parent;OUT=BASE/'output'
def main():
    start=time.perf_counter();profiles=json.loads((OUT/'tag_profiles.json').read_text(encoding='utf-8'));chunks=[json.loads(l) for l in (OUT/'chunks.jsonl').open(encoding='utf-8')];candidates=[json.loads(l) for l in (OUT/'candidates.jsonl').open(encoding='utf-8')]
    texts=[c['text'] for c in chunks];descs=[p['tag']+'。'+p['definition']+'。'+', '.join(p['aliases']) for p in profiles];ids=[r['problem_id'] for r in candidates];idx={p:i for i,p in enumerate(ids)};tagids=[p['tag_id'] for p in profiles]
    vectorizer=TfidfVectorizer(analyzer='char',ngram_range=(2,4),min_df=2,sublinear_tf=True,dtype=np.float32)
    vectors=vectorizer.fit_transform(texts+descs);cv=vectors[:len(chunks)];tv=vectors[len(chunks):];scores=np.zeros((len(ids),266),dtype=np.float32)
    for offset in range(0,len(chunks),512):
        block=(cv[offset:offset+512]@tv.T).toarray()
        for j,val in enumerate(block):
            pi=idx[chunks[offset+j]['problem_id']];scores[pi]=np.maximum(scores[pi],val)
    rank=np.argsort(-scores,axis=1,kind='stable');np.savez_compressed(OUT/'lexical_scores.npz',scores=scores,problem_ids=np.array(ids),tag_ids=np.array(tagids))
    # Only evaluation below reads reference assignments.
    gold={r['problem_id']:set(r['tag_ids']) for r in map(json.loads,(BASE.parent/'output_v4/problems_tagged.jsonl').open(encoding='utf-8'))};rows=[]
    for k in (5,10,20,40):
        for mode in ('lexical','lexical_rules','lexical_embedding_rules'):
            n=hit=allcovered=0;sizes=[]
            for i,r in enumerate(candidates):
                c={tagids[j] for j in rank[i,:k]}
                if mode!='lexical':c|=set(r['rule_tag_ids'])
                if mode=='lexical_embedding_rules':c|={v['tag_id'] for v in r['embedding_ranking'][:k]}
                g=gold[r['problem_id']];n+=len(g);hit+=len(c&g);allcovered+=bool(g) and g<=c;sizes.append(len(c))
            rows.append(dict(method=mode+f'_top{k}',candidate_count_mean=float(np.mean(sizes)),candidate_count_p95=float(np.quantile(sizes,.95)),reference_pairs=n,covered_reference_pairs=hit,micro_candidate_recall=hit/n,all_tags_covered_nonempty_fraction=allcovered/sum(bool(g) for g in gold.values()),reference='V4_AI_silver_not_human_gold'))
    with (OUT/'lexical_candidate_metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/'lexical_summary.json').write_text(json.dumps(dict(method='character TF-IDF cosine; max chunk aggregation',settings=vectorizer.get_params()|{'dtype':'float32'},features=len(vectorizer.vocabulary_),transductive_unlabelled_fit=True,exploratory_after_primary_diagnostic=True,elapsed_seconds=time.perf_counter()-start,metrics=rows),ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8');print(json.dumps(rows))
if __name__=='__main__':main()
