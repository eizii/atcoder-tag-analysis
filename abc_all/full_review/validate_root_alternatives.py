"""Independent small-case checks for full-review feasible alternatives."""
import itertools,json,random
from pathlib import Path
rng=random.Random(20261124);counts={}
def fwht(a):
 a=list(a);h=1
 while h<len(a):
  for k in range(0,len(a),2*h):
   for j in range(k,k+h):
    x,y=a[j],a[j+h];a[j]=x+y;a[j+h]=x-y
  h*=2
 return a
n=0
for w in range(1,5):
 z=1<<w;g=[min(bin(x).count('1'),w-bin(x).count('1')) for x in range(z)];gh=fwht(g)
 for h in range(1,4):
  for rows in itertools.product(range(z),repeat=h):
   f=[0]*z
   for x in rows:f[x]+=1
   fh=fwht(f);v=fwht([a*b for a,b in zip(fh,gh)]);assert all(x%z==0 for x in v)
   got=[x//z for x in v]
   expected=[min(sum(bin(rows[i]^x^(z-1 if mask>>i&1 else 0)).count('1') for i in range(h)) for mask in range(1<<h)) for x in range(z)]
   assert got==expected,(w,rows,got,expected);n+=1
counts['abc396_g_fwht_vs_all_row_column_flips']=n
n=0
for _ in range(500):
 size=rng.randrange(1,10);capacity=rng.randrange(1,15)
 foods=[(rng.randrange(3),rng.randrange(1,10),rng.randrange(1,10)) for i in range(size)]
 dp=[[0]*(capacity+1) for j in range(3)]
 for v,a,c in foods:
  for x in range(capacity,c-1,-1):dp[v][x]=max(dp[v][x],dp[v][x-c]+a)
 for v in range(3):
  for x in range(1,capacity+1):dp[v][x]=max(dp[v][x],dp[v][x-1])
 allocation=[0,0,0]
 for x in range(capacity):
  v=min(range(3),key=lambda i:dp[i][allocation[i]]);allocation[v]+=1
 greedy=min(dp[i][allocation[i]] for i in range(3))
 brute=0
 for mask in range(1<<size):
  vals=[0,0,0];cal=0
  for i,(v,a,c) in enumerate(foods):
   if mask>>i&1:vals[v]+=a;cal+=c
  if cal<=capacity:brute=max(brute,min(vals))
 assert greedy==brute,(foods,capacity,greedy,brute);n+=1
counts['abc390_e_greedy_allocation_vs_all_food_subsets']=n
# For a fixed selected vertex set, a cycle costs add/remove weight per edge.
def bitcycle(n,edges):
 inf=10**9;full=(1<<n)-1;cycle=[inf]*(1<<n)
 for start in range(n):
  dp={1<<start:{start:0}}
  for mask in range(1<<start,1<<n):
   if mask not in dp:continue
   for last,val in list(dp[mask].items()):
    if bin(mask).count('1')>=3:cycle[mask]=min(cycle[mask],val+( -1 if tuple(sorted((last,start))) in edges else 1))
    for nxt in range(start+1,n):
     if mask>>nxt&1:continue
     nm=mask|1<<nxt;cost=val+(-1 if tuple(sorted((last,nxt))) in edges else 1)
     dp.setdefault(nm,{})[nxt]=min(dp.get(nm,{}).get(nxt,inf),cost)
 best=[inf]*(1<<n);best[0]=0
 for mask in range(1,1<<n):
  sub=mask;first=mask&-mask
  while sub:
   if sub&first and cycle[sub]<inf:best[mask]=min(best[mask],cycle[sub]+best[mask^sub])
   sub=(sub-1)&mask
 return len(edges)+best[full]
def permcycle(n,edges):
 best=10**9
 for p in itertools.permutations(range(n)):
  cuts=[None,*range(3,n-2)]
  for cut in cuts:
   groups=[p] if cut is None else [p[:cut],p[cut:]];e=set()
   for a in groups:
    for i in range(len(a)):e.add(tuple(sorted((a[i],a[(i+1)%len(a)]))))
   best=min(best,len(e^edges))
 return best
n=0
for size in range(3,8):
 possible=list(itertools.combinations(range(size),2))
 graphs=range(1<<len(possible)) if size<=5 else [rng.randrange(1<<len(possible)) for _ in range(20)]
 for mask in graphs:
  edges={e for i,e in enumerate(possible) if mask>>i&1}
  a=bitcycle(size,edges);b=permcycle(size,edges);assert a==b,(size,edges,a,b);n+=1
counts['abc412_d_subset_cycle_dp_vs_final_graph_permutations']=n
Path(__file__).with_name('root_alternative_witnesses.json').write_text(json.dumps(dict(checks_passed=True,seed=20261124,comparisons=counts,limits='Exhaustive small instances and seeded cases validate these constructions; they do not measure overall tag precision.'),indent=2)+'\n',encoding='utf-8')
print(json.dumps(counts))
