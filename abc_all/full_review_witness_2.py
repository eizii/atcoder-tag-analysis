from itertools import permutations
import json
from pathlib import Path
lines=[(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
def mask_dp(a):
 dp=[0]*512;dp[0]=1
 for mask in range(511):
  for v in range(9):
   if mask>>v&1:continue
   if any(v in line and sum(bool(mask>>x&1) for x in line)==1 and any((mask>>x&1) and a[x]==a[v] for x in line) for line in lines):continue
   dp[mask|1<<v]+=dp[mask]
 return dp[-1]
def enumeration(a):
 total=0
 for p in permutations(range(9)):
  rank=[0]*9
  for i,x in enumerate(p):rank[x]=i
  bad=False
  for line in lines:
   x,y,z=sorted(line,key=rank.__getitem__)
   if a[x]==a[y] and a[x]!=a[z]:bad=True;break
  total+=not bad
 return total
cases=[list(range(9)),[1,1,2,3,4,5,6,7,8],[1,2,1,2,3,3,4,5,6]];results=[]
for a in cases:
 x=mask_dp(a);y=enumeration(a);assert x==y,(a,x,y);results.append({'board':a,'valid_orders':x,'permutations':362880})
Path('abc_all/full_review/shard_2_probability_witnesses.json').write_text(json.dumps({'checks_passed':True,'problem_id':'abc319_c','meaning':'dp[mask] counts unrejected revelation orders; divide each transition by 9-popcount(mask) for probability DP.','cases':results},indent=2)+'\n',encoding='utf-8')
print(results)
