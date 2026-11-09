"""Prepare reviewable application changes without overwriting any application files."""
import hashlib,json
from pathlib import Path
from build_dataset import ROOT,APP,load,save,sha

def replace_once(s,old,new):
    assert s.count(old)==1,repr(old[:120])
    return s.replace(old,new,1)
def stage():
    out=ROOT/"output";staged=ROOT/"staged_app";backup=ROOT/"app_backup"
    assert not (ROOT/"applied.json").exists(),"Already applied; review current changes before restaging."
    plans={
        "public/all_problems.csv":(out/"all_problems.csv").read_bytes(),
        "src/data/tagCatalog.json":(out/"tagCatalog.json").read_bytes(),
        "src/data/problemTopics.json":(out/"problemTopics.json").read_bytes(),
    }
    main=(APP/"src/components/Main.jsx").read_text(encoding="utf-8")
    main=replace_once(main,'import tagCatalog from "../data/tagCatalog.json";',
        'import tagCatalog from "../data/tagCatalog.json";\nimport problemTopics from "../data/problemTopics.json";')
    main=replace_once(main,'{tagCatalog.source_problem_count}問（距離閾値 {tagCatalog.distance_threshold}、\n              {MIN_PROBLEMS_PER_TAG}問以上）',
        '{tagCatalog.source_problem_count}問（学習単位・{MIN_PROBLEMS_PER_TAG}問以上）')
    main=replace_once(main,'clustersByLabel.get(selectedAlgoName)?.member_tags.map((tag) => tag.tag) ?? []',
        'clustersByLabel.get(selectedAlgoName)?.detail_methods ?? []')
    main=replace_once(main,'          <AlgorithmCard\n            algo={selectedAlgo}',
        '          <AlgorithmCard\n            definition={clustersByLabel.get(selectedAlgoName)?.description}\n            problemTopics={problemTopics}\n            algo={selectedAlgo}')
    plans["src/components/Main.jsx"]=main.encode("utf-8")
    card=(APP/"src/components/AlgorithmCard.jsx").read_text(encoding="utf-8")
    card=replace_once(card,'export default function AlgorithmCard({ algo, problems, submissionsMap, memberTags = [] }) {',
        '''export default function AlgorithmCard({
  algo,
  problems,
  submissionsMap,
  memberTags = [],
  definition,
  problemTopics = {},
}) {''')
    card=replace_once(card,'          {memberTags.length > 1 && (',
        '          {definition && <p className="selected-algo-members">{definition}</p>}\n          {memberTags.length > 0 && (memberTags.length > 1 || memberTags[0] !== algo.algo) && (')
    card=replace_once(card,'                {problem.title}\n              </span>',
        '''                {problem.title}
                {problemTopics[problem.problem_id]?.length > 0 && (
                  <span className="problem-topic-label">
                    題材：{problemTopics[problem.problem_id].join("、")}
                  </span>
                )}
              </span>''')
    plans["src/components/AlgorithmCard.jsx"]=card.encode("utf-8")
    style=(APP/"style.css").read_text(encoding="utf-8")
    style += '''
.problem-topic-label {
  display: block;
  margin-top: 3px;
  font-size: 0.75rem;
  line-height: 1.5;
  opacity: 0.75;
}
'''
    plans["style.css"]=style.encode("utf-8")
    stats=load(out/"summary.json")
    docs=f"""# 学習単位によるタグ分類

既存の898問・115種類の細かいタグを、意味に基づく{stats['learning_units']}の学習単位に整理しました。
2問以上の分類を表示するため、実際の円グラフは{stats['visible_units']}個です。
問題の難易度・ID・URLは保持しています。全ABC問題の自動付与データには入れ替えていません。

表示の単位は「独立して説明・練習できる具体的な計算課題または技法の系統」です。
同じ学習時間や難易度を保証するものではありません。
同じ問題に付くという理由だけで別の技法を統合することはしていません。

- 点更新・区間集約：Fenwick木、Segment Tree。区間更新と静的クエリは別分類。
- 最小全域木：Kruskal法、Prim法。具体的な手法名は選択時に確認できます。
- 重心分解は畳み込み・FFTから分離しました。
- 接尾辞配列、Zアルゴリズム、ローリングハッシュを分離しました。
- 二部マッチングと最大流、2-SATと二部グラフ判定も別分類です。
- 括弧列やMEXは問題の題材として、該当する問題一覧に表示します。
- 一般DPなどの上位分類は、専門的な状態型が既知の問題で二重に表示しません。
- 既存レビューの参考・根拠不足・分析用・曖昧な対応は表示の根拠から保留します。

src/data/tagCatalog.json の classification_method は semantic_learning_units、
version は {stats['version']} です。
clusters という配列名は既存UIとの互換性のために保持しています。
階層クラスタリングの距離・連結法・cutによる分類ではありません。
problemTopics.json は問題IDに対応する題材の一覧です。

public/all_problems.csv は従来と同じ6列・1問題–1分類につき1行です。
同じ問題・同じ分類の重複はありません。1問以下の分類もCSVとカタログには保持します。
分類名変更により旧版の同レート帯集計は使えません。
peer-baselines.json の版が一致するまで、既存の互換性判定により比較リングを表示しません。
本人のAC・WA・未挑戦は従来どおり問題IDで集計します。

これはAIによる分類の整理案です。問題への付与には未レビューが多く残り、
主解・別解・補助の全件確認や独立した人手評価は未実施です。
同一分類の全技法を各問題が使う意味ではなく、その分類の習得もACだけからは判定できません。
"""
    plans["docs/SEMANTIC_TAGS.md"]=docs.encode("utf-8")
    olddoc=(APP/"docs/CLUSTER_TAGS.md").read_text(encoding="utf-8")
    plans["docs/CLUSTER_TAGS.md"]=("この文書は旧・階層クラスタリング版の記録です。現行の分類は [学習単位版](SEMANTIC_TAGS.md) を参照してください。\n\n---\n\n"+olddoc).encode("utf-8")
    manifest={}
    for rel,data in plans.items():
        target=(APP/rel).resolve()
        assert APP.resolve() in target.parents
        saved=backup/rel
        saved.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            assert not saved.exists(),"Do not overwrite an existing backup."
            saved.write_bytes(target.read_bytes())
            oldsha=sha(target)
        else:oldsha=None
        dest=staged/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        manifest[rel]=dict(before_sha256=oldsha,staged_sha256=sha(dest))
    save(ROOT/"change_manifest.json",manifest)
    print(json.dumps(dict(staged_files=list(plans),backup=str(backup)),ensure_ascii=True))
if __name__=="__main__":stage()
