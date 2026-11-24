from pathlib import Path
p=Path('abc_all/full_review/verify_progress.py')
s=p.read_text(encoding='utf-8-sig')
s=s.replace("by={r['problem_id']:r for r in rows};coverage=[]",'''by={r['problem_id']:r for r in rows}
plan=json.loads((W/'root_resolution_plan.json').read_text(encoding='utf-8'))
for owner in ('root','agent_0','agent_2'):
 f=W/f'root_resolution_{owner.removeprefix("agent_") if owner.startswith("agent_") else owner}.tsv'
 if not f.exists():continue
 data=list(csv.DictReader(f.open(encoding='utf-8-sig',newline=''),delimiter='\\t'))
 local_seen=set()
 for r in data:
  pid=r['problem_id'];assert pid in plan[owner] and pid not in local_seen,(owner,pid)
  local_seen.add(pid);assert pid in by and r['scope']=='full' and r['review_status']=='reviewed',(owner,pid)
  d=D[pid]
  source=d['statement'] if r['source_indices']=='statement' else '\\n'.join(e['text'] for e in d['editorials']) if r['source_indices']=='match' else '\\n'.join(d['editorials'][int(j)]['text'] for j in r['source_indices'].split(','))
  if normalize(r['evidence_quote']) not in normalize(source):errors.append(dict(problem_id=pid,issue='override_quote_not_found'))
  for a in filter(None,r['accepted'].split(',')):
   tid,role=a.split(':');assert tid in T and role in {'primary','alternative','supporting','concept','analysis_concept'},(pid,a)
  assert len(r['reason'])>=10,(pid,'missing override reason')
  r['shard']=3;by[pid]=r
 checks.append(dict(resolution_owner=owner,rows=len(data),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
coverage=[]''')
p.write_text(s,encoding='utf-8-sig')
