"""Tests for semantic probability/expectation recall and small exact witnesses."""
import csv,itertools,json,math,unittest
from collections import defaultdict
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path
from tag_precision import ROOT,read_jsonl,read_reviews
from tag_all import normalize

class ProbabilityAuditTests(unittest.TestCase):
 comparisons=0
 @classmethod
 def setUpClass(cls):
  cls.docs={d['problem_id']:d for d in read_jsonl(ROOT/'corpus_sources.jsonl')}
  cls.reviews=read_reviews(cls.docs,ROOT/'probability_reviews.tsv')
 def same(self,a,b):self.assertEqual(a,b);type(self).comparisons+=1
 def test_missing_named_keyword_does_not_block_semantic_labels(self):
  for pid in ['abc275_e','abc298_e','abc300_e','abc310_f','abc323_e','abc342_f']:
   self.assertIn('T029',self.reviews[pid][0]['accepted'])
   self.assertNotIn('確率DP',normalize(self.docs[pid]['editorials'][0]['text']))
 def test_both_probability_and_expectation_have_separate_states(self):
  self.assertEqual(self.reviews['abc382_e'][0]['accepted'],{'T029':'supporting','T026':'primary'})
  self.assertEqual(self.reviews['abc280_e'][0]['accepted'],{'T029':'primary','T026':'alternative'})
 def test_review_quotes_and_reference_method_notes_are_grounded(self):
  self.assertEqual(len(self.reviews),35)
  with (ROOT/'probability_reference_methods.tsv').open(encoding='utf-8-sig') as f:
   for row in csv.DictReader(f,delimiter='\t'):
    self.assertTrue(any(normalize(row['evidence_quote']) in normalize(e['text']) for e in self.docs[row['problem_id']]['editorials']),row['problem_id'])
 def test_simple_probability_words_do_not_create_dp_tags(self):
  self.assertNotIn('abc003_1',self.reviews)
  self.assertNotIn('abc193_d',self.reviews)
  self.assertNotIn('abc231_g',self.reviews)
  self.assertNotIn('abc319_c',self.reviews)
 def test_sugoroku4_dp_against_all_face_sequences(self):
  for n in range(1,6):
   for m in range(1,n+1):
    for k in range(1,5):
     dp=[F(0)]*(n+1);dp[0]=F(1)
     for _ in range(k):
      nxt=[F(0)]*(n+1);nxt[n]=dp[n]
      for x in range(n):
       for face in range(1,m+1):
        y=x+face;y=y if y<=n else 2*n-y
        nxt[y]+=dp[x]/m
      dp=nxt
     wins=0
     for faces in itertools.product(range(1,m+1),repeat=k):
      x=0
      for face in faces:
       if x==n:break
       x=x+face if x+face<=n else 2*n-x-face
      wins+=x==n
     self.same(dp[n],F(wins,m**k))
 def test_playlist_time_dp_against_sequence_tree(self):
  for times in [(1,2),(2,3),(1,3,4),(2,2,3)]:
   n=len(times)
   for x in range(7):
    p=[F(0)]*(x+1);p[0]=F(1)
    for t in range(1,x+1):p[t]=sum((p[t-d] for d in times if t>=d),F(0))/n
    got=sum((p[t]/n for t in range(max(0,x-times[0]+1),x+1)),F(0))
    def visit(t):
     result=F(0)
     for i,d in enumerate(times):
      if t+d>x:result+=F(i==0,n)
      else:result+=visit(t+d)/n
     return result
    self.same(got,visit(0))
 def test_scaled_lottery_dp_against_ordered_draws(self):
  probs=[F(1,6),F(2,6),F(3,6)]
  for k in range(1,5):
   dp={(0,0):F(1)}
   for p in probs:
    nxt=defaultdict(F)
    for (distinct,draws),value in dp.items():
     for c in range(k-draws+1):nxt[distinct+(c>0),draws+c]+=value*p**c/math.factorial(c)
    dp=nxt
   for m in range(1,4):
    brute=F(0)
    for seq in itertools.product(range(3),repeat=k):
     if len(set(seq))==m:brute+=math.prod(probs[i] for i in seq)
    self.same(dp.get((m,k),F(0))*math.factorial(k),brute)
 def test_binomial_probability_precomputation_against_random_walks(self):
  for n in range(1,6):
   p=[F(1)]
   for _ in range(n):
    q=[F(0)]*(len(p)+1)
    for i,v in enumerate(p):q[i]+=v/2;q[i+1]+=v/2
    p=q
   counts=defaultdict(int)
   for seq in itertools.product([(1,0),(-1,0),(0,1),(0,-1)],repeat=n):counts[sum(x for x,y in seq),sum(y for x,y in seq)]+=1
   for (x,y),count in counts.items():
    u=(n+x+y)//2;v=(n+x-y)//2
    got=p[u]*p[v] if 0<=u<=n and 0<=v<=n else 0
    self.same(got,F(count,4**n))

if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProbabilityAuditTests))
 out=ROOT/'output_v3_1';out.mkdir(exist_ok=True)
 (out/'probability_test_results.json').write_text(json.dumps(dict(checks_passed=result.wasSuccessful(),tests=result.testsRun,exact_comparisons=ProbabilityAuditTests.comparisons),indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if result.wasSuccessful() else 1)

