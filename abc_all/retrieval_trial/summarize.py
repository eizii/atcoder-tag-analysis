"""Export readable diagnostics and a static research plot from frozen results."""
import csv,json
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parent;OUT=BASE/'output'
def rows(name):return list(csv.DictReader((OUT/name).open(encoding='utf-8-sig')))
def jsonrows(name):return [json.loads(l) for l in (OUT/name).open(encoding='utf-8')]
def main():
    profiles=json.loads((OUT/'tag_profiles.json').read_text(encoding='utf-8'));names={p['tag_id']:p['tag'] for p in profiles};candidates=jsonrows('candidates.jsonl');ref={r['problem_id']:set(r['tag_ids']) for r in map(json.loads,(BASE.parent/'output_v4/problems_tagged.jsonl').open(encoding='utf-8'))};support=Counter(t for tags in ref.values() for t in tags);per=[];freq=Counter()
    for method in ('rules','definitions_top20','hybrid_top20','hybrid_top40'):
        hits=Counter();selected=Counter()
        for r in candidates:
            c=set(r['rule_tag_ids']) if method=='rules' else {v['tag_id'] for v in r['embedding_ranking'][:40 if method.endswith('40') else 20]}
            if method.startswith('hybrid'):c|=set(r['rule_tag_ids'])
            selected.update(c);hits.update(c&ref[r['problem_id']])
        for t in names:per.append(dict(method=method,tag_id=t,tag=names[t],reference_pairs=support[t],covered_pairs=hits[t],recall=hits[t]/support[t] if support[t] else '',selected_problems=selected[t]))
        if method=='definitions_top20':freq=selected
    with (OUT/'candidate_tag_metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(per[0]));w.writeheader();w.writerows(per)
    pilot={r['custom_id']:r for r in jsonrows('pilot_requests_scoped.jsonl')};control={r['custom_id']:r for r in jsonrows('pilot_all266_requests.jsonl')};early={r['custom_id']:r for r in jsonrows('early_pilot_requests.jsonl')} if (OUT/'early_pilot_requests.jsonl').exists() else {};size=[];changed=[]
    for pid,r in pilot.items():
        a=sum(len(m['content']) for m in r['messages']);b=sum(len(m['content']) for m in control[pid]['messages']);size.append(dict(problem_id=pid,hybrid_input_characters=a,all266_input_characters=b,character_ratio=a/b))
        c=lambda q:{t['tag_id'] for t in json.loads(q['messages'][1]['content'])['candidates']}
        if pid in early and c(r)!=c(early[pid]):changed.append(pid)
    out=dict(pilot_size=len(size),not_random_sample=True,measure='Unicode characters of system and user contents; NOT model tokens, cost or latency',mean_character_ratio=float(np.mean([r['character_ratio'] for r in size])),rows=size,early_candidate_comparison_available=bool(early),early_vs_final_candidate_set_differences=changed,most_frequent_embedding_candidates=[dict(tag_id=t,tag=names[t],problems=n,reference_pairs=support[t]) for t,n in freq.most_common(12)])
    (OUT/'diagnostic_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    primary=rows('candidate_metrics.csv');lex=rows('lexical_candidate_metrics.csv')
    fig,ax=plt.subplots(figsize=(9.3,5.6));colors=['#999999','#21918c','#2166ac','#e08214','#762a83']
    for prefix,label,data,col in [('names_top','Name embeddings',primary,colors[0]),('definitions_top','Definition embeddings',primary,colors[1]),('hybrid_top','Rules + embeddings',primary,colors[2]),('lexical_rules_top','Rules + char TF-IDF',lex,colors[3]),('lexical_embedding_rules_top','Rules + both searches',lex,colors[4])]:
        rr=[r for r in data if r['method'].startswith(prefix)];x=[float(r['candidate_count_mean']) for r in rr];y=[100*float(r['micro_candidate_recall']) for r in rr];ax.plot(x,y,'o-',label=label,color=col,lw=2,ms=5)
    rule=next(r for r in primary if r['method']=='rules');ax.scatter([float(rule['candidate_count_mean'])],[100*float(rule['micro_candidate_recall'])],marker='D',s=45,color='#111111',label='Rules only',zorder=5)
    ax.axhline(100,color='#555555',ls=':',lw=1);ax.set(xlim=(0,80),ylim=(0,103),xlabel='Mean candidates per problem (266 possible tags)',ylabel='Candidate recall vs. V4 AI silver labels (%)',title='AtCoder 3,012 problems: candidate coverage / candidate budget')
    ax.grid(alpha=.22);ax.legend(loc='lower right',fontsize=9);fig.text(.12,.015,'Diagnostic only: no human gold, no final LLM accuracy; exploratory lexical controls use unlabelled IDF.',fontsize=8,color='#555555');fig.tight_layout(rect=(0,.035,1,1));fig.savefig(OUT/'candidate_tradeoff.png',dpi=180);fig.savefig(OUT/'candidate_tradeoff.svg');plt.close(fig)
    print(json.dumps(dict(probability_and_expectation=[r for r in per if r['tag_id'] in ('T026','T029')],most_frequent_candidates=out['most_frequent_embedding_candidates'][:5],pilot_character_ratio=out['mean_character_ratio'],early_final_differences=changed),ensure_ascii=False))
if __name__=='__main__':main()
