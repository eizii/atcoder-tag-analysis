"""Extract operational sentences for review; summaries are not review decisions."""
import argparse,json,csv,re,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('start',type=int);p.add_argument('end',type=int);p.add_argument('--ids',nargs='*');p.add_argument('--chars',type=int,default=680);a=p.parse_args()
M=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems'];D={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))};P={r['problem_id']:r for r in csv.DictReader((R/'output_v3_2/problems.csv').open(encoding='utf-8-sig'))}
key=re.compile(r'DP|dp|動的|探索|ソート|累積|畳み込み|連結|木|heap|queue|Fenwick|セグ|漸化|法|状態|定義|遷移|貪欲|最小|最大|計算量|回数|順番|順に|シミュレ|条件|数え|反転|帰着|行列|重複|周期|場合|等しい|取り除|答え|全て|すべて',re.I)
def simplify(s):
 s=re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s))
 s=re.sub(r'\\(?:mathrm|operatorname|text|mathbf|mathbb|boldsymbol|displaystyle|coloneqq|begin|end)(?:\{[^}]*\})?', '',s)
 s=s.replace('\\(','').replace('\\)','').replace('\\[','').replace('\\]','')
 s=re.sub(r'\\(?:leq|le|geq|ge|times|cdot|to|rightarrow|infty|frac|sum|prod|binom|subseteq|subset|dots|ldots|cdots|neq|lbrace|rbrace|left|right|qquad|quad|lt|gt|log|min|max|bmod)',lambda m:m.group()[1:],s)
 return s
for i,x in enumerate(M):
 if (x['problem_id'] not in a.ids) if a.ids else not(a.start<=i<a.end):continue
 d=D[x['problem_id']];sources=d['editorials'];t=simplify(sources[0]['text']) if sources else simplify(d['statement'].split('入力例')[0])
 sentences=re.split(r'(?<=[。？！])\s*',t)
 content=[s for s in sentences if key.search(s) and not re.search(r'practice|AtCoder Beginners|APG4b|初心者|学習を|プログラミングを始め|実装例|解答例|参考に',s)]
 # Preserve first setup, earliest operational sentences, and last complexity.
 chosen=content[:4]
 tail=[s for s in content[4:] if re.search(r'計算量|O\(',s)]
 if tail:chosen+=tail[-1:]
 desc=' '.join(chosen)[:a.chars] or t[:a.chars]
 print(f"{i} {x['problem_id']} {x['title']} [{P[x['problem_id']]['tag_ids']}] {desc}")
