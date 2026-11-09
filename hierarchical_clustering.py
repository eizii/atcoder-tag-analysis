# -*- coding: utf-8 -*-
"""Cluster algorithm tags by overlap in the problems carrying each tag.

Run from any working directory:
    .venv-clustering/Scripts/python.exe hierarchical_clustering.py
    .venv-clustering/Scripts/python.exe hierarchical_clustering.py --threshold 0.85

The matrix contains assignment observations, not suitability/optimality scores.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import scipy
from scipy.cluster.hierarchy import (
    cophenet, dendrogram, fcluster, is_monotonic, is_valid_linkage, linkage,
)
from scipy.spatial.distance import pdist, squareform
import sklearn
from sklearn.metrics import adjusted_rand_score, silhouette_score


ROOT = Path(__file__).resolve().parent
SOURCE_NAMES = [
    "all_problems.csv", "tags.md", "problem_tag_matrix.csv",
    "all_problems_tagged.csv", "tag_catalog.csv",
]


def csv_rows(file):
    with file.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(file, columns, rows):
    with file.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def load_inputs(input_dir=ROOT):
    with (input_dir / "problem_tag_matrix.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        rows = list(csv.reader(handle))
    catalog = csv_rows(input_dir / "tag_catalog.csv")
    names = rows[0][1:]
    if names == [row["tag_id"] for row in catalog]:
        names = [row["tag"] for row in catalog]
    problems = [row[0] for row in rows[1:]]
    if not rows or rows[0][0] != "problem_id":
        raise ValueError("Unexpected matrix header")
    if len(set(problems)) != len(problems) or len(set(names)) != len(names):
        raise ValueError("Duplicate problem IDs or tag names")
    if any(len(row) != len(names) + 1 for row in rows[1:]):
        raise ValueError("Inconsistent matrix width")
    raw = [row[1:] for row in rows[1:]]
    if any(cell not in ("0", "1") for row in raw for cell in row):
        raise ValueError("Matrix must contain only literal 0 or 1")
    # Parse numbers first: bool("0") would incorrectly be True.
    matrix = np.asarray(raw, dtype=np.uint8).T.astype(bool)
    if not matrix.any(axis=0).all():
        raise ValueError("A problem has no assigned tags")
    if [row["tag"] for row in catalog] != names:
        raise ValueError("Catalog and matrix column order differ")
    if [int(row["problem_count"]) for row in catalog] != matrix.sum(axis=1).tolist():
        raise ValueError("Catalog counts do not match matrix")
    if len({row["tag_id"] for row in catalog}) != len(catalog):
        raise ValueError("Duplicate tag IDs")
    tag_idx = {name: i for i, name in enumerate(names)}
    problem_idx = {pid: i for i, pid in enumerate(problems)}
    label_rows = csv_rows(input_dir / "all_problems_tagged.csv")
    rebuilt = np.zeros_like(matrix)
    review_mask = np.zeros_like(matrix)
    evidence = {}
    for row in label_rows:
        i, j = tag_idx[row["tag"]], problem_idx[row["problem_id"]]
        if rebuilt[i, j]:
            raise ValueError("Duplicate problem-tag pair")
        if row["tag_id"] != catalog[i]["tag_id"] or row["related"] != "1":
            raise ValueError("Invalid tag ID or relation value")
        if row["needs_review"] not in ("0", "1"):
            raise ValueError("Invalid needs_review")
        rebuilt[i, j] = True
        review_mask[i, j] = row["needs_review"] == "1"
        evidence[(i, j)] = row
    if not np.array_equal(matrix, rebuilt):
        raise ValueError("Tagged CSV and matrix do not agree")
    original_problems = {r["problem_id"] for r in csv_rows(ROOT / "all_problems.csv")}
    if original_problems != set(problems):
        raise ValueError("Original problem IDs do not match matrix")
    return matrix, problems, catalog, review_mask, evidence


def normalized_labels(tree, n, threshold):
    raw = fcluster(tree, t=threshold, criterion="distance")
    # Cluster numbers are stable within this cut: order by minimum leaf index.
    groups = sorted(
        (np.flatnonzero(raw == label).tolist() for label in set(raw)),
        key=lambda members: min(members),
    )
    labels = np.zeros(n, dtype=int)
    for cluster_id, members in enumerate(groups, 1):
        labels[members] = cluster_id
    return labels


def cut_stats(model, threshold):
    labels = normalized_labels(model["Z"], len(model["tags"]), threshold)
    sizes = Counter(labels.tolist())
    k = len(sizes)
    silhouette = None
    if 1 < k < len(labels):
        silhouette = float(silhouette_score(model["D"], labels, metric="precomputed"))
    return {
        "threshold": float(threshold), "tag_count": len(labels),
        "cluster_count": k, "multi_tag_clusters": sum(size > 1 for size in sizes.values()),
        "singleton_clusters": sum(size == 1 for size in sizes.values()),
        "silhouette": silhouette,
    }


def build_model(key, title, matrix, catalog, min_support, threshold):
    indices = np.flatnonzero(matrix.sum(axis=1) >= min_support)
    if len(indices) < 2:
        raise ValueError("At least two nonempty tags are required")
    vectors = matrix[indices]
    condensed = pdist(vectors, metric="jaccard")
    distances = squareform(condensed)
    tree = linkage(condensed, method="average", optimal_ordering=True)
    if not is_valid_linkage(tree) or not is_monotonic(tree):
        raise AssertionError("Invalid or nonmonotonic linkage")
    if not np.all(np.isfinite(distances)) or not np.allclose(distances, distances.T):
        raise AssertionError("Invalid distances")
    if not np.allclose(np.diag(distances), 0):
        raise AssertionError("Distance diagonal is not zero")
    if np.any(distances < 0) or np.any(distances > 1):
        raise AssertionError("Distance outside [0, 1]")
    # Independently verify every binary Jaccard distance using set arithmetic.
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            shared = np.count_nonzero(vectors[i] & vectors[j])
            union = np.count_nonzero(vectors[i] | vectors[j])
            expected = 1 - shared / union
            if not np.isclose(distances[i, j], expected, atol=1e-12):
                raise AssertionError("Jaccard distance mismatch")
    model = {
        "key": key, "title": title, "indices": indices, "X": vectors,
        "tags": [catalog[i] for i in indices], "Z": tree, "D": distances,
        "cophenetic_correlation": float(cophenet(tree, condensed)[0]),
        "min_support": min_support,
    }
    model["labels"] = normalized_labels(tree, len(indices), threshold)
    model["stats"] = cut_stats(model, threshold)
    # Evaluate all unique merge-height cuts and a fixed comparison grid.
    thresholds = sorted(set(
        [0, .25, .5, .6, .7, .75, .8, .85, .9, .925, .95, .975, .99, .999, 1]
        + [float(height) for height in tree[:, 2]] + [threshold]
    ))
    model["metrics"] = [cut_stats(model, t) for t in thresholds]
    valid = [row for row in model["metrics"] if row["silhouette"] is not None]
    model["best_silhouette_cut"] = max(valid, key=lambda r: r["silhouette"]) if valid else None
    return model


def self_check():
    # Both shared positives and differing positives matter; shared zeros do not.
    toy = np.array([[1, 1, 0], [1, 0, 1], [0, 0, 1]], dtype=bool)
    distances = pdist(toy, "jaccard")
    np.testing.assert_allclose(distances, [2 / 3, 1, 1 / 2], atol=1e-12)
    np.testing.assert_allclose(
        pdist(np.pad(toy, ((0, 0), (0, 2))), "jaccard"), distances
    )
    tree = linkage(distances, "average")
    np.testing.assert_allclose(tree[:, 2], [.5, 5 / 6], atol=1e-12)
    assert len(set(fcluster(tree, .6, criterion="distance"))) == 2
    assert len(set(fcluster(tree, 1, criterion="distance"))) == 1
    assert np.asarray([["0", "1"]], dtype=np.uint8).astype(bool).tolist() == [[False, True]]


def configure_fonts():
    available = {font.name for font in font_manager.fontManager.ttflist}
    family = next((name for name in ["Yu Gothic", "Meiryo", "Noto Sans CJK JP",
                   "IPAexGothic", "MS Gothic"] if name in available), "DejaVu Sans")
    matplotlib.rcParams.update({
        "font.family": [family, "DejaVu Sans"], "axes.unicode_minus": False,
        "svg.fonttype": "none", "pdf.fonttype": 42,
    })
    return family


def save_dendrogram(model, output, threshold):
    count = len(model["tags"])
    labels = [
        f'{tag["tag_id"]}  {tag["tag"]}  (n={int(model["X"][i].sum())})'
        for i, tag in enumerate(model["tags"])
    ]
    figure, axis = plt.subplots(figsize=(15, max(10, count * .235 + 1.5)))
    result = dendrogram(
        model["Z"], labels=labels, orientation="right", leaf_font_size=9,
        color_threshold=threshold, above_threshold_color="#94a3b8", ax=axis,
    )
    axis.axvline(threshold, color="#dc2626", linestyle="--", linewidth=1.2,
                 label=f"distance cut = {threshold:g}")
    axis.set_xlim(-.01, 1.025)
    axis.set_xlabel("Jaccard distance: 0 = same assigned problems, 1 = no overlap")
    axis.set_title(
        f'{model["title"]}\nAverage linkage / {count} tags / '
        f'{model["stats"]["cluster_count"]} clusters at cut {threshold:g}',
        loc="left", pad=16, fontsize=13,
    )
    axis.set_xticks(np.linspace(0, 1, 11))
    axis.grid(axis="x", alpha=.2)
    axis.legend(loc="lower right", fontsize=9)
    figure.subplots_adjust(left=.44, right=.985, top=.955, bottom=.04)
    for extension in ("svg", "png"):
        figure.savefig(output / f'dendrogram_{model["key"]}.{extension}',
                       dpi=130, facecolor="white")
        if extension == "svg":
            svg_file = output / f'dendrogram_{model["key"]}.svg'
            clean_svg = "\n".join(line.rstrip() for line in svg_file.read_text(encoding="utf-8").splitlines())
            svg_file.write_text(clean_svg + "\n", encoding="utf-8")

    plt.close(figure)
    model["leaf_order"] = result["leaves"]


def groups_for(model):
    rows = []
    for cluster_id in sorted(set(model["labels"].tolist())):
        members = np.flatnonzero(model["labels"] == cluster_id)
        distances = model["D"][np.ix_(members, members)]
        mean_similarity = (
            float(np.mean(1 - distances[np.triu_indices(len(members), 1)]))
            if len(members) > 1 else None
        )
        representative = int(members[np.argmin(distances.sum(axis=1))])
        rows.append({
            "cluster_id": f"C{cluster_id:03d}", "members": members.tolist(),
            "size": len(members),
            "representative": model["tags"][representative]["tag"],
            "mean_pair_jaccard": mean_similarity,
            "problem_union_count": int(model["X"][members].any(axis=0).sum()),
        })
    return rows


def export_model(model, output, threshold, review_mask):
    leaf_rows = []
    membership = []
    group_map = {g["cluster_id"]: g for g in groups_for(model)}
    for i, tag in enumerate(model["tags"]):
        cluster_id = f'C{model["labels"][i]:03d}'
        group = group_map[cluster_id]
        global_i = int(model["indices"][i])
        leaf_rows.append([i, tag["tag_id"], tag["tag"], int(model["X"][i].sum())])
        membership.append([
            model["key"], threshold, cluster_id, group["size"], tag["tag_id"],
            tag["tag"], int(model["X"][i].sum()), int(review_mask[global_i].sum()),
            int(model["X"][i].sum()) < 3, group["representative"],
            group["problem_union_count"], group["mean_pair_jaccard"],
        ])
    write_csv(output / f'leaves_{model["key"]}.csv',
              ["leaf_node_id", "tag_id", "tag", "problem_count"], leaf_rows)
    write_csv(output / f'clusters_{model["key"]}.csv', [
        "model", "distance_threshold", "cluster_id", "cluster_size", "tag_id", "tag",
        "problem_count_in_model", "needs_review_pairs_in_input", "low_support",
        "representative_tag", "cluster_problem_union_count", "mean_pair_jaccard",
    ], membership)
    write_csv(output / f'linkage_{model["key"]}.csv',
              ["merge_index", "new_node_id", "left_node_id", "right_node_id",
               "distance", "leaf_count"],
              [[i, len(model["tags"]) + i, int(row[0]), int(row[1]), float(row[2]),
                int(row[3])] for i, row in enumerate(model["Z"])])


def review_sensitivity(baseline, filtered, catalog, threshold):
    base_index = {int(idx): i for i, idx in enumerate(baseline["indices"])}
    filtered_index = {int(idx): i for i, idx in enumerate(filtered["indices"])}
    common = sorted(set(base_index) & set(filtered_index))
    left = [int(baseline["labels"][base_index[i]]) for i in common]
    right = [int(filtered["labels"][filtered_index[i]]) for i in common]
    changed_pairs = sum(
        (left[i] == left[j]) != (right[i] == right[j])
        for i in range(len(common)) for j in range(i + 1, len(common))
    )
    rows = []
    changed_tags = 0
    for pos, tag_idx in enumerate(common):
        base_peers = [catalog[i]["tag_id"] for j, i in enumerate(common)
                      if j != pos and left[j] == left[pos]]
        filtered_peers = [catalog[i]["tag_id"] for j, i in enumerate(common)
                          if j != pos and right[j] == right[pos]]
        changed = base_peers != filtered_peers
        changed_tags += changed
        rows.append([
            threshold, catalog[tag_idx]["tag_id"], catalog[tag_idx]["tag"],
            f"C{left[pos]:03d}", f"C{right[pos]:03d}", ";".join(base_peers),
            ";".join(filtered_peers), int(changed),
        ])
    return {
        "common_tags": len(common),
        "tags_losing_all_evidence": [
            catalog[i]["tag_id"] for i in sorted(set(base_index) - set(filtered_index))
        ],
        "adjusted_rand_index": float(adjusted_rand_score(left, right)),
        "changed_cocluster_pairs": int(changed_pairs), "changed_tags": int(changed_tags),
    }, rows


def export_pairs(model, problems, evidence, output):
    vectors = model["X"]
    pairs = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            common = np.flatnonzero(vectors[i] & vectors[j])
            union = int((vectors[i] | vectors[j]).sum())
            ni, nj = int(vectors[i].sum()), int(vectors[j].sum())
            low = min(ni, nj) < 3
            source_i, source_j = int(model["indices"][i]), int(model["indices"][j])
            uncertain = sum(
                evidence[(source_i, int(p))]["needs_review"] == "1"
                or evidence[(source_j, int(p))]["needs_review"] == "1"
                for p in common
            )
            pairs.append({
                "tag_id_a": model["tags"][i]["tag_id"],
                "tag_a": model["tags"][i]["tag"],
                "tag_id_b": model["tags"][j]["tag_id"],
                "tag_b": model["tags"][j]["tag"],
                "count_a": ni, "count_b": nj, "shared_problem_count": len(common),
                "union_problem_count": union, "jaccard_similarity": len(common) / union,
                "jaccard_distance": float(model["D"][i, j]),
                "shared_fraction_of_a": len(common) / ni,
                "shared_fraction_of_b": len(common) / nj,
                "low_support": int(low),
                "shared_problems_with_review_pair": uncertain,
                "shared_problem_ids": ";".join(problems[int(p)] for p in common),
            })
    pairs.sort(key=lambda r: (-r["jaccard_similarity"], -r["shared_problem_count"],
                             r["tag_id_a"], r["tag_id_b"]))
    write_csv(output / "tag_pairs.csv", list(pairs[0]), [list(row.values()) for row in pairs])
    ids = [tag["tag_id"] for tag in model["tags"]]
    for filename, values in [
        ("tag_distance.csv", model["D"]), ("tag_similarity.csv", 1 - model["D"])
    ]:
        write_csv(output / filename, ["tag_id"] + ids,
                  [[ids[i]] + values[i].tolist() for i in range(len(ids))])
    return pairs


def write_html(models, output, threshold, summary):
    data_models = []
    for model in models:
        svg = (output / f'dendrogram_{model["key"]}.svg').read_bytes()
        data_models.append({
            "key": model["key"], "title": model["title"],
            "tags": [{"id": tag["tag_id"], "name": tag["tag"],
                      "count": int(model["X"][i].sum())}
                     for i, tag in enumerate(model["tags"])],
            "tree": model["Z"].tolist(), "leaf_order": model["leaf_order"],
            "metrics": model["metrics"],
            "svg": "data:image/svg+xml;base64," + base64.b64encode(svg).decode("ascii"),
        })
    data = {"threshold": threshold, "models": data_models, "summary": summary}
    # Prevent accidental script termination if a future tag contains HTML.
    serialized = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    template = (ROOT / "clustering_report_template.html").read_text(encoding="utf-8")
    (output / "report.html").write_text(
        template.replace("__CLUSTERING_DATA__", serialized), encoding="utf-8"
    )


def md_table(headers, rows):
    def escape(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join(
        ["| " + " | ".join(headers) + " |",
         "| " + " | ".join("---" for _ in headers) + " |"]
        + ["| " + " | ".join(escape(v) for v in row) + " |" for row in rows]
    )


def write_report(models, pairs, summary, output, threshold):
    full, frequent, filtered = models
    n_problems, n_taxonomy = summary["problem_count"], summary["taxonomy_count"]
    n_full, n_frequent = len(full["tags"]), len(frequent["tags"])
    n_unused, n_rare = summary["unused_tags"], summary["tags_with_1_or_2_problems"]
    bfs_dfs = next(p for p in pairs if {p["tag_id_a"], p["tag_id_b"]} == {"T066", "T067"})
    example = (f'幅優先探索と深さ優先探索の該当問題数はそれぞれ{bfs_dfs["count_a"]}問・'
               f'{bfs_dfs["count_b"]}問、共通問題は{bfs_dfs["shared_problem_count"]}問で、'
               f'類似度は{bfs_dfs["jaccard_similarity"]:.4f}です。')
    sim_rows = [
        [p["tag_a"], p["tag_b"], f'{p["jaccard_similarity"]:.3f}',
         p["shared_problem_count"], f'{p["count_a"]} / {p["count_b"]}',
         "1–2問のみ" if p["low_support"] else "3問以上"]
        for p in pairs[:12]
    ]
    group_rows = []
    for group in groups_for(frequent):
        if group["size"] < 2:
            continue
        members = [
            f'{frequent["tags"][i]["tag"]}（{int(frequent["X"][i].sum())}問）'
            for i in group["members"]
        ]
        group_rows.append([group["cluster_id"], "、".join(members),
                           f'{group["mean_pair_jaccard"]:.3f}'])
    cut_rows = []
    for model in models:
        for t in [.7, .8, .85, .9, .95, .975, .99]:
            metric = cut_stats(model, t)
            value = metric["silhouette"]
            cut_rows.append([model["title"], t, metric["cluster_count"],
                             metric["multi_tag_clusters"], metric["singleton_clusters"],
                             "定義不可" if value is None else f"{value:.4f}"])
    cut_table = md_table(
        ["対象", "距離閾値", "クラスタ数", "複数タグのクラスタ", "単独タグ", "シルエット"],
        cut_rows,
    )
    best = frequent["best_silhouette_cut"]
    best_text = (
        f'観測した結合高さと比較用の閾値で最大だったシルエットは'
        f'{best["silhouette"]:.4f}（距離閾値{best["threshold"]:.6f}、'
        f'{best["cluster_count"]}クラスタ）です。'
        if best else ""
    )
    sensitivity = summary["review_sensitivity"]
    fence = chr(96) * 3
    report = f"""# アルゴリズムの階層クラスタリング

対象は{n_problems}問に対する{n_taxonomy}タグの0/1行列です。入力は「{summary["dataset_label"]}」（{summary["input_directory"]}、{summary["assigned_pairs"]}付与組）です。問題方向を特徴として転置し、タグをクラスタリングしました。使用されている{n_full}タグを全体版、該当問題が3問以上の{n_frequent}タグを少数例の影響を減らす補助版としています。未使用の{n_unused}タグは分類する材料がなく、excluded_tags.csvに記録しました。

修正案には未点検の付与も含まれます。全問の意味的な正しさを検証済みという意味ではありません。初期表示は使用済みの全タグです。

## 結果の確認

[操作できるレポート](report.html)をブラウザーで開くと、対象と距離の閾値を変えてクラスタ一覧を確認できます。インターネット接続は不要です。図とCSVは以下にあります。

- [全{n_full}タグのデンドログラム](dendrogram_all.svg) / [PNG](dendrogram_all.png) / [クラスタ一覧](clusters_all.csv)
- [3問以上の{n_frequent}タグのデンドログラム](dendrogram_min3.svg) / [PNG](dendrogram_min3.png) / [クラスタ一覧](clusters_min3.csv)
- [要確認の付与を除いたデンドログラム](dendrogram_review_excluded.svg) / [クラスタ一覧](clusters_review_excluded.csv)
- [全タグ対の関連度と共通問題](tag_pairs.csv)、[類似度行列](tag_similarity.csv)、[距離行列](tag_distance.csv)
- [閾値別の評価](cut_metrics.csv)、[要確認の付与を除いたときの変化](review_sensitivity.csv)、[集計JSON](summary.json)

初期表示の距離閾値は{threshold:g}です。全{n_full}タグでは{full["stats"]["cluster_count"]}クラスタ（複数タグのグループ{full["stats"]["multi_tag_clusters"]}、単独タグ{full["stats"]["singleton_clusters"]}）、3問以上の{n_frequent}タグでは{frequent["stats"]["cluster_count"]}クラスタ（複数タグのグループ{frequent["stats"]["multi_tag_clusters"]}、単独タグ{frequent["stats"]["singleton_clusters"]}）になりました。これは探索用の例で、最適なクラスタ数や正式な分類体系を決めたものではありません。

## 距離と階層の作り方

タグAに付いた問題集合をP(A)として、類似度は共通問題数を和集合の問題数で割ります。

{fence}text
Jaccard similarity(A, B) = |P(A) ∩ P(B)| / |P(A) ∪ P(B)|
distance(A, B) = 1 - similarity(A, B)
{fence}

例えば{example}両方とも付いていない問題は類似度に寄与しません。[SciPyのJaccard距離の定義](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.jaccard.html)に基づきます。

クラスタ間の距離には、その2クラスタに属する全タグ対の距離の平均を使います。SciPyのaverage linkage（UPGMA）を使いました。Jaccard距離でWard法は使用していません。[連結法の定義](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html)

デンドログラムの横軸は結合した時点の距離です。左側で結合するほど問題集合が近くなります。平均連結なので、同じクラスタに入った全タグ対の距離が閾値以下とは限りません。距離1付近での結合は、共通問題がほとんどないグループ間の結合です。左右・上下の表示順やクラスタ番号自体に意味はありません。同じ距離の結合順は実装・入力順に依存する場合があります。

## 3問以上のタグで得られたグループ

距離閾値{threshold:g}で、2タグ以上になったグループを掲載します。単独タグもCSVと操作レポートに残しています。件数は各タグの該当問題数で、平均類似度はクラスタ内の全タグ対のJaccard類似度の平均です。

{md_table(["クラスタ", "タグ（該当問題数）", "平均類似度"], group_rows)}

## 関連度の高いタグ対

{md_table(["タグA", "タグB", "類似度", "共通問題数", "各タグの問題数", "例数"], sim_rows)}

Grundy数とNimの類似度1は、このデータで同じ2問に付いたことを意味します。アルゴリズムが同じであるという証明ではありません。全体版の{n_rare}タグは1〜2問しか例がなく、高い類似度でも判断材料が少ないことに注意して解釈します。tag_pairs.csvの共通問題IDから元の問題・解説を確認できます。

## 分割の評価

{cut_table}

3問以上のタグで初期閾値{threshold:g}のシルエットは{frequent["stats"]["silhouette"] if frequent["stats"]["silhouette"] is not None else "定義不可"}です。{best_text}この値は低く、現在の0/1タグ付けでは明確なクラスタ境界が弱いと読み取れます。シルエットだけでクラスタ数を確定せず、結合高さ・問題例・グループの解釈を合わせて検討してください。単独タグのシルエットは0として平均しています。[シルエットの定義](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html)

デンドログラムが元のタグ間距離をどの程度保っているかを表すcophenetic correlationは全体版{full["cophenetic_correlation"]:.4f}、3問以上版{frequent["cophenetic_correlation"]:.4f}でした。これは階層への距離の保存度で、クラスタの意味や正しさを保証する指標ではありません。[SciPyの定義](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.cophenet.html)

## 要確認の付与を除いた場合

all_problems_tagged.csvのneeds_review=1である{summary["review_pairs_removed"]}組だけを除き、距離と階層を作り直しました。needs_review=0もすべて検証済みという意味ではありません。除外後は{len(filtered["tags"])}タグに問題例が残ります。この比較用入力では{summary["problems_losing_all_tags_after_review_exclusion"]}問のタグが0件になり、Jaccard距離への寄与もなくなります。例がなくなったタグはexcluded_tags.csvに別の理由として記録しました。

同じ距離閾値{threshold:g}で共通の{sensitivity["common_tags"]}タグを比較すると、同じクラスタになるタグ対の関係が{sensitivity["changed_cocluster_pairs"]}組変わり、{sensitivity["changed_tags"]}タグの同クラスタの相手が変わりました。Adjusted Rand Indexは{sensitivity["adjusted_rand_index"]:.4f}です。クラスタ番号は対象ごとに振り直すため、番号の一致・不一致を直接比較していません。

## この結果で分かることと次の改善

今回の関連スコアは「付与された問題集合の重なり」です。FBにある「その問題に対してアルゴリズムを選んだ場合の最適度」は測定していません。行列の0は未付与であり、適用できないという判定ではありません。

同じ問題に登場する補助データ構造と主アルゴリズム、または別解が近くなるため、Dijkstra法とHeapのような組合せもまとまります。同義語を自動で統合する根拠としては使えません。一方、タグ付け時に基礎DPを個別DPへ置き換えるなど、広いタグと細かいタグを併記していない場合があります。概念上の親子関係でも共起がなく、離れることがあります。問題集合は元CSVの範囲に限られ、未使用タグの関連性は評価できません。

分類体系を整える次の作業としては、共通問題を確認し、主解・別解・補助の役割を区別して関連スコアを付けること、未使用タグに代表問題を追加すること、タグの親子関係を別途記録することが有効です。現在の階層はその検討に使える初期結果として保存しました。

## 再実行

作業フォルダーで以下を実行します。Python 3.9以上を想定し、今回の実行環境はPython {sys.version.split()[0]}です。

{fence}powershell
py -m venv .venv-clustering
.\\.venv-clustering\\Scripts\\python.exe -m pip install -r requirements-clustering.txt
.\\.venv-clustering\\Scripts\\python.exe hierarchical_clustering.py
.\\.venv-clustering\\Scripts\\python.exe hierarchical_clustering.py --input-dir {summary["input_directory"]} --threshold 0.85 --output clustering_085
{fence}

既定の入力先はvalidation/revisedです。検証前のデータを使う場合は --input-dir . を指定します。

閾値の変更は出力先を指定しなければ同じclusteringフォルダーを更新します。デンドログラム・クラスタCSV・レポートはその閾値で再生成されます。操作レポートのスライダーはクラスタ一覧・統計を切り替えます。埋め込みの図は生成時の閾値のままであることを表示しています。

linkage CSVの葉ノードはleaves CSVの0始まりのID、結合ノードはタグ数+merge_indexです。左右ノード・結合距離・葉数を保存しており、別のツールでも階層を再構成できます。使用パッケージの版と入力ファイルのSHA-256はsummary.jsonに記録しました。

## 検証

{n_problems}問題IDの一致、{n_taxonomy}タグとカタログ件数の一致、0/1入力、{summary["assigned_pairs"]}付与組との完全一致、タグ対距離の全件再計算、距離の対称性・範囲、階層の妥当性・結合高さの単調性を実行時に検証しました。小さな既知の行列でJaccard距離、平均連結の高さ、距離による分割を独立に検証しています。これらは計算・データの整合性の検証で、元のタグ付けの正しさを証明するものではありません。

生成処理ではタグ対距離と入力の整合性を毎回検証します。HTMLの分割計算は別途SciPyとの照合対象とし、画面操作や画像の目視確認の状況は生成時の検証記録に残します。
"""
    (output / "clustering_report.md").write_text(report, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=.9,
                        help="Exploratory distance cut in [0, 1], default 0.9")
    parser.add_argument("--output", default="clustering", help="Output folder")
    parser.add_argument("--input-dir", default="validation/revised",
                        help="Folder containing tagged CSV, matrix and catalog; use . for the baseline")
    args = parser.parse_args()
    if not np.isfinite(args.threshold) or not 0 <= args.threshold <= 1:
        parser.error("--threshold must be finite and in [0, 1]")
    output = (ROOT / args.output).resolve()
    # Never overwrite the input directory or its parents.
    if output == ROOT or output in ROOT.parents:
        parser.error("--output must be a separate output folder")
    output.mkdir(parents=True, exist_ok=True)
    self_check()
    input_dir = (ROOT / args.input_dir).resolve()
    matrix, problems, catalog, review_mask, evidence = load_inputs(input_dir)
    filtered_matrix = matrix & ~review_mask
    models = [
        build_model("all", "All used tags", matrix, catalog, 1, args.threshold),
        build_model("min3", "Tags with at least 3 problems", matrix, catalog, 3, args.threshold),
        build_model("review_excluded", "Review-flagged assignments excluded",
                    filtered_matrix, catalog, 1, args.threshold),
    ]
    font_family = configure_fonts()
    for model in models:
        export_model(model, output, args.threshold, review_mask)
        save_dendrogram(model, output, args.threshold)
    pairs = export_pairs(models[0], problems, evidence, output)
    excluded = []
    for model in models:
        counts = (filtered_matrix if model["key"] == "review_excluded" else matrix).sum(axis=1)
        for i in range(len(catalog)):
            if counts[i] < model["min_support"]:
                reason = (
                    "no_assigned_problems" if matrix[i].sum() == 0 else
                    "no_evidence_after_review_exclusion" if counts[i] == 0 else
                    "fewer_than_3_problems"
                )
                excluded.append([model["key"], catalog[i]["tag_id"], catalog[i]["tag"],
                                 int(matrix[i].sum()), int(counts[i]), reason])
    write_csv(output / "excluded_tags.csv",
              ["model", "tag_id", "tag", "original_problem_count",
               "problem_count_in_model", "reason"], excluded)
    metric_columns = [
        "model", "threshold", "tag_count", "cluster_count", "multi_tag_clusters",
        "singleton_clusters", "silhouette",
    ]
    write_csv(output / "cut_metrics.csv", metric_columns, [
        [model["key"]] + [row[name] for name in metric_columns[1:]]
        for model in models for row in model["metrics"]
    ])
    sensitivity, change_rows = review_sensitivity(
        models[0], models[2], catalog, args.threshold
    )
    write_csv(output / "review_sensitivity.csv", [
        "distance_threshold", "tag_id", "tag", "cluster_all", "cluster_review_excluded",
        "other_tags_all", "other_tags_review_excluded", "peer_set_changed",
    ], change_rows)
    source_paths = {name: (input_dir if name in {
        "problem_tag_matrix.csv", "all_problems_tagged.csv", "tag_catalog.csv"
    } else ROOT) / name for name in SOURCE_NAMES}
    input_rows = csv_rows(input_dir / "all_problems_tagged.csv")
    summary = {
        "dataset_label": "検証後のタグ付け修正案" if any(
            "validation_status" in r for r in input_rows) else "検証前のタグ付け",
        "input_directory": str(input_dir.relative_to(ROOT)) if ROOT == input_dir or ROOT in input_dir.parents else str(input_dir),
        "validation_status_counts": dict(Counter(r.get("validation_status", "not_recorded") for r in input_rows)),
        "problem_count": len(problems), "taxonomy_count": len(catalog),
        "assigned_pairs": int(matrix.sum()), "used_tags": int(matrix.any(axis=1).sum()),
        "unused_tags": int((~matrix.any(axis=1)).sum()),
        "tags_with_1_or_2_problems": int(((matrix.sum(axis=1) > 0)
                                         & (matrix.sum(axis=1) < 3)).sum()),
        "review_pairs_removed": int(review_mask.sum()),
        "problems_losing_all_tags_after_review_exclusion":
            int((~filtered_matrix.any(axis=0)).sum()),
        "distance": "Jaccard", "linkage": "average (UPGMA)", "optimal_leaf_ordering": True,
        "default_distance_threshold": args.threshold,
        "review_sensitivity": sensitivity,
        "models": [{
            "key": m["key"], "min_support": m["min_support"], **m["stats"],
            "cophenetic_correlation": m["cophenetic_correlation"],
            "best_silhouette_cut_observed": m["best_silhouette_cut"],
        } for m in models],
        "runtime": {
            "python": sys.version.split()[0], "numpy": np.__version__,
            "scipy": scipy.__version__, "matplotlib": matplotlib.__version__,
            "scikit_learn": sklearn.__version__, "plot_font": font_family,
        },
        "source_sha256": {
            name: hashlib.sha256(source_paths[name].read_bytes()).hexdigest()
            for name in SOURCE_NAMES
        },
        "validation": "all checks passed",
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(models, pairs, summary, output, args.threshold)
    write_html(models, output, args.threshold, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
