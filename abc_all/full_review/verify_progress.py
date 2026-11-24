"""Validate saved per-problem review records and expose exact remaining work."""
import csv,json,hashlib,re
from pathlib import Path
from collections import Counter
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from tag_all import normalize
R=Path(__file__).resolve().parent.parent;W=R/'full_review'
M=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems'];D={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))};T={t['tag_id'] for t in json.loads((R/'taxonomy.json').read_text(encoding='utf-8'))}
rows=[];checks=[];errors=[];seen=set()
for i in range(4):
 f=W/f'shard_{i}.tsv'
 if not f.exists():continue
 data=list(csv.DictReader(f.open(encoding='utf-8-sig',newline=''),delimiter='\t'))
 for r in data:
  pid=r['problem_id'];d=D[pid]
  assert pid not in seen,('duplicate',pid)
  seen.add(pid)
  if r['source_indices']=='statement':source=d['statement']
  elif r['source_indices']=='match':source='\n'.join(e['text'] for e in d['editorials'])
  else:source='\n'.join(d['editorials'][int(j)]['text'] for j in r['source_indices'].split(','))
  ok=normalize(r['evidence_quote']) in normalize(source)
  if not ok:errors.append(dict(problem_id=pid,issue='quote_not_found',quote=r['evidence_quote']))
  for a in r['accepted'].split(','):
   if not a:continue
   tid,role=a.split(':');assert tid in T and role in {'primary','alternative','supporting','concept','analysis_concept'},(pid,a)
  assert len(r['reason'])>=10,(pid,'missing reason')
  if r.get('review_status','reviewed')=='reviewed':assert r['scope']=='full',(pid,'reviewed not full')
  r['shard']=i;rows.append(r)
 checks.append(dict(shard=i,rows=len(data),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
by={r['problem_id']:r for r in rows}
plan=json.loads((W/'root_resolution_plan.json').read_text(encoding='utf-8'))
for owner in ('root','agent_0','agent_2'):
 f=W/f'root_resolution_{owner.removeprefix("agent_") if owner.startswith("agent_") else owner}.tsv'
 if not f.exists():continue
 data=list(csv.DictReader(f.open(encoding='utf-8-sig',newline=''),delimiter='\t'))
 local_seen=set()
 for r in data:
  pid=r['problem_id'];assert (pid in plan[owner] or (owner=='agent_0' and pid=='abc426_g')) and pid not in local_seen,(owner,pid)
  local_seen.add(pid);assert pid in by and r['scope']=='full' and r['review_status']=='reviewed',(owner,pid)
  d=D[pid]
  source=d['statement'] if r['source_indices']=='statement' else '\n'.join(e['text'] for e in d['editorials']) if r['source_indices']=='match' else '\n'.join(d['editorials'][int(j)]['text'] for j in r['source_indices'].split(','))
  if normalize(r['evidence_quote']) not in normalize(source):errors.append(dict(problem_id=pid,issue='override_quote_not_found'))
  for a in filter(None,r['accepted'].split(',')):
   tid,role=a.split(':');assert tid in T and role in {'primary','alternative','supporting','concept','analysis_concept'},(pid,a)
  assert len(r['reason'])>=10,(pid,'missing override reason')
  r['shard']=3;by[pid]=r
 checks.append(dict(resolution_owner=owner,rows=len(data),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
coverage=[]
for n,p in enumerate(M):
 r=by.get(p['problem_id']);status=r.get('review_status','reviewed') if r else 'not_started'
 coverage.append(dict(manifest_index=n,problem_id=p['problem_id'],title=p['title'],review_status=status,shard=n//750 if n<2250 else 3,next_action='確認済みの解法について統合照合' if status=='reviewed' else r.get('uncertainty','') if r else '問題文・満点解説の個別確認'))
with (W/'coverage.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(coverage[0]));w.writeheader();w.writerows(coverage)
counts=Counter(r['review_status'] for r in coverage)
summary=dict(task_status='complete' if counts['reviewed']==len(M) and not errors else 'in_progress',target_problems=len(M),saved_problem_decisions=len(rows),coverage=dict(counts),source_quote_errors=errors,shards=checks,limits='Review completion means the recorded reference solutions were assessed, not every possible alternative or an independent gold-label accuracy estimate.')
(W/'progress.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
