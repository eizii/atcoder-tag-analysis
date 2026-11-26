"""Readable definitions, relation documentation, remaining misses and research plot."""
import csv,json
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parent;JA=BASE/'output';OUT=BASE/'bilingual_output';OLD=BASE.parent/'output';ROOT=BASE.parent.parent
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def main():
    profiles=json.loads((JA/'tag_profiles.json').read_text(encoding='utf-8'));names={p['tag_id']:p['tag'] for p in profiles};relations=json.loads((JA/'relations.json').read_text(encoding='utf-8'));adj=defaultdict(list)
    for r in relations:adj[r['source_tag_id']].append(r)
    kind={'parent':'上位概念','support':'補助手法の候補','possible_variant':'別解・関連解法の候補'}
    text=['# 266タグの日本語定義と採否条件','', '検索には肯定的な定義文だけを埋め込みます。除外条件はAIの最終判断に渡します。関連タグは候補であり、自動採用ではありません。','', '[比較結果と実行手順](README.md)','']
    for p in profiles:
        t=p['tag_id'];text.extend([f'<a id="{t}"></a>',f'## {t} {p["tag"]}','',p['definition'],'',f'採用条件：{p["adopt_when"]}','',f'除外条件：{p["do_not_adopt_when"]}',''])
        if adj[t]:
            text.append('追加を検討する候補：')
            text.append('')
            for r in adj[t]:
                dest=r['target_tag_id'];text.append(f'- [{dest} {names[dest]}](#{dest})：{kind[r["kind"]]}。条件 `{r["guard"]}`。{r["reason"]}')
            text.append('')
    (BASE/'tag_definitions_ja.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    relrows=[dict(relation_id=r['relation_id'],source_tag_id=r['source_tag_id'],source_tag=names[r['source_tag_id']],target_tag_id=r['target_tag_id'],target_tag=names[r['target_tag_id']],kind=r['kind'],guard=r['guard'],reason=r['reason'],candidate_only=True) for r in relations]
    with (BASE/'relations.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(relrows[0]));w.writeheader();w.writerows(relrows)
    refs={r['problem_id']:r for r in map(json.loads,(ROOT/'output_v4/problems_tagged.jsonl').open(encoding='utf-8'))};manifest={p['problem_id']:p for p in json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))['problems']};missing=[]
    for r in rows(OUT/'candidate_misses.csv'):
        for t in r['missing_tag_ids'].split(' | '):
            if t in ('T026','T029'):missing.append(dict(problem_id=r['problem_id'],title=r['title'],tag_id=t,tag=names[t],reference_role=refs[r['problem_id']]['labels'][t][0]['role'],url=manifest[r['problem_id']]['url']))
    with (OUT/'priority_remaining_misses.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['problem_id','title','tag_id','tag','reference_role','url']);w.writeheader();w.writerows(missing)
    primary=rows(JA/'candidate_metrics.csv');bilingual=rows(OUT/'candidate_metrics.csv');tagrows=rows(OUT/'tag_metrics.csv');tagja=rows(JA/'tag_metrics.csv')
    fig,(ax,bx)=plt.subplots(1,2,figsize=(13,5.6),gridspec_kw={'width_ratios':[1.25,1]})
    colors=['#777777','#e08214','#2166ac','#762a83']
    for prefix,label,color in [('en_hybrid_top','English + rules',colors[0]),('ja_hybrid_top','Japanese + rules',colors[1]),('ja_expanded_top','Japanese + rules + relations',colors[2])]:
        rr=[r for r in primary if r['method'].startswith(prefix)];ax.plot([float(r['candidate_count_mean']) for r in rr],[100*float(r['micro_candidate_recall']) for r in rr],'o-',lw=2,color=color,label=label)
    final=next(r for r in bilingual if r['method']=='bilingual_expanded20_each');control=next(r for r in bilingual if r['method']=='en_budget_matched');ax.scatter([float(final['candidate_count_mean'])],[100*float(final['micro_candidate_recall'])],marker='*',s=200,color=colors[3],label='Both languages + rules + relations',zorder=6);ax.scatter([float(control['candidate_count_mean'])],[100*float(control['micro_candidate_recall'])],marker='s',s=50,color=colors[0],label='English, exactly matched budget')
    ax.set(xlabel='Mean candidate tags per problem',ylabel='Candidate recall vs. V4 silver (%)',ylim=(40,100),title='Coverage and candidate budget');ax.grid(alpha=.2);ax.legend(fontsize=8,loc='lower right')
    methods=[('en_hybrid_top20','English',tagja),('ja_hybrid_top20','Japanese',tagja),('ja_expanded_top20','Japanese + relations',tagja),('bilingual_expanded20_each','Both + relations',tagrows)]
    for i,(method,label,data) in enumerate(methods):
        rr=[next(r for r in data if r['method']==method and r['tag_id']==t) for t in ('T029','T026')];x=[j+(i-1.5)*.18 for j in (0,1)];bars=bx.bar(x,[100*float(r['recall']) for r in rr],width=.17,color=colors[i],label=label)
        for bar,r in zip(bars,rr):bx.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1,f"{r['covered_pairs']}/{r['reference_pairs']}",ha='center',fontsize=8)
    bx.set(xticks=[0,1],xticklabels=['Probability DP','Expectation DP'],ylabel='Candidate recall vs. V4 silver (%)',ylim=(0,108),title='Priority tag families');bx.legend(fontsize=8,loc='lower right');bx.grid(axis='y',alpha=.2)
    fig.text(.5,.015,'3,012 problems; 7,708 AI silver pairs. Development diagnostics only, not independent gold or final LLM accuracy.',ha='center',fontsize=9,color='#555555');fig.tight_layout(rect=(0,.04,1,1));fig.savefig(OUT/'comparison.png',dpi=170);fig.savefig(OUT/'comparison.svg');plt.close(fig)
    print(json.dumps(dict(Japanese_definitions=len(profiles),typed_relations=len(relations),remaining_priority_misses=missing),ensure_ascii=False))
if __name__=='__main__':main()
