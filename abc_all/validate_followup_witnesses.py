"""Independent finite experiments for the follow-up's nonliteral DP classifications."""
import itertools,json,math,random
from collections import Counter
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path
R=Path(__file__).resolve().parent
checks=Counter()
def equal(a,b,kind):
 assert a==b,(kind,a,b)
 checks[kind]+=1

def add(a,b):
 c=[F(0)]*max(len(a),len(b))
 for i,x in enumerate(a):c[i]+=x
 for i,x in enumerate(b):c[i]+=x
 return c

def mul(a,b):
 c=[F(0)]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):c[i+j]+=x*y
 return c

def series_div(a,b,n):
 q=[]
 for i in range(n):q.append(((a[i] if i<len(a) else 0)-sum(b[j]*q[i-j] for j in range(1,min(i,len(b)-1)+1)))/b[0])
 return q

def pancake_merge(pairs):
 q=[F(1,2),F(1,2)];leaves=[]
 for v,idx,high in sorted((v,i,h) for i,ab in enumerate(pairs) for h,v in enumerate(ab)):
  leaves.append(([F(0),F(1)] if high else mul(q,q),q,[F(v,2)] if high else [v*x/2 for x in q]))
 def dc(ls):
  if len(ls)==1:return ls[0]
  m=len(ls)//2;l=dc(ls[:m]);r=dc(ls[m:])
  return mul(l[0],r[0]),mul(l[1],r[1]),add(mul(l[2],r[1]),mul(l[0],r[2]))
 merged=dc(leaves);den=[F(1)]
 for _ in leaves:den=mul(den,q)
 return series_div(merged[2],den,len(pairs))

def pancake_enum(pairs):
 ans=[F(0)]*len(pairs)
 for picks in itertools.product((0,1),repeat=len(pairs)):
  a=sorted(ab[c] for ab,c in zip(pairs,picks))
  for k,v in enumerate(a):ans[k]+=F(v,2**len(pairs))
 return ans

# Every orientation/hidden-permutation history is enumerated independently.
for n in range(1,8):
 hist=Counter()
 for perm in itertools.permutations(range(n)):
  known={};unknown=set(range(n));operations=0
  for target in range(n):
   while True:
    if target in known:
     del known[target];operations+=1;break
    card=min(unknown);unknown.remove(card);value=perm[card];operations+=1
    if value==target:break
    known[value]=card
  hist[operations-n]+=1
 prob=[F(1)]
 for k in range(1,n+1):prob=mul(prob,[F(1,k),F(k-1,k)])
 equal(prob,[F(hist[j],math.factorial(n)) for j in range(n+1)],'wipeout_hidden_permutations')
 checks['wipeout_enumerated_histories']+=math.factorial(n)

for n in range(1,8):
 for faces in [(1,),(1,2),(1,2,3),(1,1,3),(2,4)]:
  hist=[F(0)]*(n+1)
  def visit(pos,t,prob):
   if pos>=n:hist[t]+=prob;return
   for step in faces:visit(pos+step,t+1,prob/len(faces))
  visit(0,0,F(1))
  die=[F(0)]*(max(faces)+1)
  for x in faces:die[x]+=F(1,len(faces))
  power=[F(1)];survival=[]
  for t in range(n+1):
   survival.append(sum(power[:n]));power=mul(power,die)
  equal(hist[1:],[survival[t-1]-survival[t] for t in range(1,n+1)],'sugoroku_projected_survival')

choices=list(itertools.combinations(range(1,5),2))
for n in range(1,4):
 for pairs in itertools.product(choices,repeat=n):equal(pancake_merge(pairs),pancake_enum(pairs),'half_baked_merge_vs_outcomes')
rng=random.Random(20261123)
for _ in range(30):
 pairs=[tuple(sorted(rng.sample(range(1,30),2))) for i in range(6)]
 equal(pancake_merge(pairs),pancake_enum(pairs),'half_baked_merge_vs_outcomes')
equal(pancake_merge([(1,2)]),[F(3,2)],'half_baked_single_pair_normalization')

# All decimal strings length <= 5 over an alphabet with zero and nonzero digits.
for n in range(1,6):
 for digits in itertools.product((0,1,9),repeat=n):
  s=F(0);x=F(digits[0])
  for d in digits[1:]:s,x=s+x/2,5*x+d
  total=0
  for cuts in itertools.product((False,True),repeat=n-1):
   parts=[];cur=digits[0]
   for d,cut in zip(digits[1:],cuts):
    if cut:parts.append(cur);cur=d
    else:cur=10*cur+d
   total+=sum(parts)+cur
  equal((s+x)*2**(n-1),total,'separate_digits_expectation_vs_cuts')

# Circular removal: exact stochastic process vs interval first-moment recurrence.
def removal_enum(s):
 n=len(s)
 @lru_cache(None)
 def e(alive):
  if len(alive)==1:return F(0)
  ans=F(0)
  for idx,u in enumerate(alive):
   v=alive[(idx+(1 if s[u]=='R' else -1))%len(alive)]
   dist=(v-u)%n if s[u]=='R' else (u-v)%n
   ans+=F(dist,len(alive))+e(tuple(x for x in alive if x!=v))/len(alive)
  return ans
 return e(tuple(range(n)))

def removal_interval(s):
 n=len(s);ss=s+s;num={};cost={}
 for l in range(2*n-1):num[l,l+1]=1;cost[l,l+1]=0
 for w in range(2,n+1):
  for l in range(2*n-w):
   r=l+w;num[l,r]=cost[l,r]=0
   for i in range(l+1,r):
    c1=int(ss[l]=='R')+int(ss[r]=='L');c2=(i-l)*(ss[l]=='R')+(r-i)*(ss[r]=='L');b=math.comb(w-2,i-l-1)
    num[l,r]+=num[l,i]*num[i,r]*c1*b
    cost[l,r]+=(num[l,i]*num[i,r]*c2+cost[l,i]*num[i,r]*c1+num[l,i]*cost[i,r]*c1)*b
 return F(sum(cost[l,l+n] for l in range(n)),math.factorial(n))
for n in range(2,8):
 for dirs in itertools.product('LR',repeat=n):
  s=''.join(dirs);equal(removal_interval(s),removal_enum(s),'removing_people_first_moment_vs_process')

# Dye Color: full Markov equations for N<=3 vs transformed one-dimensional recurrence.
def solve_linear(a,b):
 n=len(b);a=[list(map(F,row))+[F(v)] for row,v in zip(a,b)]
 for i in range(n):
  pivot=next(k for k in range(i,n) if a[k][i]);a[i],a[pivot]=a[pivot],a[i]
  v=a[i][i];a[i]=[x/v for x in a[i]]
  for j in range(n):
   if j!=i:
    v=a[j][i];a[j]=[x-v*y for x,y in zip(a[j],a[i])]
 return [row[-1] for row in a]

def dye_transition(state):
 n=len(state);p=Counter()
 for mask in range(1<<n):
  selected=[i for i in range(n) if mask>>i&1];k=len(selected);weight=F(1,(1<<n)*math.perm(n,k))
  for colors in itertools.permutations(range(n),k):
   t=list(state)
   for i,c in zip(selected,colors):t[i]=c
   p[tuple(t)]+=weight
 return p
for n in (2,3):
 states=[s for s in itertools.product(range(n),repeat=n) if len(set(s))>1];ix={s:i for i,s in enumerate(states)}
 a=[[F(i==j) for j in range(len(states))] for i in range(len(states))]
 for s,i in ix.items():
  for t,p in dye_transition(s).items():
   if t in ix:a[i][ix[t]]-=p
 full=solve_linear(a,[1]*len(states));g=[F(0)]
 for i in range(n):
  # i balls have target color zero; all other balls have color one.
  p=[F(0)]*(n+1)
  for t,w in dye_transition(tuple([0]*i+[1]*(n-i))).items():p[t.count(0)]+=w
  equal(sum(p[i+2:]),F(0),'dye_hessenberg_structure')
  g.append((g[i]-F(1,n)-sum(p[j]*g[j] for j in range(i+1)))/p[i+1])
 for s,i in ix.items():equal(sum(g[s.count(c)] for c in range(n))-g[n],full[i],'dye_potential_vs_full_markov')

# ABC301 F: 29-state probability automaton vs explicit substitutions.
def anti_ddos_dp(s,upper='ABC',lower='ab'):
 u=len(upper);a=[F(0)]*(u+3);a[0]=F(1);seen=set();repeat=u+1;after=u+2
 for c in s:
  b=[F(0)]*len(a)
  # Unknown symbols of each case have total probability 1/2 in the
  # original 26+26 alphabet; the reduced alphabet below is weighted by size.
  small=F(len(lower),u+len(lower)) if c=='?' else F(c in lower)
  big=1-small
  b[0]+=a[0]*small;b[1]+=a[0]*big
  for y in range(1,u+1):
   b[y]+=a[y]*small
   r=F(y,u) if c=='?' else F(1) if c in seen else F(y-len(seen),u-len(seen)) if len(seen)<u else F(0)
   b[repeat]+=a[y]*big*r
   if y<u:b[y+1]+=a[y]*big*(1-r)
  b[repeat]+=a[repeat]*big;b[after]+=a[repeat]*small+a[after]*small
  a=b
  if c in upper:seen.add(c)
 return sum(a)
def anti_ddos_enum(s,upper='ABC',lower='ab'):
 alphabet=upper+lower;good=0;q=s.count('?')
 for repl in itertools.product(alphabet,repeat=q):
  it=iter(repl);t=''.join(next(it) if c=='?' else c for c in s)
  bad=any(t[i] in upper and t[i]==t[j] and t[k] in lower and t[l] in upper for i,j,k,l in itertools.combinations(range(len(t)),4))
  good+=not bad
 return F(good,len(alphabet)**q)
for n in (4,5,6):
 for _ in range(40):
  s=''.join(rng.choice('ABCab?') for i in range(n))
  equal(anti_ddos_dp(s),anti_ddos_enum(s),'anti_ddos_probability_states_vs_substitutions')
for s in ('????','A??aA','AB?Ba?','A?B?Aa','AAaA','ABabBA','??????'):
 equal(anti_ddos_dp(s),anti_ddos_enum(s),'anti_ddos_probability_states_vs_substitutions')

for s in ('A?DaS','D?oS','?Da?','A?A?AA','DDaS'):
 equal(anti_ddos_dp(s,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),anti_ddos_enum(s,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'anti_ddos_full_alphabet')

out=R/'output_v3_2';out.mkdir(exist_ok=True)
report=dict(checks_passed=True,comparisons=dict(checks),method='Exact rational arithmetic; independent hidden outcomes, recursive random processes, and full absorbing Markov equations.',limitations='Small instances validate state semantics and algebra, not production FFT implementations, asymptotic feasibility, dataset-wide precision, or recall.',source_issue={'problem_id':'abc481_g','detail':'\u5b9a\u5f0f\u53162\u306e\u672c\u6587M\u306b\u306f\u9078\u629e\u78ba\u73871/2\u304c\u898b\u5f53\u305f\u3089\u306a\u3044\u3002\u4fdd\u5b58\u6e08\u307f\u5b9f\u88c5\u306ecm\u306f1/2\u3092\u542b\u307f\u3001N=1\u306e\u5217\u6319\u3068\u4e00\u81f4\u3002\u30ec\u30d3\u30e5\u30fc\u306f\u672c\u6587\u306e\u4fc2\u6570\u3092\u305d\u306e\u307e\u307e\u8ee2\u8a18\u305b\u305a\u3001\u3053\u306e\u6b63\u898f\u5316\u3092\u4f7f\u7528\u3002','minimum_witness':'A=1,B=2: E=3/2; omitted factor produces 3.'})
(out/'followup_solution_witness_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
