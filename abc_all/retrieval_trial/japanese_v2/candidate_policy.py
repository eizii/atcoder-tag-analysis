"""Label-independent directed candidate relations, never tag assignments."""
import hashlib,json,re,sys
from collections import defaultdict,deque
from pathlib import Path
BASE=Path(__file__).resolve().parent;TRIAL=BASE.parent
sys.path.insert(0,str(BASE))
from policy import adoption_policy,GLOBAL_ADOPT,GLOBAL_EXCLUDE

GUARDS={
 'stochastic':r'確率|等確率|期待値|確率変数|ランダム|サイコロ|\bprobability\b|\bexpectation\b|\brandom\b',
 'counting':r'個数|通り|何種類|数え上げ|数える|総数|\bcount\b',
 'modular':r'998244353|1000000007|\\bmod|\bmod\b|逆元|剰余',
 'subset_or_order':r'部分集合|順列|順番|並べ替え|並び替え|選ぶ|選択|\bsubset\b|\bpermutation\b',
 'shortest_path':r'最短|最小の回数|最小回数|最小の辺数|最小の移動|深さ|\bshortest\b',
 'range_query':r'区間|クエリ|問い合わせ|\brange\b|\bquery\b',
 'xor_convolution':r'XOR\s*畳み込み|排他的論理和.*畳み込み|xor\s*convolution',
 'polynomial':r'多項式|母関数|形式的|冪級数|べき級数|polynomial|power\s*series',
}

def load_profiles():
    old=json.loads((TRIAL/'output/tag_profiles.json').read_text(encoding='utf-8'))
    lines=[l for l in (BASE/'definitions_ja.tsv').read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    definitions=dict(l.split('|',1) for l in lines)
    assert len(lines)==len(definitions)==266 and set(definitions)=={p['tag_id'] for p in old}
    result=[]
    for p in old:
        pol=adoption_policy(p['tag_id'])
        result.append(dict(tag_id=p['tag_id'],tag=p['tag'],aliases=p['aliases'],definition=definitions[p['tag_id']],adopt_when=pol['adopt_when'],do_not_adopt_when=pol['do_not_adopt_when']))
    return result

def load_relations(tag_ids):
    edges=[];seen=set()
    for l in (BASE/'relations.tsv').read_text(encoding='utf-8-sig').splitlines():
        if not l.strip():continue
        source,targets,kind,guard,reason=l.split('|')
        assert source in tag_ids and kind in {'parent','support','possible_variant'} and (guard=='always' or guard in GUARDS)
        for target in targets.split():
            assert target in tag_ids and source!=target
            key=(source,target,kind,guard);assert key not in seen;seen.add(key)
            assert kind!='parent' or guard=='always'
            edges.append(dict(relation_id=f'R{len(edges)+1:03d}',source_tag_id=source,target_tag_id=target,kind=kind,guard=guard,reason=reason,candidate_only=True))
    parents=defaultdict(list)
    for e in edges:
        if e['kind']=='parent':parents[e['source_tag_id']].append(e['target_tag_id'])
    def visit(t,path):
        assert t not in path,('parent_cycle',path,t)
        for parent in parents[t]:visit(parent,path+[t])
    for t in tag_ids:visit(t,[])
    # Similarity must never turn BFS into DFS, or the reverse.
    assert not any({e['source_tag_id'],e['target_tag_id']}=={'T066','T067'} for e in edges)
    return edges

def collect_guards(source_texts):
    result={'always':dict(passed=True)}
    for name,pattern in GUARDS.items():
        result[name]=dict(passed=False)
        for source in source_texts:
            text=source['text'].split('入力例')[0] if source['source_id']=='statement' else source['text']
            match=re.search(pattern,text,re.I)
            if match:
                result[name]=dict(passed=True,source_id=source['source_id'],matched=match.group(),excerpt=text[max(0,match.start()-35):match.end()+60],quote_admissible=False)
                break
    return result

class Expander:
    def __init__(self,edges):
        self.adj=defaultdict(list);self.parents=defaultdict(list)
        for e in edges:
            self.adj[e['source_tag_id']].append(e)
            if e['kind']=='parent':self.parents[e['source_tag_id']].append(e)
    def expand(self,seeds,guards):
        """One hop of optional/support links; transitive closure of parents only."""
        original=set(seeds);result=set(original);reasons=defaultdict(list);path={t:[] for t in original}
        def add(e,origin_path):
            t=e['target_tag_id'];trail=origin_path+[e['relation_id']]
            if t not in result:path[t]=trail
            result.add(t)
            if t not in original:reasons[t].append(dict(e,path=trail,guard_evidence=guards[e['guard']]))
        for t in sorted(original):
            for e in self.adj[t]:
                if guards[e['guard']]['passed']:add(e,[])
        queue=deque(sorted(result));processed=set()
        while queue:
            t=queue.popleft()
            if t in processed:continue
            processed.add(t)
            for e in self.parents[t]:
                target=e['target_tag_id'];new=target not in result;add(e,path[t])
                if new:queue.append(target)
        assert original<=result and set(reasons)==result-original
        return result,dict(reasons)

def freeze_configuration():
    files=['definitions_ja.tsv','relations.tsv','policy.py','candidate_policy.py','generate.py']
    return {name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in files}
