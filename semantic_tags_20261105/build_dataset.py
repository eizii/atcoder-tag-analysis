"""Build a semantic learning-unit taxonomy for the CURRENT 898-task application."""
import csv,hashlib,io,json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parent
APP=Path("C:/Users/ejham/theme2026-kaziru")
OUT=ROOT/"output"
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def save(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def read(p):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def write(p,fields,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    policy=load(ROOT/"policy.json")
    min_count=int(policy.get("display_min_problem_count",1))
    fine=read(WORKSPACE/"validation/revised/all_problems_tagged.csv")
    taxonomy={r["tag_id"]:r["tag"] for r in load(WORKSPACE/"abc_all/taxonomy.json")}
    # Use the saved current application catalog after the first build.
    before=ROOT/"before"
    before.mkdir(exist_ok=True)
    for name,source in [("all_problems.csv",APP/"public/all_problems.csv"),("tagCatalog.json",APP/"src/data/tagCatalog.json")]:
        if not (before/name).exists():(before/name).write_bytes(source.read_bytes())
    old=load(before/"tagCatalog.json");app_rows=read(before/"all_problems.csv")
    meta={}
    for r in app_rows:
        fields={k:r[k] for k in ["problem_id","title","difficulty","diff_band","url"]}
        if r["problem_id"] in meta:assert meta[r["problem_id"]]==fields
        meta[r["problem_id"]]=fields
    assert len(meta)==898 and len(fine)==1740
    assert {r["problem_id"] for r in fine}==set(meta)
    old_members={t["tag_id"]:g for g in old["clusters"] for t in g["member_tags"]}
    expected_old={(r["problem_id"],old_members[r["tag_id"]]["label"]) for r in fine}
    assert expected_old=={(r["problem_id"],r["tag"]) for r in app_rows}
    groups={g["id"]:g for g in policy["groups"]}
    direct={tid:g["id"] for g in groups.values() for tid in g["source_tag_ids"]}
    facets={f["tag_id"]:f for f in policy["facets"]}
    active={r["tag_id"] for r in fine}
    mapped=[t for g in groups.values() for t in g["source_tag_ids"]]+list(facets)
    assert set(mapped)==active and len(mapped)==len(set(mapped))==115
    assert len({g["label"] for g in groups.values()})==len(groups)
    bypid=defaultdict(list)
    for r in fine:bypid[r["problem_id"]].append(r)
    overrides=defaultdict(list)
    for r in policy["overrides"]:overrides[r["problem_id"]].append(r)
    assignments=[];audit=[];details={};topics={};supports=defaultdict(set)
    for pid in sorted(meta):
        accepted=defaultdict(list);record_facets=[];excluded=[]
        for r in bypid[pid]:
            tid=r["tag_id"];role=r["validated_role"]
            if tid in facets:
                record_facets.append(dict(facets[tid],source_role=role,source_note=r["note"],
                    context_type="analysis_background" if role=="analysis_concept" else facets[tid]["type"]))
                audit.append(dict(problem_id=pid,source_tag_id=tid,source_tag=taxonomy[tid],
                    unit_id="",action="retain_as_metadata",reason=facets[tid]["reason"],source_role=role))
            elif role in policy["excluded_roles"]:
                excluded.append(dict(tag_id=tid,tag=taxonomy[tid],role=role,reason="Existing review marks this evidence as reference, unsupported, analysis-only or ambiguous."))
                audit.append(dict(problem_id=pid,source_tag_id=tid,source_tag=taxonomy[tid],
                    unit_id=direct[tid],action="withhold_prior_flagged_evidence",reason="既存レビューで参考・根拠不足・分析用・要再確認とされた対応を表示根拠にしない。",source_role=role))
            else:
                accepted[direct[tid]].append(dict(tag_id=tid,tag=taxonomy[tid],role=role,
                    evidence_urls=r.get("validation_evidence_urls","") or r.get("editorial_url",""),
                    note=r["note"],provisional=role=="unreviewed"))
        for r in overrides.get(pid,[]):
            assert r["basis_tag_id"] in {x["tag_id"] for x in bypid[pid]}
            accepted[r["unit_id"]].append(dict(method="assistant_source_review",role=r["role"],
                basis_tag_id=r["basis_tag_id"],evidence_url=r["evidence_url"],note=r["reason"],
                independent_human_review=False))
            audit.append(dict(problem_id=pid,source_tag_id=r["basis_tag_id"],source_tag=taxonomy[r["basis_tag_id"]],
                unit_id=r["unit_id"],action="source_review_refinement",reason=r["reason"],source_role=r["role"]))
        suppressed={}
        for rule in policy["suppression_rules"]:
            if rule["base"] in accepted and set(rule["when_any"])&set(accepted):
                suppressed[rule["base"]]=accepted.pop(rule["base"])
                for e in suppressed[rule["base"]]:
                    audit.append(dict(problem_id=pid,source_tag_id=e["tag_id"],source_tag=e["tag"],
                        unit_id=rule["base"],action="suppress_broader_display_unit",reason=rule["reason"],source_role=e["role"]))
        for uid,es in accepted.items():
            supports[uid].add(pid)
            assignments.append(dict(tag=groups[uid]["label"],**meta[pid],unit_id=uid,
                source_tag_ids=" | ".join(sorted({e["tag_id"] for e in es if "tag_id" in e})),
                role=" | ".join(sorted({e["role"] for e in es})),
                assignment_status="provisional" if any(e.get("provisional") for e in es) else "prior_or_assistant_reviewed",
                taxonomy_version=policy["version"]))
        details[pid]=dict(original_fine_tags=[dict(tag_id=r["tag_id"],tag=r["tag"],role=r["validated_role"]) for r in bypid[pid]],
            units=accepted,facets=record_facets,suppressed_broader_units=suppressed,withheld_evidence=excluded,
            independent_human_review=False)
        topics[pid]=[f["label"] for f in record_facets if f["context_type"] in {"problem_topic","query_topic"}]
    # Every original task stays available in the CSV, including tasks hidden by the min-2 rule.
    assert {r["problem_id"] for r in assignments}==set(meta),"A task lost all supported learning units"
    assert len({(r["problem_id"],r["unit_id"]) for r in assignments})==len(assignments)
    catalog_units=[]
    for uid,g in groups.items():
        member_tags=[dict(tag_id=t,tag=taxonomy[t]) for t in g["source_tag_ids"]]
        methods=[x["tag"] for x in member_tags] or [g["label"]]
        catalog_units.append(dict(cluster_id=uid,label=g["label"],representative=g["label"],
            category=g["category"],kind=g["kind"],description=g["description"],rationale=g["rationale"],
            member_tags=member_tags,detail_methods=methods,algorithm_count=len(methods),problem_count=len(supports[uid]),
            visible=len(supports[uid])>=min_count))
    OUT.mkdir(exist_ok=True)
    fields=["tag","problem_id","title","difficulty","diff_band","url"]
    write(OUT/"all_problems.csv",fields,sorted(assignments,key=lambda r:(r["unit_id"],float(r["difficulty"]),r["problem_id"])))
    write(OUT/"problem_unit_assignments.csv",list(assignments[0]),assignments)
    write(OUT/"assignment_audit.csv",["problem_id","source_tag_id","source_tag","unit_id","action","reason","source_role"],audit)
    write(OUT/"units.csv",["unit_id","label","category","kind","problem_count","visible","source_tag_ids","description","rationale"],
        [dict(g,unit_id=uid,problem_count=len(supports[uid]),visible=int(len(supports[uid])>=min_count),source_tag_ids=" | ".join(g["source_tag_ids"])) for uid,g in groups.items()])
    mapping=[]
    for tid in sorted(active):
        uid=direct.get(tid,"")
        mapping.append(dict(source_tag_id=tid,source_tag=taxonomy[tid],old_cluster_id=old_members[tid]["cluster_id"],
            old_cluster_label=old_members[tid]["label"],disposition="learning_unit" if uid else "metadata",
            unit_id=uid,unit_label=groups[uid]["label"] if uid else "",
            rationale=groups[uid]["rationale"] if uid else facets[tid]["reason"]))
    write(OUT/"tag_mapping.csv",list(mapping[0]),mapping)
    old_to_new=[]
    for c in old["clusters"]:
        direct_units={direct[t["tag_id"]] for t in c["member_tags"] if t["tag_id"] in direct}
        for uid in sorted(direct_units):
            old_to_new.append(dict(old_cluster_id=c["cluster_id"],old_label=c["label"],new_unit_id=uid,new_label=groups[uid]["label"],
                member_tags=" | ".join(t["tag"] for t in c["member_tags"] if direct.get(t["tag_id"])==uid)))
    write(OUT/"old_cluster_to_units.csv",list(old_to_new[0]),old_to_new)
    save(OUT/"problem_details.json",details);save(OUT/"problemTopics.json",topics)
    catalog=dict(version=policy["version"],classification_method="semantic_learning_units",source_problem_count=898,
        source_fine_tag_count=115,learning_unit_count=len(groups),metadata_tag_count=len(facets),
        display_min_problem_count=min_count,visible_unit_count=sum(len(supports[u])>=min_count for u in groups),
        granularity_definition=policy["unit_definition"],independent_human_review=False,
        annotations_provisional=True,clusters=catalog_units,problemCatalog="public/all_problems.csv",
        problemCatalogSha256=sha(OUT/"all_problems.csv"),
        source_sha256={"previous_application_csv":sha(before/"all_problems.csv"),
            "previous_application_catalog":sha(before/"tagCatalog.json"),
            "fine_assignments":sha(WORKSPACE/"validation/revised/all_problems_tagged.csv"),
            "semantic_policy":sha(ROOT/"policy.json")})
    save(OUT/"tagCatalog.json",catalog)
    stats=dict(version=policy["version"],problems=898,source_fine_tags=115,previous_clusters=len(old["clusters"]),
        previous_visible=sum(c["problem_count"]>=2 for c in old["clusters"]),learning_units=len(groups),
        active_units=sum(bool(supports[u]) for u in groups),visible_units=catalog["visible_unit_count"],
        single_problem_units=sum(len(supports[u])==1 for u in groups),zero_problem_units=sum(not supports[u] for u in groups),
        previous_problem_cluster_pairs=len(app_rows),new_problem_unit_pairs=len(assignments),
        metadata_tags=len(facets),problem_metadata_pairs=sum(len(d["facets"]) for d in details.values()),
        broader_unit_suppressions=sum(len(d["suppressed_broader_units"]) for d in details.values()),
        withheld_prior_evidence=sum(len(d["withheld_evidence"]) for d in details.values()),
        source_review_refinements=len(policy["overrides"]),all_problem_ids_preserved=True,
        unchanged_problem_metadata=True,no_paid_api_calls=True,independent_human_review=False,
        unit_kind_counts=dict(Counter(g["kind"] for g in groups.values())),
        input_sha256=catalog["source_sha256"])
    save(OUT/"summary.json",stats)
    report(stats,policy,catalog,mapping)
    print(json.dumps(stats,ensure_ascii=True))

def report(s,p,catalog,mapping):
    lines=["# AtCompass：学習単位に基づくタグ整理案","",
        "作成日：2026-11-05。既存アプリの898問を固定し、階層クラスタリングを使わず、意味と操作に基づいて表示タグを設計した。AIによる編集案であり、第三者が認定した分類体系ではない。","",
        "## 何をそろえたか","",
        "表示する単位は「独立して説明・練習できる具体的な計算課題または技法の系統」とした。同義語だけでなく、同じ操作・計算課題を担う派生形をまとめる。難易度、学習時間、必要知識の量が等しいことは意味しない。","",
        "アルゴリズム、データ構造、DPの状態設計、数え上げや帰着の技法は学習単位として残し、分野・種別を別の属性にした。数学分野名、入力の題材名、課題名だけのタグを同じ層の円グラフに並べるのをやめた。","",
        "| 項目 | 変更前 | 整理案 |","|---|---:|---:|",
        f"| 対象問題 | 898 | {s['problems']} |",
        f"| 表示分類の定義数 | {s['previous_clusters']}クラスタ | {s['learning_units']}学習単位 |",
        f"| 画面に表示する分類 | {s['previous_visible']} | {s['visible_units']} |",
        f"| 問題–表示分類の対応 | {s['previous_problem_cluster_pairs']} | {s['new_problem_unit_pairs']} |",
        "","タグ数を先に決めて削ったわけではない。1問の分類も含め、問題を持つすべての分類を表示する。定義とデータは削除していない。ABC全3,012問の比較用データへの入替えも行っていない。","",
        "## 主な変更","",
        "| 扱い | 例 | 理由 |","|---|---|---|",
        "| 同じ操作の系統に統合 | Fenwick木・Segment Tree → 点更新・区間集約 | 更新と問い合わせの操作を基準にする。区間更新・静的クエリは分ける。 |",
        "| 同じ計算課題に統合 | 最小全域木・Kruskal法・Prim法 → 最小全域木 | 実現方法は詳細タグに残す。 |",
        "| 派生形を統合 | 木DP・全方位木DP → 木上のDP | 同じ構造上のDPとして表示し、全方位の詳細は保持する。 |",
        "| 共起による統合を解消 | 重心分解と畳み込み・FFT | 同じ問題で併用しても、学ぶ技法は異なる。 |",
        "| 共起による統合を解消 | 接尾辞配列・Zアルゴリズム・ローリングハッシュ | 名前が異なる独立した手法を同じ分類にしない。 |",
        "| 解法と題材を分離 | 括弧列・MEX・Fibonacci数 | 題材のラベルを、そのまま解法の分類に使わない。 |",
        "| 原文に基づく具体化 | 線形代数 → アフィン変換の合成 | ABC189 Eの公式解説で使う操作に限定する。 |",
        "| 原文に基づく具体化 | マンハッタン距離 → 距離の式変形・座標変換 | ABC437 Fの公式解説で使う変形に限定する。 |",
        "","## 上位と下位の二重表示を抑えるルール",""]
    for r in p["suppression_rules"]:
        names={g["id"]:g["label"] for g in p["groups"]}
        lines.append("- "+r["reason"]+" 対象："+names[r["base"]]+" → "+ " / ".join(names[u] for u in r["when_any"])+"。")
    lines += ["",
        "これは表示用の優先規則であり、元の技法の利用を否定する判定ではない。別解が異なる分類を使う場合もあるため、元の対応は problem_details.json と assignment_audit.csv に保存した。","",
        "## 題材・分野として残す6種類","",
        "| 元タグ | 詳細での扱い | 理由 |","|---|---|---|"]
    for f in p["facets"]:lines.append(f"| {f['tag_id']} {f['label']} | {f['type']} | {f['reason']} |")
    lines += ["",
        "括弧列・MEXなどの題材は、該当問題の一覧に表示する。線形代数という分野名や、計算量評価だけのFibonacci数は、解法の円グラフとしては表示しない。","",
        "## 学習単位の一覧","",
        "| ID | 表示名 | 分野 | 問題数 | 表示 | 定義 |","|---|---|---|---:|---|---|"]
    for g in catalog["clusters"]:
        lines.append(f"| {g['cluster_id']} | {g['label']} | {g['category']} | {g['problem_count']} | {'表示' if g['visible'] else '非表示（対象問題なし）'} | {g['description']} |")
    lines += ["",
        "## 妥当性と限界","",
        f"- 元の115タグすべてについて、学習単位または詳細属性への対応と理由を記録した。元の問題ID・タイトル・難易度・URLを898問すべてで保持した。",
        f"- 一般DPなどの上位分類を{ s['broader_unit_suppressions']}問題–分類で抑制した。抑制後も元タグは詳細に残る。",
        f"- 既存レビューで参考・根拠不足・分析用・曖昧と記録された{ s['withheld_prior_evidence']}対応は表示の根拠から保留した。今回新たに全件の主解・別解・補助を確認したわけではない。",
        "- 既存の問題への付与には未レビューが多く残る。名称と分類の意味を整理しても、誤付与や拾い漏れが解消したとは言えない。",
        "- 点更新のデータ構造を一つにまとめるか、確率DPと期待値DPを分けるかなどには編集判断が含まれる。policy.jsonの定義と理由をチームでレビューする必要がある。",
        "- 一般の状態遷移DPは残余分類であり、まだ具体的な状態型へ整理できる問題が残り得る。全タグが同じ学習負荷になったとは主張しない。",
        "- 進捗リングは問題単位のAC・WA・未挑戦を集計する。その分類の習得を直接測定するものではなく、同じ問題が複数分類に現れることもある。",
        "- 同レート帯の集計は分類版が変わるため旧版の数値を流用しない。現在の版と一致するデータがない場合は、既存の互換性チェックで非表示になる。",
        "",
        "## 確認資料","",
        "- [元115タグの対応表・変更理由](output/tag_mapping.csv)",
        "- [表示名・定義・件数](output/units.csv)",
        "- [旧クラスタから新しい学習単位への対応](output/old_cluster_to_units.csv)",
        "- [問題ごとの対応](output/problem_unit_assignments.csv)",
        "- [保留・上位分類の抑制・具体化の記録](output/assignment_audit.csv)",
        "- [元タグ・題材・根拠を残した詳細](output/problem_details.json)",
        "- [差し替え用CSV](output/all_problems.csv)",
        "- [差し替え用カタログ](output/tagCatalog.json)",
        "- [編集方針](policy.json)","",
        "再生成：既存仮想環境のPythonで build_dataset.py を実行する。before/ に初回のアプリ用CSV・カタログを保存しており、差し替え後も同じ入力から作り直せる。",
        "外部AI APIは使っていない。追加API費用0円。公開・コミットは行わない。",""]
    (ROOT/"README.md").write_text("\n".join(lines),encoding="utf-8")
if __name__=="__main__":build()
