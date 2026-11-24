from pathlib import Path
p=Path('abc_all/full_review/verify_release.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace("main=keyed(read(O/'all_problems_tagged.csv'));", "manifest=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems']; aliases={p['contest_id']+'_'+p['problem_index'].lower():p['problem_id'] for p in manifest}; ids={p['problem_id'] for p in manifest}\nmain=keyed(read(O/'all_problems_tagged.csv'));")
s=s.replace("assert (pid,t) not in main,(pid,t,'known incidental/partial tag survived')", "pid=aliases.get(pid,pid);assert pid in ids,pid\n assert (pid,t) not in main,(pid,t,'known incidental/partial tag survived')")
p.write_text(s,encoding='utf-8-sig')
