import runpy
import author_shard_1 as a
def check(entries):
 for pid,tags,anchor,reason,gap,source in entries:
  t=a.D[pid]['statement'] if source=='statement' else a.D[pid]['editorials'][source]['text']
  if a.norm(anchor) not in a.norm(t):print(pid,repr(anchor))
a.save=check
runpy.run_path('abc_all/full_review/append_shard_1_1470.py')













