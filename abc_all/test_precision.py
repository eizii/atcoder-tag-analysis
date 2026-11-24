"""Regression checks against observed V2 mislabels and source extraction defects."""
import json,unittest
from pathlib import Path
from precision_policy import scoped_editorial,named_evidence_v3,description_rejection
from tag_all import alias_regex
from tag_precision import clean_code,read_reviews,read_jsonl
from refresh_precision_sources import parse
R=Path(__file__).resolve().parent

def rules(**items):return {t:[(a,alias_regex(a))] for t,a in items.items()}

class PrecisionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.docs={d['problem_id']:d for d in read_jsonl(R/'corpus_sources.jsonl')}
 def test_joint_contest_stops_before_next_problem(self):
  d=self.docs['arc074_b'];text,_,audit=scoped_editorial(d['editorials'][0],{},d)
  self.assertIn('優先度付きキュー',text)
  self.assertNotIn('RGB Sequence',text)
  self.assertNotIn('最小カット',text)
  self.assertTrue(any(a['reason']=='pdf_next_problem_boundary' for a in audit))
 def test_grid_coloring_does_not_inherit_matching(self):
  d=self.docs['arc080_b'];text,_,_=scoped_editorial(d['editorials'][0],{},d)
  self.assertIn('順序付け',text)
  self.assertNotIn('Old Maid',text)
  self.assertNotIn('マッチング',text)
 def test_mistyped_pdf_letter_does_not_delete_knapsack(self):
  d=self.docs['abc015_4'];text,_,_=scoped_editorial(d['editorials'][0],{},d)
  self.assertIn('ナップサック',text)
  self.assertIn('動的計画法',text)
 def test_partial_score_modulo_is_not_full_score_method(self):
  d=self.docs['abc010_4'];text,_,_=scoped_editorial(d['editorials'][0],{},d)
  self.assertIn('最小カット',text)
  self.assertNotIn('(i >> k) % 2',text)
 def test_fifo_is_not_substring_of_heap(self):
  hits,_=named_evidence_v3('優先度付きキューを用います。キューに最大値を入れます。',rules(T010='優先度付きキュー',T011='キュー'))
  self.assertEqual({h['tag_id'] for h in hits},{'T010'})
 def test_real_queue_evidence_survives(self):
  hits,_=named_evidence_v3('FIFOキューを使って幅優先探索を実行します。',rules(T011='キュー'))
  self.assertEqual({h['tag_id'] for h in hits},{'T011'})
 def test_topological_sort_is_not_plain_sort_name(self):
  hits,_=named_evidence_v3('topological sort を行います。',rules(T049='topological sort',T077='sort'))
  self.assertEqual({h['tag_id'] for h in hits},{'T049'})
 def test_independent_sort_survives(self):
  hits,_=named_evidence_v3('topological sort を行います。出力を sort します。',rules(T049='topological sort',T077='sort'))
  self.assertEqual({h['tag_id'] for h in hits},{'T049','T077'})
 def test_bst_name_is_not_binary_search(self):
  hits,_=named_evidence_v3('平衡二分探索木を使います。',rules(T014='平衡二分探索木',T064='二分探索'))
  self.assertEqual({h['tag_id'] for h in hits},{'T014'})
 def test_minimax_theorem_and_search_are_distinct(self):
  hits,_=named_evidence_v3('ミニマックス定理を証明します。',rules(T038='ミニマックス'))
  self.assertFalse(hits)
  hits,_=named_evidence_v3('ゲーム木でミニマックス法を使います。',rules(T038='ミニマックス'))
  self.assertTrue(hits)
 def test_prim_analogy_is_not_prim(self):
  hits,_=named_evidence_v3('Prim のような感じで全コストを保持するDPを考えます。',rules(T234='Prim'))
  self.assertFalse(hits)
 def test_counting_arrangements_is_not_sort_execution(self):
  self.assertEqual(description_rejection('T077','仕切りの並び替え方の総数を求めます。','並び替え'),'counting_permutations_not_sorting')
  self.assertIsNone(description_rejection('T077','数列を昇順に並び替えます。','並び替え'))
 def test_persistent_tree_analogy_is_not_prefix_sums(self):
  hits,_=named_evidence_v3('累積和の要領で木の複製と直線の追加を繰り返します。',rules(T086='累積和'))
  self.assertFalse(hits)
 def test_dp_derivation_is_not_simulation(self):
  self.assertEqual(description_rejection('T076','問題文の通りに DP の式を立てます。','問題文の通り'),'deriving_dp_from_statement_not_simulation')
 def test_cpp_comments_and_strings_are_not_execution(self):
  code='int main(){ // sort(a);\n string s="dijkstra()"; return 0; }'
  actual=clean_code(code)
  self.assertNotIn('sort',actual);self.assertNotIn('dijkstra',actual)
 def test_called_python_helper_survives_but_unused_does_not(self):
  code='def unused():\n sorted([0])\ndef used():\n return sorted([2])\nused()\n'
  actual=clean_code(code);self.assertIn('sorted([2])',actual);self.assertNotIn('sorted([0])',actual)
 def test_all_review_quotes_and_ids_are_valid(self):
  reviews=read_reviews(self.docs)
  taxonomy={r['tag_id'] for r in json.loads((R/'taxonomy.json').read_text(encoding='utf-8'))}
  for pid,rs in reviews.items():
   for review in rs:
    self.assertTrue(set(review['accepted'])<=taxonomy)
    self.assertTrue(set(review['rejected'])<=taxonomy)
    self.assertFalse(set(review['accepted'])&set(review['rejected']))
    self.assertIn(review['scope'],{'full','selected_tags'})
    self.assertTrue(review['reason'])
 def test_html_details_are_all_extracted(self):
  raw='<div id="main-container"><div><span class="label">公式</span><h2 class="mt-1"><a href="/contests/x/tasks/x_a">A</a></h2><div><details><summary>前提</summary><div>前提知識</div></details><details><summary>解法</summary><div>幅優先探索で解く。<pre>queue&lt;int&gt; q;</pre></div></details></div></div></div>'
  e=parse(raw.encode(),'https://atcoder.jp/contests/x/editorial/1')
  self.assertIn('幅優先探索',e['text']);self.assertTrue(e['codes']);self.assertEqual(e['task_ids'],['x_a'])
 def test_real_truncated_editorial_is_recovered(self):
  path=R/'precision_cache/editorial_2229.html'
  if not path.exists():self.skipTest('Optional downloaded HTML not present')
  e=parse(path.read_bytes(),'https://atcoder.jp/contests/abc209/editorial/2229')
  self.assertIn('各街の色を求めるには幅優先探索',e['text'])
  self.assertEqual(e['task_ids'],['abc209_d']);self.assertTrue(e['codes'])

if __name__=='__main__':unittest.main(verbosity=2)
