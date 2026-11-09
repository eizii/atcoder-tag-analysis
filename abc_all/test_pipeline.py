import unittest
from collect_statements import ROOT,load_json,parse_print
from collect_editorials import links_for_tasks,parse_editorial
from tag_all import alias_regex,named_evidence

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.data=load_json(ROOT/"manifest.json")
    def test_legacy_nested_ids_are_not_duplicate_tasks(self):
        expected=[p for p in self.data["problems"] if p["contest_id"]=="abc007"]
        got=parse_print((ROOT/"cache/abc007_tasks.html").read_bytes(),expected)
        self.assertEqual(len(got),4)
        self.assertIn("入力",got["abc007_3"]["statement"])
    def test_current_statement_preserves_constraints_and_samples(self):
        expected=[p for p in self.data["problems"] if p["contest_id"]=="abc482"]
        got=parse_print((ROOT/"cache/abc482_tasks.html").read_bytes(),expected)
        self.assertEqual(len(got),7)
        self.assertIn("制約",got["abc482_a"]["statement"])
        self.assertIn("入力例",got["abc482_a"]["statement"])
    def test_old_editorial_redirect_is_resolved(self):
        _,pdfs=links_for_tasks((ROOT/"cache/abc042_editorial.html").read_bytes())
        self.assertIn("https://img.atcoder.jp/arc058/editorial.pdf",pdfs)
    def test_web_editorial_selects_body_and_removes_generic_intro(self):
        got=parse_editorial((ROOT/"cache/editorial_11554.html").read_bytes(),"source",False)
        self.assertIn("差",got["text"])
        self.assertNotIn("Welcome to AtCoder",got["text"])
        self.assertTrue(got["codes"])
    def test_specific_bfs_is_not_counted_as_generic_name(self):
        rules={"T066":[("BFS",alias_regex("BFS"))],"T144":[("0-1 BFS",alias_regex("0-1 BFS"))]}
        found,_=named_evidence("0-1 BFSで解く。",rules)
        self.assertEqual({x["tag_id"] for x in found},{"T144"})
    def test_reference_and_infeasible_methods_are_not_positive_evidence(self):
        rules={"T065":[("全探索",alias_regex("全探索"))],"T064":[("二分探索",alias_regex("二分探索"))]}
        found,rejected=named_evidence("全探索では間に合いません。二分探索で解きます。参考文献:全探索",rules)
        self.assertEqual({x["tag_id"] for x in found},{"T064"})
        self.assertTrue(rejected)
    def test_ascii_names_do_not_match_other_words(self):
        found,_=named_evidence("minimum primary",{"T037":[("Nim",alias_regex("Nim"))],"T234":[("Prim",alias_regex("Prim"))]})
        self.assertEqual(found,[])

if __name__=="__main__": unittest.main(verbosity=2)
