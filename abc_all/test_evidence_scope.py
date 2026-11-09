import json
import unittest
from collect_statements import ROOT,load_json
from evidence_scope import source_scope,shared_body_keys,executable_code
from tag_all import named_evidence,alias_regex

def rules(**names):
    return {tid:[(name,alias_regex(name))] for tid,name in names.items()}

class ScopeTests(unittest.TestCase):
    def test_complexity_ackermann_is_not_used_algorithm(self):
        found,rejected=named_evidence("ここで、αはアッカーマン関数の逆関数であり、計算量はほぼ定数です。",rules(T111="アッカーマン関数"))
        self.assertFalse(found)
        self.assertEqual(rejected[0]["reason"],"inverse_ackermann_complexity_background")

    def test_actual_ackermann_calculation_is_not_blacklisted(self):
        found,_=named_evidence("アッカーマン関数を再帰で計算します。",rules(T111="アッカーマン関数"))
        self.assertEqual(len(found),1)

    def test_infeasible_and_feasible_methods_in_same_sentence(self):
        found,rejected=named_evidence("全探索では間に合わないため二分探索を使います。",rules(T065="全探索",T064="二分探索"))
        self.assertEqual({x["tag_id"] for x in found},{"T064"})
        self.assertEqual({x["tag_id"] for x in rejected},{"T065"})

    def test_feasible_time_limit_is_not_a_negative(self):
        found,_=named_evidence("二分探索は実行時間制限に間に合います。",rules(T064="二分探索"))
        self.assertTrue(found)

    def test_real_preface_is_removed_but_solution_fft_remains(self):
        with (ROOT/"corpus_sources.jsonl").open(encoding="utf-8") as stream:
            source=next(obj for obj in map(json.loads,stream) if obj["problem_id"]=="abc265_h")
        text,codes,audit=source_scope(source["editorials"][0],{})
        found,_=named_evidence(text,rules(T087="AND 畳み込み",T103="OR 畳み込み",T108="XOR 畳み込み",T196="FFT"))
        tids={x["tag_id"] for x in found}
        self.assertIn("T108",tids)
        self.assertIn("T196",tids)
        self.assertNotIn("T087",tids)
        self.assertNotIn("T103",tids)
        self.assertTrue(audit)

    def test_unsegmented_multi_problem_source_is_quarantined(self):
        e=dict(url="source",text="A問題:二分探索。B問題:動的計画法。"*8,codes=["sort(a,a+n);"])
        shared=shared_body_keys({"a":{"editorials":[e]},"b":{"editorials":[e]}})
        text,codes,audit=source_scope(e,shared)
        self.assertEqual((text,codes),("",[]))
        self.assertEqual(audit[0]["reason"],"shared_unsegmented_editorial")

    def test_unused_library_definition_is_not_execution(self):
        code="void dijkstra(){ sort(a,a+n); }\nint main(){ int x=1; return x; }"
        self.assertNotIn("dijkstra",executable_code(code))
        self.assertNotIn("sort",executable_code(code))
        self.assertIn("dijkstra",executable_code("void dijkstra(){}\nint main(){dijkstra();}"))

    def test_python_called_helper_and_unused_definition(self):
        code="def unused():\n sorted([1])\ndef used():\n return sorted([2])\nused()\n"
        actual=executable_code(code)
        self.assertNotIn("unused",actual)
        self.assertIn("sorted([2])",actual)


    def test_reference_title_is_not_application_but_lym_proof_remains(self):
        text="LYM 不等式より上界を証明できます。次の記事を参照してください：Sperner の定理 - AtCoderInfo"
        found,rejected=named_evidence(text,rules(T101="LYM 不等式",T105="Sperner"))
        self.assertEqual({h["tag_id"] for h in found},{"T101"})
        self.assertEqual(rejected[0]["reason"],"reference_link_title_only")

    def test_prime_number_complexity_bound_is_not_algorithm(self):
        found,rejected=named_evidence("素数は素数定理より O(N/log N) 個あり、DPの計算量を評価できます。",rules(T135="素数定理"))
        self.assertFalse(found)
        self.assertEqual(rejected[0]["reason"],"prime_number_theorem_complexity_bound")

    def test_worked_example_is_removed_but_real_application_remains(self):
        e={"text":"反転公式を使います。例題：カタラン数を求めます。さて、反転公式を元の問題に適用します。"}
        text,_,audit=source_scope(e,{})
        found,_=named_evidence(text,rules(T091="カタラン数",T127="反転公式"))
        self.assertNotIn("T091",{h["tag_id"] for h in found})
        self.assertIn("T127",{h["tag_id"] for h in found})
        self.assertTrue(audit)

    def test_pdf_duplicate_is_kept_only_for_exact_title(self):
        e={"url":"a.pdf","source":"official_pdf_title_anchored","text":"数列ゲーム\n説明。"*8}
        shared=shared_body_keys({"a":{"editorials":[e]},"c":{"editorials":[e]}})
        self.assertFalse(source_scope(e,shared,"ゲーム")[0])
        self.assertTrue(source_scope(e,shared,"数列ゲーム")[0])

    def test_all_occurrences_of_confirmed_background_tags_are_filtered(self):
        config=load_json(ROOT/"tag_rules.json")
        compiled={t:[(a,alias_regex(a)) for a in aa] for t,aa in config["aliases"].items()}
        targets={"abc222_h":"T091","abc370_g":"T135","abc476_g":"T105"}
        with (ROOT/"corpus_sources.jsonl").open(encoding="utf-8") as stream:
            docs={obj["problem_id"]:obj for obj in map(json.loads,stream) if obj["problem_id"] in targets}
        for pid,tid in targets.items():
            hits=[h for e in docs[pid]["editorials"] for h in named_evidence(source_scope(e,{},docs[pid]["title"])[0],compiled)[0]]
            self.assertNotIn(tid,{h["tag_id"] for h in hits})
            if pid=="abc476_g":self.assertIn("T101",{h["tag_id"] for h in hits})

if __name__=="__main__": unittest.main(verbosity=2)
