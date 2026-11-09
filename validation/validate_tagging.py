# -*- coding: utf-8 -*-
"""Reproduce local tagging validation; no network/API calls and no source overwrites."""
import csv, json, hashlib, re, difflib
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
from sklearn.metrics import adjusted_rand_score
from statement_extraction import self_check

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT / "validation_sources" / "ac_analyze_test"
COMMIT = "67c0f2937c8d4460ea8468953a6ee69b15e75b46"

def read_csv(file):
    with file.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))

def write_csv(file, rows, columns):
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def read_json(file):
    return json.loads(file.read_text(encoding="utf-8-sig"))

def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()

def regex_term(term):
    # English short names must not match inside other words.
    return re.compile((r"(?<![A-Za-z])" if re.match(r"^[A-Za-z]",term) else "")
                      + re.escape(term)
                      + (r"(?![A-Za-z])" if re.search(r"[A-Za-z]$",term) else ""), re.I)

def main():
    original = read_csv(ROOT / "all_problems.csv")
    baseline = read_csv(ROOT / "all_problems_tagged.csv")
    catalog = read_csv(ROOT / "tag_catalog.csv")
    tags = {r["tag_id"]:r["tag"] for r in catalog}
    problems = {r["problem_id"]:r for r in original}
    data = {r["task_id"]: (r, file.relative_to(REPO).as_posix())
            for file in sorted((REPO / "data").rglob("*.json"))
            for r in [read_json(file)]}
    outputs = {r["task_id"]:r for file in sorted((REPO / "output").rglob("*.json"))
               for r in [read_json(file)]}
    reviews = read_json(HERE / "manual_reviews.json")
    decisions = {(r["problem_id"],r["tag_id"]):r for r in reviews}
    assert len(decisions) == len(reviews)
    before = {(r["problem_id"],r["tag_id"]):r.copy() for r in baseline}
    assert len(before) == len(baseline)
    assert digest(ROOT / "all_problems.csv") == digest(REPO / "output" / "all_problems.csv")
    assert set(problems) <= set(data)
    for r in reviews:
        assert r["problem_id"] in problems and r["tag_id"] in tags
        available = {e["url"] for e in data[r["problem_id"]][0]["editorials"]}
        assert set(r["evidence_urls"]) <= available, r
        assert r["independent_human_review"] is False
        key = (r["problem_id"],r["tag_id"])
        if r["status"] in {"supported_existing","refine_existing"}:
            assert key in before
        if r["status"] == "add_supported":
            assert key not in before
        if r["apply"]:
            assert r["status"] in {"add_supported","refine_existing"}

    coverage, quality = [], []
    recovered_count = 0
    for pid in sorted(problems):
        obj, rel = data[pid]
        statement = obj["statement"]
        tail = statement.split("制約",1)[1].strip() if "制約" in statement else ""
        issues = []
        if "制約" not in statement:
            issues.append("no_constraint_heading")
        elif len(tail) < 8:
            issues.append("empty_constraint_tail")
        if len(statement) < 100:
            issues.append("short_statement_only_heuristic")
        fixed = HERE / "recovered_statements" / (pid+".json")
        recovered = read_json(fixed) if fixed.exists() else None
        if recovered:
            recovered_tail = recovered["statement"].split("制約",1)[-1].strip()
            assert "制約" in recovered["statement"] and len(recovered_tail) >= 8, pid
            recovered_count += 1
        coverage.append(dict(problem_id=pid,title=problems[pid]["title"],
            title_matches=problems[pid]["title"] == obj["title"],
            statement_available=bool(statement.strip()),
            editorial_available=any(e.get("text","").strip() for e in obj["editorials"]),
            source_file=rel,statement_source_url=problems[pid]["url"],
            editorial_urls=" | ".join(e["url"] for e in obj["editorials"]),
            source_sha256=digest(REPO/rel),
            recovered_statement=str(fixed.relative_to(ROOT)).replace("\\","/") if recovered else ""))
        if issues:
            quality.append(dict(problem_id=pid,issues=" | ".join(issues),
                original_length=len(statement),
                recovered_length=len(recovered["statement"]) if recovered else "",
                recovery_status="recovered" if recovered else "short_only_not_proven_truncated",
                source_url=recovered["source_url"] if recovered else problems[pid]["url"]))
    assert all(r["title_matches"] and r["statement_available"] and r["editorial_available"] for r in coverage)
    write_csv(HERE/"source_coverage.csv",coverage,list(coverage[0]))
    write_csv(HERE/"statement_quality.csv",quality,list(quality[0]))
    scope = []
    for pid in sorted(data):
        output = outputs.get(pid)
        scope.append(dict(problem_id=pid,in_all_problems_csv=pid in problems,
            original_output_present=output is not None,
            original_tags_empty=(not output.get("tags")) if output is not None else "",
            source_file=data[pid][1]))
    write_csv(HERE/"corpus_scope.csv",scope,list(scope[0]))

    unused = [r["tag_id"] for r in catalog if int(r["problem_count"]) == 0]
    rules = read_json(HERE/"tag_detection_rules.json")
    hits = []
    for tid in unused:
        terms = list(dict.fromkeys(rules.get(tid,[]) + [tags[tid]]))
        patterns = [(term,regex_term(term)) for term in terms]
        for pid in sorted(problems):
            obj, rel = data[pid]
            # Preserve original scan for audit reproducibility. Recovered statements are separate evidence.
            sources = [("statement",obj["statement"],problems[pid]["url"])]
            sources += [("editorial",e.get("text",""),e["url"]) for e in obj["editorials"]]
            for kind, body, url in sources:
                matches = [term for term,pattern in patterns if pattern.search(body)]
                if matches:
                    review = decisions.get((pid,tid),{})
                    hits.append(dict(tag_id=tid,tag=tags[tid],problem_id=pid,
                        title=problems[pid]["title"],matched_terms=" | ".join(matches),
                        source_kind=kind,source_url=url,source_file=rel,
                        status=review.get("status","candidate_only")))
    write_csv(HERE/"candidate_hits.csv",hits,list(hits[0]))
    audit = []
    for tid in unused:
        relevant = [r for r in reviews if r["tag_id"] == tid]
        additions = [r for r in relevant if r["status"] == "add_supported"]
        candidate_ids = {h["problem_id"] for h in hits if h["tag_id"] == tid}
        audit.append(dict(tag_id=tid,tag=tags[tid],candidate_problem_count=len(candidate_ids),
            confirmed_additions=len(additions),reviewed_candidate_pairs=len(relevant),
            status="confirmed_omission" if additions else
                ("candidate_unreviewed_or_partial" if candidate_ids else "no_name_hit_not_absence"),
            reviewed_statuses=" | ".join(sorted({r["status"] for r in relevant}))))
    write_csv(HERE/"unused_tag_audit.csv",audit,list(audit[0]))

    reviewed_rows = []
    for r in reviews:
        row = dict(r)
        row.update(tag=tags[r["tag_id"]],current_related=int((r["problem_id"],r["tag_id"]) in before))
        row["evidence_urls"] = " | ".join(r["evidence_urls"])
        reviewed_rows.append(row)
    write_csv(HERE/"reviewed_pairs.csv",reviewed_rows,list(reviewed_rows[0]))
    sample = read_json(HERE/"sample_metadata.json")
    # Blind problem-level review avoids showing existing labels or assistant judgments.
    blind_rows = []
    for pid in sample["problem_ids"]:
        blind_rows.append(dict(problem_id=pid,title=problems[pid]["title"],
            difficulty=problems[pid]["difficulty"],diff_band=problems[pid]["diff_band"],
            source_file=data[pid][1],
            recovered_statement_file=("validation/recovered_statements/"+pid+".json")
                if (HERE/"recovered_statements"/(pid+".json")).exists() else "",
            statement_url=problems[pid]["url"],
            editorial_urls=" | ".join(e["url"] for e in data[pid][0]["editorials"]),
            human_tag_ids="",human_roles="",human_reason="",reviewer=""))
    write_csv(HERE/"human_review_blind.csv",blind_rows,list(blind_rows[0]))
    selection = []
    for band in sorted({p["diff_band"] for p in problems.values()}):
        members = [pid for pid,p in problems.items() if p["diff_band"] == band]
        ordered = sorted(members,key=lambda pid:hashlib.sha256((sample["seed"]+":"+pid).encode()).hexdigest())
        expected = ordered[:6]
        assert set(expected) <= set(sample["problem_ids"])
        for pid in expected:
            prior = [key for key in before if key[0]==pid]
            checked = [decisions.get(key) for key in prior]
            assert all(checked),pid
            selection.append(dict(problem_id=pid,difficulty=problems[pid]["difficulty"],
                diff_band=band,original_pair_count=len(prior),
                supported_pairs=sum(r["status"]=="supported_existing" for r in checked),
                pending_pairs=sum(r["status"]=="needs_review" for r in checked),
                seed=sample["seed"]))
    write_csv(HERE/"sample_selection.csv",selection,list(selection[0]))

    revised = {key:dict(row) for key,row in before.items()}
    for r in reviews:
        key = (r["problem_id"],r["tag_id"])
        if r["apply"] and r["status"] == "refine_existing":
            del revised[key]
        elif r["apply"] and r["status"] == "add_supported":
            p = problems[r["problem_id"]]
            revised[key] = dict(p,tag=tags[r["tag_id"]],tag_id=r["tag_id"],related="1",
                labeling_method="source_validation",original_tags=" | ".join(sorted({x["tag"] for x in original if x["problem_id"]==r["problem_id"]})),
                editorial_url=" | ".join(r["evidence_urls"]),needs_review="0",note=r["reason"])
    for key,row in revised.items():
        review = decisions.get(key)
        row.update(validation_status=review["status"] if review else "not_reviewed",
            validated_role=review["role"] if review else "unreviewed",
            validation_evidence_urls=" | ".join(review["evidence_urls"]) if review else "",
            independent_human_review="0")
        if review and review["status"]=="needs_review":
            row["needs_review"]="1"
    write_csv(HERE/"revised"/"all_problems_tagged.csv",
              [revised[key] for key in sorted(revised)],list(next(iter(revised.values()))))
    matrix_rows = [dict(problem_id=pid,**{tid:int((pid,tid) in revised) for tid in tags}) for pid in sorted(problems)]
    assert all(sum(r[tid] for tid in tags)>0 for r in matrix_rows)
    write_csv(HERE/"revised"/"problem_tag_matrix.csv",matrix_rows,["problem_id"]+list(tags))
    counts = Counter(tid for pid,tid in revised)
    write_csv(HERE/"revised"/"tag_catalog.csv",
              [dict(r,problem_count=counts[r["tag_id"]]) for r in catalog],list(catalog[0]))

    # Team review sheet includes every existing pair and every detected candidate.
    human_keys = set(before) | set(decisions) | {(h["problem_id"],h["tag_id"]) for h in hits}
    human_rows = []
    for pid,tid in sorted(human_keys):
        r=decisions.get((pid,tid),{})
        human_rows.append(dict(problem_id=pid,title=problems[pid]["title"],tag_id=tid,tag=tags[tid],
            baseline_related=int((pid,tid) in before),revised_related=int((pid,tid) in revised),
            assistant_status=r.get("status","not_reviewed"),assistant_role=r.get("role",""),
            assistant_reason=r.get("reason",""),evidence_urls=" | ".join(r.get("evidence_urls",[])),
            source_file=data[pid][1],human_judgment="",human_role="",human_reason="",reviewer=""))
    write_csv(HERE/"human_review.csv",human_rows,list(human_rows[0]))

    def clusters(pairs):
        active = sorted({tid for pid,tid in pairs})
        values = np.array([[int((pid,tid) in pairs) for pid in sorted(problems)] for tid in active],dtype=bool)
        labels = fcluster(linkage(pdist(values,metric="jaccard"),method="average"),t=0.9,criterion="distance")
        return dict(zip(active,map(int,labels)))
    old_clusters,new_clusters = clusters(before),clusters(revised)
    common = sorted(set(old_clusters)&set(new_clusters))
    comparison = dict(cut=0.9,distance="jaccard",linkage="average",
        baseline_active_tags=len(old_clusters),revised_active_tags=len(new_clusters),
        baseline_clusters=len(set(old_clusters.values())),revised_clusters=len(set(new_clusters.values())),
        common_tag_ARI=adjusted_rand_score([old_clusters[t] for t in common],[new_clusters[t] for t in common]),
        note="修正案の全役割の二値関連を用いた探索的比較。最適な群数やタグ間の同義性を保証しない。")
    (HERE/"clustering_comparison.json").write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    write_csv(HERE/"revised"/"tag_cluster_membership.csv",
              [dict(tag_id=t,tag=tags[t],cluster=c,problem_count=counts[t]) for t,c in new_clusters.items()],
              ["tag_id","tag","cluster","problem_count"])

    upstream = REPO/"scraper"/"tasks.py"
    old = upstream.read_text(encoding="utf-8")
    score_start = old.index("    # 配点削除")
    score_end = old.index("    # タイトル抽出",score_start)
    fixed = old[:score_start]+old[score_end:]
    extract_start = fixed.index('    statement = ja.get_text')
    extract_end = fixed.index('    return {',extract_start)
    section_code = """    # 本文中の「入力」は残し、実際の見出しだけで区切る。
    sections = ja.select(".part > section") or ja.find_all("section")
    selected = []
    for section in sections:
        heading = section.find(["h2", "h3"])
        label = heading.get_text(strip=True) if heading else ""
        if label in {"入力", "出力"} or label.startswith(("入力例", "出力例")):
            break
        selected.append(section.get_text("\\n", strip=True))
    if not selected:
        raise RuntimeError(f"problem statement sections not found: {task_id}")
    statement = "\\n".join(selected)

"""
    # The patch source needs actual Python backslash-n literals, not escaped backslash-backslash-n.
    section_code = section_code.replace('\\\\n','\\n')
    fixed = fixed[:extract_start]+section_code+fixed[extract_end:]
    compile(fixed,str(upstream),"exec")
    patch = "".join(difflib.unified_diff(old.splitlines(True),fixed.splitlines(True),
                                        fromfile="a/scraper/tasks.py",tofile="b/scraper/tasks.py"))
    (HERE/"scraper_tasks.patch").write_text(patch,encoding="utf-8")

    summary = dict(repository_commit=COMMIT,csv_rows=len(original),unique_problems=len(problems),
        repository_data_problems=len(data),repository_output_problems=len(outputs),
        original_empty_tag_outputs=sum(not r.get("tags") for r in outputs.values()),
        csv_scope_extra_problems=len(set(data)-set(problems)),
        aligned_statement_and_editorial_problems=len(coverage),recovered_statements=recovered_count,
        baseline_pairs=len(before),revised_pairs=len(revised),
        additions=sum(r["apply"] and r["status"]=="add_supported" for r in reviews),
        refinements=sum(r["apply"] and r["status"]=="refine_existing" for r in reviews),
        sampled_problems=len(selection),sampled_existing_pairs=sum(r["original_pair_count"] for r in selection),
        sample_supported_pairs=sum(r["supported_pairs"] for r in selection),
        sample_pending_pairs=sum(r["pending_pairs"] for r in selection),
        reviewed_problem_count=len({r["problem_id"] for r in reviews}),reviewed_pairs=len(reviews),
        candidate_rows=len(hits),unused_tags_before=len(unused),unused_tags_after=len(tags)-len(counts),
        independent_human_review=False,extractor_checks=self_check(),
        source_sha256={f:digest(ROOT/f) for f in ["all_problems.csv","tags.md","all_problems_tagged.csv","tag_catalog.csv"]},
        clustering=comparison)
    (HERE/"validation_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report = """# タグ付けの検証結果

対象は all_problems.csv の{csv_rows}データ行・{unique_problems}固有問題です。
チームリポジトリの固定コミット {repository_commit} と照合しました。
元CSVはリポジトリのCSVとバイト単位で一致し、全{aligned_statement_and_editorial_problems}問で問題文・解説があり、タイトルも一致しました。

## 確認範囲
難易度の5帯から固定シードで各6問、計{sampled_problems}問を抽出しました。
その既存{sampled_existing_pairs}組のうち、{sample_supported_pairs}組には解法・補助処理・概念としての根拠があり、{sample_pending_pairs}組は定義や解説の裏付けに追加確認が必要でした。
未使用タグの名前の候補検出と、疑わしい既存タグを狙った確認を合わせ、{reviewed_problem_count}問・{reviewed_pairs}組の判断を記録しました。
名前の一致だけを確認済みとはしていません。全898問の意味的な正しさや再現率を検証し終えたわけではありません。

確認済み組には別解、補助データ構造、分析で用いる概念も含まれます。
primary（主解法）、alternative（別解）、supporting（補助処理）、concept / analysis_concept（概念・計算量説明）を区別しました。
「計算できる解法」と「最も適した解法」は別です。実行時間の測定・最適性比較は実施していません。
本検証はタグを作成した同じアシスタントによる再点検です。独立した人による評価ではなく、61/67等を全体の精度として報告できません。

## 修正案
根拠のある{additions}組を追加し、通常BFSから0-1 BFSへの{refinements}組の細分化を行いました。
修正案は{revised_pairs}組です。元のファイルは保持し、revised/ に別ファイルで出力しました。
追加の根拠・役割は reviewed_pairs.csv、全既存・候補組の独立レビュー欄は human_review.csv にあります。
追加の代表例は二部グラフ判定、2-SAT、Li Chao Tree、重心分解、FFT・畳み込み、Color Coding、二部マッチングです。
FFT等はユーザー解説に示された別解です。全てを公式解説の主解法とは扱っていません。

修正案でも validation_status=not_reviewed の行は未点検です。
needs_review は判断が必要な行であり、自動で削除しません。
BFSの細分化は不適切な手法の削除という意味ではなく、親子関係のあるタグの粒度調整です。
0は未付与を示し、適用不能を証明する値ではありません。

## 未使用タグ
266種類中、使用されたタグは修正前104種類、修正案では{active}種類です。
未使用は{unused_tags_before}種類から{unused_tags_after}種類になりました。
候補検出は日本語・英語表記の限定した辞書によるもので、名前が出ない解法や記述の欠落を検出できません。
unused_tag_audit.csv の no_name_hit_not_absence は「名前を見つけていない」であり「この問題集合に存在しない」ではありません。
フォードの文字列一致、LCS参考資料、level ancestorとLCAの混同は採用しませんでした。
一般の最小カットやマッチングは、理論的帰着・親概念としてのみ現れる場合があります。

## 元データの注意点
リポジトリの data は{repository_data_problems}問、output JSONは{repository_output_problems}問です。
outputで元のtagsが空の問題が{original_empty_tag_outputs}問あり、CSV変換処理はそれらを出力しません。
したがって全898問にタグが付いたという結果は、最初からタグのある問題に偏ったCSV内での結果です。
CSV外の{csv_scope_extra_problems}問は今回のタグ付け対象へ追加していません。corpus_scope.csvで確認できます。
fetch_data.py は難易度2000以上・難易度不明を除外します。高度なアルゴリズムの低出現を考察する際の収集条件です。

scraper/tasks.py は最初の段落を無条件に削除し、本文中で最初に現れる「入力」から先を切り落とします。
本文や制約の欠落が疑われた90問を公式ページから取得し直し、全{recovered_statements}問で制約の見出しと内容を保持できました。
見出しに基づく抽出へ変えるパッチ scraper_tasks.patch と復元用スクリプトを用意しました。
短い問題文だけでは欠損と断定しません。また、今回復元しなかった808問の全文が完全であることは保証しません。
以前解説を取得できなかった40問についてもチームデータでは解説があります。存在することとタグの正しさは分けて評価します。
解説データにはユーザー解説もあり、参考資料・他問題の言及を含むため、タグ名を検索しただけでは正解ラベルにできません。

## クラスタリングへの影響
同じJaccard距離・average linkage・切断距離0.9では、修正前の70群から修正案の{clusters}群になります。
未使用タグはこの群数に含めません。共通タグ上のARIは{ari:.4f}です。
これは部分的な修正の影響確認であり、最適な表示数やクラスタリング全体の妥当性の保証ではありません。
主解法のみ、別解を含む場合、補助処理を含む場合を比較するには、残りの組にも役割を付ける必要があります。

## チームでの次の検証
1. human_review_blind.csv の30問を、既存のタグ・アシスタントの判定を見ずに別の担当者が問題文・制約・解説からタグ付けする。タグ一覧は tags.md を使い、human_tag_ids に Txxx を | 区切りで記入する。可能なら二人が別々に判定してから相違を協議する。
2. 主解法・別解・補助処理・概念の役割を記録し、人のラベルを確定してから修正前・修正案と比較する。human_review.csv は比較・不一致の協議用に使い、human_judgmentを relevant / not_relevant / uncertain とする。
3. 付与済みの精度と、未付与からの漏れを別々に集計する。今回の名前検索の候補だけから全体の再現率を算出しない。
4. タグ定義と親子関係を揃え、役割別の距離・切断位置の安定性と、人が見た群の解釈を評価する。
卒業制作では方法、標本抽出、独立性の限界、未点検範囲を明記して報告できます。

## 再実行
ローカルvenvに requirements-clustering.txt と requirements-validation.txt を入れ、
.venv-clustering/Scripts/python.exe -X utf8 validation/validate_tagging.py を実行します。
ネットワークやLLM APIは使いません。元CSV・タグ表・修正前タグ付けを読み、検証用ファイルだけを出力します。
固定コミットのローカルclone、manual_reviews.json、tag_detection_rules.json、sample_metadata.json、復元済み問題文が入力です。
公式ページから再取得する場合のみ recover_statements.py を実行します。
""".format(**summary,active=len(counts),clusters=comparison["revised_clusters"],ari=comparison["common_tag_ARI"])
    (HERE/"validation_report.md").write_text(report,encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
