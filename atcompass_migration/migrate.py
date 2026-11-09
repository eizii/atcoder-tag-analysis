# -*- coding: utf-8 -*-
"""Install the frozen cluster dataset in AtCompass; preserve the original CSV schema."""
import csv,hashlib,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent.parent
APP=Path("C:/Users/ejham/theme2026-kaziru")
BACKUP=Path(__file__).resolve().parent/"before"
DATA=ROOT/"clustering/all_problems_clustered.csv"
CATALOG=ROOT/"clustering/cluster_catalog.json"
BASELINE_HASH="ef84cd9cdfe70f0238962c62514eec15b9d91d81ba549141f323f1a9ada31751"

def csv_rows(data):
    import io
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))

def replace_once(text,old,new):
    if text.count(old)!=1:
        raise RuntimeError("Expected exactly one edit anchor: "+old[:100])
    return text.replace(old,new,1)

def main():
    old_csv=(APP/"public/all_problems.csv").read_bytes()
    assert hashlib.sha256(old_csv).hexdigest()==BASELINE_HASH,"App CSV changed; inspect before replacing"
    source=DATA.read_bytes()
    original=csv_rows(old_csv)
    rows=csv_rows(source)
    catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
    labels={c["label"] for c in catalog["clusters"]}
    assert len(rows)==1472 and len(labels)==72
    assert {r["problem_id"] for r in original}=={r["problem_id"] for r in rows}
    assert len({r["problem_id"] for r in rows})==898
    assert {r["tag"] for r in rows}==labels
    assert len({(r["tag"],r["problem_id"]) for r in rows})==len(rows)
    old_meta={r["problem_id"]:{k:v for k,v in r.items() if k!="tag"} for r in original}
    assert all({k:v for k,v in r.items() if k!="tag"}==old_meta[r["problem_id"]] for r in rows)
    assert all(0<=float(r["difficulty"])<2000 for r in rows)
    assert [c["label"] for c in catalog["clusters"] if "シミュレーション" in c["label"]]==["C047: シミュレーション"]
    plans={"public/all_problems.csv":source}
    catalog.update(problemCatalog="public/all_problems.csv",
                   problemCatalogSha256=hashlib.sha256(source).hexdigest())
    plans["src/data/tagCatalog.json"]=(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n").encode("utf-8")

    app=(APP/"src/App.jsx").read_text(encoding="utf-8")
    app=replace_once(app,'import { loadPeerBaselines } from "./utils/peerBaselines";',
        'import { loadPeerBaselines } from "./utils/peerBaselines";\nimport tagCatalog from "./data/tagCatalog.json";')
    app=replace_once(app,"loadPeerBaselines(controller.signal)",
                        "loadPeerBaselines(controller.signal, tagCatalog.version)")
    plans["src/App.jsx"]=app.encode("utf-8")

    peers=(APP/"src/utils/peerBaselines.js").read_text(encoding="utf-8")
    peers=replace_once(peers,"export async function loadPeerBaselines(signal) {",
         "export async function loadPeerBaselines(signal, expectedTaggingVersion) {")
    peers=replace_once(peers,"  return data;","""  return {
    ...data,
    catalogCompatible:
      expectedTaggingVersion == null || data.source?.taggingVersion === expectedTaggingVersion,
  };""")
    peers=replace_once(peers,'  if (!peerBaselines?.bands || !Number.isFinite(numericRate) || numericRate < 0) {',
        """  if (
    !peerBaselines?.bands ||
    peerBaselines.catalogCompatible === false ||
    !Number.isFinite(numericRate) ||
    numericRate < 0
  ) {""")
    plans["src/utils/peerBaselines.js"]=peers.encode("utf-8")

    main=(APP/"src/components/Main.jsx").read_text(encoding="utf-8")
    main=replace_once(main,'import { createPeerProgressMap, getPeerRatingBand } from "../utils/peerBaselines";',
        'import { createPeerProgressMap, getPeerRatingBand } from "../utils/peerBaselines";\nimport tagCatalog from "../data/tagCatalog.json";\n\nconst clustersByLabel = new Map(tagCatalog.clusters.map((cluster) => [cluster.label, cluster]));')
    main=replace_once(main,'  const peerStatisticLabel = peerStatistic === "median" ? "中央値" : "平均";',
        '  const peerDataUnavailable = peerBaselines?.catalogCompatible === false;\n  const peerStatisticLabel = peerStatistic === "median" ? "中央値" : "平均";')
    main=replace_once(main,"                      checked={showPeerProgressRing}",
        "                      checked={showPeerProgressRing && !peerDataUnavailable}\n                      disabled={peerDataUnavailable}")
    main=replace_once(main,"                    <span>同レート帯リング</span>",
        '                    <span>同レート帯リング{peerDataUnavailable ? "（準備中）" : ""}</span>')
    main=replace_once(main,'                    showPeerProgressRing ? "" : " peer-statistic-control--disabled"',
        '                    showPeerProgressRing && !peerDataUnavailable ? "" : " peer-statistic-control--disabled"')
    assert main.count("disabled={!showPeerProgressRing}")==2
    main=main.replace("disabled={!showPeerProgressRing}","disabled={!showPeerProgressRing || peerDataUnavailable}")
    main=replace_once(main,"          {showPlacementSettings && (","""          {peerDataUnavailable && (
            <p className="peer-data-note" role="status">
              現在の分類に対応する同レート帯データは準備中です。
            </p>
          )}

          {showPlacementSettings && (""")
    main=replace_once(main,'            <h1 className="chart-title">アルゴリズム分布図</h1>',
        '            <h1 className="chart-title">アルゴリズム分布図</h1>\n            <p className="chart-dataset-note">{tagCatalog.clusters.length}分類・{tagCatalog.source_problem_count}問</p>')
    main=replace_once(main,"          <AlgorithmCard algo={selectedAlgo} problems={problems} submissionsMap={submissionsMap} />",
        """          <AlgorithmCard
            algo={selectedAlgo}
            problems={problems}
            submissionsMap={submissionsMap}
            memberTags={clustersByLabel.get(selectedAlgoName)?.member_tags.map((tag) => tag.tag) ?? []}
          />""")
    plans["src/components/Main.jsx"]=main.encode("utf-8")

    card=(APP/"src/components/AlgorithmCard.jsx").read_text(encoding="utf-8")
    card=replace_once(card,"export default function AlgorithmCard({ algo, problems, submissionsMap }) {",
         "export default function AlgorithmCard({ algo, problems, submissionsMap, memberTags = [] }) {")
    card=replace_once(card,'            <div className="selected-algo-name">{algo.algo}</div>',
        """            <div className="selected-algo-name">{algo.algo}</div>""")
    card=replace_once(card,'          <div className="selected-algo-stats">\n            <div className="stat-row">',
        """          {memberTags.length > 1 && (
            <p className="selected-algo-members">含まれる手法：{memberTags.join("、")}</p>
          )}
          <div className="selected-algo-stats">
            <div className="stat-row">""")
    plans["src/components/AlgorithmCard.jsx"]=card.encode("utf-8")
    style=(APP/"style.css").read_text(encoding="utf-8")
    style += """
.chart-dataset-note,
.peer-data-note,
.selected-algo-members {
  font-size: 0.875rem;
  line-height: 1.6;
  opacity: 0.8;
}

.chart-dataset-note {
  margin: 4px 0 0;
}

.peer-data-note,
.selected-algo-members {
  margin: 8px 0;
}
"""
    plans["style.css"]=style.encode("utf-8")
    docs="""# 72クラスタ版のタグデータ

public/all_problems.csv は、898問の修正案・115種類の細かいタグを、
Jaccard距離・平均連結法・距離閾値0.9で72群にまとめたデータです。
同じ問題に同じクラスタが重複して付かないようにし、1,472組の行を収録しています。
列名・問題ID・タイトル・難易度・URLは元のCSVと同じです。難易度を再補正していません。

表示名は C047: シミュレーション のようにクラスタIDと代表名です。
英語表記 simulation を独立のタグとして残していません。
src/data/tagCatalog.json に、各群を構成する細かい手法とバージョンを記録しています。
主解法・別解・補助データ構造の共通問題に基づくグループであり、同義語だけを統合したものではありません。
元の細かいタグには未点検のものも含まれます。

同レート帯リングの public/peer-baselines.json は旧分類の集計です。
重複する問題を含む旧タグの集計値を足しても、新クラスタの平均・中央値にはなりません。
そのため、source.taggingVersion が現行 tagCatalog.version と一致しない場合は比較リングを表示しません。
新しい問題集合に対して、各参加者の問題単位の提出・AC記録から重複なく再集計する必要があります。
再集計後に同じバージョンをsource.taggingVersionへ設定します。
古い集計値に新しいバージョンを付けるだけでは移行できません。
本人のAC・WA・未挑戦リングは問題IDで集計するため、引き続き利用できます。
"""
    plans["docs/CLUSTER_TAGS.md"]=docs.encode("utf-8")
    for rel in plans:
        target=APP/rel
        assert APP.resolve() in target.resolve().parents
        if target.exists():
            backup=BACKUP/rel
            backup.parent.mkdir(parents=True,exist_ok=True)
            assert not backup.exists(),"Refusing to overwrite a pre-migration backup"
    for rel,content in plans.items():
        target=APP/rel
        if target.exists():
            (BACKUP/rel).write_bytes(target.read_bytes())
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    result=dict(before_rows=len(original),before_tag_count=len({r["tag"] for r in original}),
        after_rows=len(rows),after_tag_count=len(labels),problem_count=898,
        simulation_count=sum(r["tag"]=="C047: シミュレーション" for r in rows),
        changed_files=list(plans),catalog_version=catalog["version"])
    (Path(__file__).resolve().parent/"migration_summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
