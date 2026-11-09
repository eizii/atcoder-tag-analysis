from pathlib import Path
p=Path(__file__).parent/"evidence_scope.py"
s=p.read_text(encoding="utf-8")
s=s.replace('    audit=[]\n','    audit=[]\n    codes=e.get("codes",[])\n',1)
s=s.replace('        return text,[],audit\n    return text,e.get("codes",[]),audit','''        codes=[]
    worked=re.compile(r"例題\\s*[:：].*?(?=さて、.{0,30}元の問題.{0,10}適用|元の問題に戻|本題に戻)",re.S)
    def remove_example(m):
        audit.append(dict(reason="worked_example_not_target_problem",url=e.get("url",""),context=m.group()[:220],excluded_chars=len(m.group())))
        return " "
    text=worked.sub(remove_example,text)
    refs=re.search(r"(?:参考文献|参考資料|関連記事|関連問題|References|Related problems)(?=\\s|[:：])",text,re.I)
    if refs:
        audit.append(dict(reason="references_or_related_problem_section",url=e.get("url",""),context=text[refs.start():refs.start()+220],excluded_chars=len(text)-refs.start()))
        text=text[:refs.start()]
    return text,codes,audit''')
s=s.replace('    if NEGATIVE.search(context):','''    if re.search(r"次の(?:記事|文献|資料).{0,20}参照.{0,15}[:：]",context):
        return "reference_link_title_only"
    if tid=="T135" and re.search(r"個あり|計算量",context) and re.search(r"mathrm|O\\s*\\(",context):
        return "prime_number_theorem_complexity_bound"
    if NEGATIVE.search(context):''',1)
p.write_text(s,encoding="utf-8")
# These are regression tests based on directly inspected sources, not a precision estimate.
p=Path(__file__).parent/"test_evidence_scope.py"
s=p.read_text(encoding="utf-8")
a=s.index('if __name__=="__main__"')
s=s[:a]+'''
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
        e={"url":"a.pdf","source":"official_pdf_title_anchored","text":"数列ゲーム\\n説明。"*8}
        shared=shared_body_keys({"a":{"editorials":[e]},"c":{"editorials":[e]}})
        self.assertFalse(source_scope(e,shared,"ゲーム")[0])
        self.assertTrue(source_scope(e,shared,"数列ゲーム")[0])

'''+s[a:]
p.write_text(s,encoding="utf-8")
p=Path(__file__).parent/"compare_difficulty.py"
s=p.read_text(encoding="utf-8")
s=s.replace('    assert all("T111" not in r["tag_ids"] for r in corrected.values())','''    for pid,tid in [("abc222_h","T091"),("abc370_g","T135"),("abc476_g","T105")]:
        assert tid in old[pid]["tag_ids"] and tid not in corrected[pid]["tag_ids"]
    assert "T101" in corrected["abc476_g"]["tag_ids"]
    assert all("T111" not in r["tag_ids"] for r in corrected.values())''')
s=s.replace('confirmed_ackermann_removals=8,confirmed_montgomery_removals=5,','confirmed_ackermann_removals=8,confirmed_montgomery_removals=5,confirmed_additional_background_removals=3,')
s=s.replace('    "加えて、次の出典・根拠を保守的に扱うようにした。",','''    "ABC222 Hの説明用のカタラン数の例題、ABC370 Gの計算量評価での素数定理、ABC476 Gの参考記事名のSpernerの定理という3対応も、原文を点検して除外した。ABC476 Gで上界の証明に実際に使っているLYM不等式は残した。",
    "",
    "加えて、次の出典・根拠を保守的に扱うようにした。",''')
s=s.replace('    "- 不可能・時間不足を述べる節を負例として扱う。','    "- 例題から元の問題に戻る区切りや参考文献・関連問題の節を除外する。",\\n    "- 不可能・時間不足を述べる節を負例として扱う。')
p.write_text(s,encoding="utf-8")
