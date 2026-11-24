import csv,json,hashlib,re
from pathlib import Path
R=Path('abc_all');p=R/'full_review/shard_2.tsv';rows=list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter='\t'));M=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems'];D={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))};T={t['tag_id'] for t in json.loads((R/'taxonomy.json').read_text(encoding='utf-8'))}
assert len(rows)==len({r['problem_id'] for r in rows})
assert {r['problem_id'] for r in rows}=={d['problem_id'] for d in M[1500:1500+len(rows)]}
for r in rows:
 d=D[r['problem_id']];source=d['statement'] if r['source_indices']=='statement' else d['editorials'][int(r['source_indices'])]['text'];assert r['evidence_quote'] in re.sub(r'\s+',' ',source),r['problem_id']
 for accepted in r['accepted'].split(',') if r['accepted'] else []:
  tag,role=accepted.split(':');assert tag in T and role in {'primary','alternative','supporting','concept','analysis_concept'}
 assert r['reason'] and len(r['reason'])>15
 assert r['review_status']=='reviewed' and not r['uncertainty']
report={'assigned_start_index':1500,'assigned_end_exclusive':2250,'saved_rows':len(rows),'completed_contiguous_end_exclusive':1500+len(rows),'remaining_start_index':1500+len(rows),'remaining_count':750-len(rows),'quotes_match':True,'unique_problem_ids':True,'taxonomy_and_roles_valid':True,'ledger_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'assigned_shard_complete' if len(rows)==750 else 'partial_checkpoint_not_complete','next_problem_id':M[1500+len(rows)]['problem_id'] if len(rows)<750 else None,'notes':[f'Indices 1500..{1499+len(rows)} were individually read using main editorial excerpts, with full sources for hard cases; existing alternatives were checked where relevant.','Full means recorded feasible reference methods, not a mathematical proof that all possible alternatives or every tag have been exhausted.',f'No decisions for indices {1500+len(rows)}..2249 have been made in this ledger; do not fill from keyword rules.','Potential cross-shard policy issues: roles for broad counting/strings, bit operations, structural concept tags and feasible independently derived alternatives need root consistency checks.']}
(R/'full_review/shard_2_checkpoint.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
