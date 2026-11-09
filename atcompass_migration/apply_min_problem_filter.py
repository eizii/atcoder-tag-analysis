# -*- coding: utf-8 -*-
from pathlib import Path
import json

APP=Path("C:/Users/ejham/theme2026-kaziru")
WORK=Path(__file__).resolve().parent
plans={}
stats=(APP/"src/utils/statistics.js").read_text(encoding="utf-8")
anchor="// 円の半径の最小値と最大値"
assert stats.count(anchor)==1
stats=stats.replace(anchor,"export const MIN_PROBLEMS_PER_TAG = 2;\n\n"+anchor,1)
anchor="  for (const [algo, values] of Object.entries(groups)) {\n    const sorted = [...values].sort((a, b) => a - b);"
assert stats.count(anchor)==1
stats=stats.replace(anchor,"""  for (const [algo, values] of Object.entries(groups)) {
    if (values.length < MIN_PROBLEMS_PER_TAG) {
      continue;
    }

    const sorted = [...values].sort((a, b) => a - b);""",1)
plans["src/utils/statistics.js"]=stats
main=(APP/"src/components/Main.jsx").read_text(encoding="utf-8")
anchor='import tagCatalog from "../data/tagCatalog.json";'
assert main.count(anchor)==1
main=main.replace(anchor,anchor+'\nimport { MIN_PROBLEMS_PER_TAG } from "../utils/statistics";',1)
anchor="""              {tagCatalog.clusters.length}分類・{tagCatalog.source_problem_count}問（距離閾値{" "}
              {tagCatalog.distance_threshold}）"""
assert main.count(anchor)==1
main=main.replace(anchor,"""              {summary.length} / {tagCatalog.clusters.length}分類を表示・
              {tagCatalog.source_problem_count}問（距離閾値 {tagCatalog.distance_threshold}、
              {MIN_PROBLEMS_PER_TAG}問以上）""",1)
plans["src/components/Main.jsx"]=main
doc=(APP/"docs/CLUSTER_TAGS.md").read_text(encoding="utf-8")
anchor="## 同レート帯リング"
assert doc.count(anchor)==1
doc=doc.replace(anchor,"""## 問題数による表示条件

AtCompassの分布図では、問題数が2問以上の分類だけを表示します。
問題とタグの重複を取り除いた後の件数を使い、0問・1問の分類は描画用集計と配置計算に含めません。
現在の0.7版では、1問だけの25分類を除いた76分類が表示されます。
CSVとtagCatalog.jsonには101分類すべてを保持し、問題のデータやタグの対応は削除していません。
画面には表示中の分類数・全分類数・最低問題数を併記します。

"""+anchor,1)
plans["docs/CLUSTER_TAGS.md"]=doc
backup=WORK/"before_min_problems"
for rel in plans:
    target=APP/rel
    assert APP.resolve() in target.resolve().parents
    assert not (backup/rel).exists(),"Existing backup"
for rel,text in plans.items():
    file=APP/rel
    saved=backup/rel
    saved.parent.mkdir(parents=True,exist_ok=True)
    saved.write_bytes(file.read_bytes())
    file.write_text(text,encoding="utf-8")
print(json.dumps({"minimum_problems":2,"expected_displayed_tags":76,"catalog_tags":101,"files":list(plans)},ensure_ascii=False))
