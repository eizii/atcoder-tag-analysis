import csv,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'full_review/shard_1.tsv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
D={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))};M=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems'];tax={t['tag_id'] for t in json.loads((R/'taxonomy.json').read_text(encoding='utf-8'))}
from author_shard_1 import norm
rows=list(csv.DictReader(P.open(encoding='utf-8-sig'),delimiter='\t'));ids=[r['problem_id'] for r in rows];assert len(ids)==len(set(ids))
indices=sorted(next(i for i,p in enumerate(M) if p['problem_id']==pid) for pid in ids)
assert indices==list(range(750,750+len(rows)))
for r in rows:
 d=D[r['problem_id']];s=d['statement'] if r['source_indices']=='statement' else d['editorials'][int(r['source_indices'])]['text'];assert norm(r['evidence_quote']) in norm(s)
 assert r['scope']=='full' and r['review_status']=='reviewed'
 for assignment in filter(None,r['accepted'].split(',')):
  t,role=assignment.split(':');assert t in tax and role in {'primary','alternative','supporting','concept','analysis_concept'}
checkpoint=dict(shard=1,assigned_indices=[750,1499],authored_review_rows=len(rows),first_reviewed_index=750,last_reviewed_index=indices[-1],next_index=indices[-1]+1,remaining=750-len(rows),checks_passed=True,complete=len(rows)==750,independent_human_review=False,accuracy_estimate=None,source_corpus_sha256=sha(R/'corpus_sources.jsonl'),review_sha256=sha(P),notes=['各行は原文引用・具体解法・計算量を伴う個別判定。未読行は生成していない。','主解・別解・補助を含む。単なるループはシミュレーションとしない。','数学の式変形や基本算術で既存266語彙に合わない問題は無理なタグを付けない。','必要な続きの範囲はnext_index以降1499まで。'])
(R/'full_review/shard_1_checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checkpoint,ensure_ascii=False))
