"""Check selected review-derived algorithms against independently enumerated answers.

These witnesses validate solution reasoning on small cases, not dataset accuracy.
"""
import itertools,math,random,re,unittest
from fractions import Fraction
from functools import reduce
from pathlib import Path
from collect_statements import save_json

class WitnessTests(unittest.TestCase):
 cases=0
 def same(self,a,b):self.assertEqual(a,b);type(self).cases+=1
 def test_tree_coloring_dp_against_all_colorings(self):
  rng=random.Random(2311)
  for n in range(2,9):
   for _ in range(8):
    edges=[(i,rng.randrange(i)) for i in range(1,n)]
    g=[[] for _ in range(n)]
    for a,b in edges:g[a].append(b);g[b].append(a)
    def dp(v,p):
     white=black=1
     for u in g[v]:
      if u!=p:
       w,b=dp(u,v);white*=w+b;black*=w
     return white,black
    expected=sum(all(not(mask>>a&1 and mask>>b&1) for a,b in edges) for mask in range(1<<n))
    self.same(sum(dp(0,-1)),expected)
 def test_topological_subset_dp_against_permutations(self):
  rng=random.Random(412)
  for n in range(2,7):
   for _ in range(6):
    edges=[(i,j) for i in range(n) for j in range(i+1,n) if rng.randrange(3)==0]
    pred=[0]*n
    for a,b in edges:pred[b]|=1<<a
    dp=[0]*(1<<n);dp[0]=1
    for s in range(1<<n):
     for v in range(n):
      if not s>>v&1 and pred[v]&s==pred[v]:dp[s|1<<v]+=dp[s]
    expected=0
    for perm in itertools.permutations(range(n)):
     pos={v:i for i,v in enumerate(perm)}
     expected+=all(pos[a]<pos[b] for a,b in edges)
    self.same(dp[-1],expected)
 def test_semi_common_multiple_formula(self):
  for a in itertools.product([2,4,6,8,10,12],repeat=3):
   for limit in [1,10,31]:
    half=[x//2 for x in a]
    powers=[(x&-x) for x in half]
    lcm=reduce(lambda x,y:x*y//math.gcd(x,y),half,1)
    got=(limit//lcm+1)//2 if len(set(powers))==1 else 0
    expected=sum(all(x%v==0 and x//v%2==1 for v in half) for x in range(1,limit+1))
    self.same(got,expected)
 def test_manhattan_transform(self):
  rng=random.Random(178)
  for _ in range(120):
   pts=[(rng.randrange(-12,13),rng.randrange(-12,13)) for _ in range(rng.randrange(2,10))]
   zs=[x+y for x,y in pts];ws=[x-y for x,y in pts]
   got=max(max(zs)-min(zs),max(ws)-min(ws))
   self.same(got,max(abs(x-a)+abs(y-b) for x,y in pts for a,b in pts))
 def test_bitmask_greedy_against_all_assignments(self):
  for length in range(1,6):
   for chars in itertools.product('01?',repeat=length):
    s=''.join(chars)
    for bound in [0,1,5,17,31]:
     got=int(s.replace('?','0'),2)
     if got>bound:got=-1
     else:
      for i,c in enumerate(s):
       bit=1<<(length-1-i)
       if c=='?' and got+bit<=bound:got+=bit
     expected=max([x for x in range(1<<length) if x<=bound and all(c=='?' or int(c)==(x>>(length-1-i)&1) for i,c in enumerate(s))],default=-1)
     self.same(got,expected)
 def test_binary_boundary_without_global_monotonicity(self):
  for n in range(2,11):
   for middle in itertools.product([0,1],repeat=n-2):
    s=[0,*middle,1];left=0;right=n-1;queries=0
    while right-left>1:
     m=(left+right)//2;queries+=1
     if s[m]==0:left=m
     else:right=m
    self.same((s[left],s[left+1]),(0,1))
    self.assertLessEqual(queries,math.ceil(math.log2(n)))
 def test_stack_parentheses_against_rewrite_rule(self):
  for length in range(7):
   for chars in itertools.product('a()',repeat=length):
    s=''.join(chars);answer=[];opens=[]
    for c in s:
     if c=='(':
      opens.append(len(answer));answer.append(c)
     elif c==')' and opens:
      start=opens.pop();del answer[start:]
     else:answer.append(c)
    expected=s
    while True:
     changed=re.sub(r'\([^()]*\)','',expected)
     if changed==expected:break
     expected=changed
    self.same(''.join(answer),expected)
 def test_divisor_mobius_gcd_sum(self):
  for n in range(2,5):
   for k in range(1,8):
    counts=[0]*(k+1)
    for d in range(k,0,-1):counts[d]=(k//d)**n-sum(counts[2*d::d])
    got=sum(d*counts[d] for d in range(1,k+1))
    self.same(got,sum(reduce(math.gcd,items) for items in itertools.product(range(1,k+1),repeat=n)))
 def test_prim_is_not_valid_for_modulo_tree_objective(self):
  weights=[1,2,4];modulus=5
  raw_mst_cost=sum(sorted(weights)[:2])%modulus
  true_min=min(sum(pair)%modulus for pair in itertools.combinations(weights,2))
  self.same(raw_mst_cost,3);self.same(true_min,0)
  self.assertNotEqual(raw_mst_cost,true_min)

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(WitnessTests)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 report=dict(checks_passed=result.wasSuccessful(),test_count=result.testsRun,enumerated_comparisons=WitnessTests.cases,scope='Selected small-case solution witnesses; not an accuracy estimate or full-constraint implementation benchmark.')
 save_json(Path(__file__).resolve().parent/'output_v3/solution_witness_verification.json',report)
 raise SystemExit(0 if result.wasSuccessful() else 1)
