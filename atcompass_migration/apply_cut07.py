# -*- coding: utf-8 -*-
import csv,hashlib,io,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
APP=Path("C:/Users/ejham/theme2026-kaziru")
SOURCE=ROOT/"clustering_07"
BACKUP=Path(__file__).resolve().parent/"before_cut07"
def digest(data): return hashlib.sha256(data).hexdigest()
def parse(data): return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
def main():
    current=(APP/"public/all_problems.csv").read_bytes()
    old_catalog=json.loads((APP/"src/data/tagCatalog.json").read_text(encoding="utf-8"))
    assert old_catalog["version"]=="hc72-jaccard-average-d0.9-v1"
    assert digest(current)==old_catalog["problemCatalogSha256"],"Live dataset changed"
    target=(SOURCE/"all_problems_clustered.csv").read_bytes()
    catalog=json.loads((SOURCE/"cluster_catalog.json").read_text(encoding="utf-8"))
    assert catalog["distance_threshold"]==0.7 and len(catalog["clusters"])==101
    assert digest(target)==catalog["problemCatalogSha256"]
    previous,rows=parse(current),parse(target)
    old_meta={r["problem_id"]:{k:v for k,v in r.items() if k!="tag"} for r in previous}
    new_meta={r["problem_id"]:{k:v for k,v in r.items() if k!="tag"} for r in rows}
    assert old_meta==new_meta and len(new_meta)==898
    assert len(rows)==1720 and len({(r["tag"],r["problem_id"]) for r in rows})==len(rows)
    assert {r["tag"] for r in rows}=={c["label"] for c in catalog["clusters"]}
    simulation=[c for c in catalog["clusters"] if "シミュレーション" in c["label"]]
    assert len(simulation)==1
    label=simulation[0]["label"]
    assert sum(r["tag"]==label for r in rows)==60
    plans={"public/all_problems.csv":target,
           "src/data/tagCatalog.json":(SOURCE/"cluster_catalog.json").read_bytes()}
    main_file=APP/"src/components/Main.jsx"
    code=main_file.read_text(encoding="utf-8")
    anchor='{tagCatalog.source_problem_count}問</p>'
    assert code.count(anchor)==1
    code=code.replace(anchor,'{tagCatalog.source_problem_count}問（距離閾値 {tagCatalog.distance_threshold}）</p>')
    plans["src/components/Main.jsx"]=code.encode("utf-8")
    docs=f"""# distance cut = 0.7 のクラスタ版タグデータ

public/all_problems.csv は、898問の修正案・115種類の細かいタグを、
Jaccard距離・平均連結法・距離閾値0.7で101群にまとめたデータです。
複数タグのグループは11群、単独タグは90群です。
同じ問題に同じクラスタを重複して付けず、1,720組を収録しています。
距離閾値0.9の72群より細かい分類です。閾値を小さくするほど結合する条件が厳しくなります。
列名・898個の問題ID・タイトル・難易度・URLは変更していません。難易度を再補正していません。

表示名は {label} のようにクラスタIDと代表名です。
simulationという独立した英語表記はなく、シミュレーションの60問はこの1分類です。
src/data/tagCatalog.json に所属する細かいタグ、閾値、版、入力ハッシュを記録しています。
現在の版は {catalog["version"]} です。
クラスタIDは今回の閾値に対して採番したもので、0.9版と同じIDでも所属手法が異なることがあります。
対応は表示名だけでなく、tagCatalog.jsonのmember_tagsのtag_idで確認してください。

所属は主解法・別解・補助データ構造の共通問題に基づきます。同義語だけの統合ではありません。
元の細かいタグには未点検のものも含まれます。

## 同レート帯リング

public/peer-baselines.json は旧分類の集計です。
旧タグの集計値を足しても、重複する問題や利用者ごとの分布を正しく復元できません。
source.taggingVersion が現行tagCatalog.versionと一致するまで比較リングを表示しません。
新しい各クラスタの問題集合に対して、各参加者の問題単位の提出・AC記録から重複なく再集計してください。
古い集計値の版だけを変更しても移行できません。
本人のAC・WA・未挑戦リングは問題IDで集計するため、引き続き利用できます。
"""
    plans["docs/CLUSTER_TAGS.md"]=docs.encode("utf-8")
    for rel in plans:
        dest=APP/rel
        assert APP.resolve() in dest.resolve().parents
        backup=BACKUP/rel
        assert not backup.exists(),"Refusing to replace an existing backup"
    for rel,value in plans.items():
        dest=APP/rel
        backup=BACKUP/rel
        backup.parent.mkdir(parents=True,exist_ok=True)
        backup.write_bytes(dest.read_bytes())
        dest.write_bytes(value)
    report=dict(before_cut=old_catalog["distance_threshold"],after_cut=0.7,
        before_clusters=len(old_catalog["clusters"]),after_clusters=101,
        problem_count=898,cluster_problem_pairs=len(rows),
        simulation_label=label,simulation_problems=60,version=catalog["version"],
        csv_sha256=digest(target),changed_files=list(plans))
    (Path(__file__).resolve().parent/"cut07_update_summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
