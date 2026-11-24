# -*- coding: utf-8 -*-
"""Readable results and an offline browser for the six V4 clustering models."""
import csv,json,html
from pathlib import Path
R=Path(__file__).resolve().parent;O=R/'hierarchical_v4_20261124'
M={'cosine':'コサイン','jaccard':'ジャカード'};L={'average':'平均連結法','single':'単連結法','complete':'完全連結法'};DS={'all_difficulties':'全難易度','under_2000':'2000未満'}
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
s=json.loads((O/'summary.json').read_text(encoding='utf-8'));matched=read(O/'matched_cluster_counts.csv')
text='''# V4：距離2種類 × 連結法3種類の階層クラスタリング

実行日：2026-11-24。修正版V4の二値タグ行列で、タグ同士の階層クラスタリングを実行しました。

**今回の条件では、単連結法は連鎖的な巨大クラスタができやすく、平均連結法と完全連結法は細かい群を保ちました。** コサイン＋平均連結法をまず内訳確認の候補にします。ただし、群数やシルエット係数だけで学習内容の妥当性は確定していません。

- [操作できる結果一覧](index.html)：対象・距離・連結法・cutを切り替え、クラスタ内のタグを検索できます。
- [群数の比較図](comparison.png) / [拡大用SVG](comparison.svg)
- [全252条件の数値](parameter_sweep.csv)：12条件 × cut 0.00〜1.00、0.05刻み
- [目標40/80群との比較](matched_cluster_counts.csv)：同じ距離のcutだけでなく、群数を近付けた結果

![クラスタ数の推移](comparison.png)

## 固定した条件

| 項目 | 全難易度 | 2000未満 |
| --- | ---: | ---: |
'''
for label,key in [('問題数','problems'),('タグ付き問題数','tagged_problems'),('タグなし問題数','zero_tag_problems'),('使用タグ数','active_tags'),('未使用タグ数','unused_tags')]:text+=f"| {label} | {s['datasets']['all_difficulties'][key]:,} | {s['datasets']['under_2000'][key]:,} |\n"
text+='''
- 入力は `output_v4/problem_tag_matrix.csv`。主解・別解・補助はすべて1、概念・証明のタグは含めません。
- クラスタリング対象は**タグ**。問題は出現パターンを表す特徴量です。
- 難易度不明の問題は全難易度に含め、2000未満には含めません。片方は同じV4行列から行だけを抽出しました。
- 各対象内で0件のタグだけを除外。1問だけのタグも保持しています。今回は使用タグに共起ゼロの孤立タグはありません。
- 重み付け・SVD・NMF・旧実験の手動制約は適用していません。
- 主解と別解で併記されたタグも共起するため、近さが同じ実装手順・同じ学習単位を意味するとは限りません。

## cut=0.8の比較

以下は同じ数値cutでの挙動比較です。コサインとジャカードで同じ粒度という意味ではありません。

| 距離 | 連結法 | 全難易度の群数 | 最大群のタグ数 | 2000未満の群数 | 最大群のタグ数 |
| --- | --- | ---: | ---: | ---: | ---: |
'''
for metric in M:
 for method in L:
  a=s['datasets']['all_difficulties']['models'][metric+'_'+method]['cut_0_8'];b=s['datasets']['under_2000']['models'][metric+'_'+method]['cut_0_8']
  text+=f"| {M[metric]} | {L[method]} | {a['clusters']} | {a['largest_cluster_tags']} | {b['clusters']} | {b['largest_cluster_tags']} |\n"
text+='''
全難易度のコサイン＋単連結法では、cut=0.7は103群・最大20タグ、0.8は36群・最大152タグ、0.9は7群・最大188タグでした。少数の近いタグが橋渡しになり、群が連鎖して結合する挙動です。ジャカード＋単連結法でも、cut=0.9では最大68タグの群ができています。

平均連結法は群間の全タグペアの平均距離、単連結法は最小距離、完全連結法は最大距離で結合します。[SciPyの定義](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html)。

## ほぼ同じ群数での比較：目標80群

| 対象 | 距離 | 連結法 | 実際の群数 | cut | 最大群のタグ数 |
| --- | --- | --- | ---: | ---: | ---: |
'''
for r in matched:
 if r['target_clusters']!='80':continue
 text+=f"| {DS[r['dataset']]} | {M[r['metric']]} | {L[r['linkage']]} | {r['actual_clusters']} | {float(r['cut']):.6f} | {r['largest_cluster_tags']} |\n"
text+='''
単連結法は群数をそろえても大きい群と単独群が混在します。全難易度・目標80群では、コサイン＋単連結法は80群中の最大群が45タグ、平均連結法は7タグ、完全連結法は9タグでした。

**同じ高さの結合は分割しません。** そのため目標群数に一致しない条件があります。目標40群では、全難易度の完全連結法は距離1未満で残る群から距離1で一気に1群になり、40群を実現できません。保存した目標40群の内訳は「最も近い実現可能な群数」で、両距離とも実際は1群です。これは推奨設定ではありません。2000未満では完全連結法の最も近い結果は72群／76群でした。

## 内訳から見えること

全難易度・コサイン＋平均連結法・cut=0.8では、例えば以下が同じ群です。

- 最大流・最小カット・燃やす埋める・Dinic
- 分割統治・多項式/FPS・畳み込み・FFT
- Heap・最短経路・Dijkstra・疎グラフ向けDijkstra
- BIT・Segment Tree・座標圧縮

一方で、Union-Find・BFS・DFS・連結成分分解も同じ群です。完全連結法ではGrundy・Nim・線形篩が同じ群になる例があります。共起だけによる分類は、補助手法や少数問題由来の関係をそのまま反映します。今回の結果は候補となる分類であり、タグの同義性や粒度の一致を保証しません。

## 樹形図・クラスタ内訳

樹形図はタグ名を左、結合距離を右に表示します。枝色はcut=0.7、破線は0.7・0.8・0.9です。色は繰り返され、分野名に対応しません。SVGを拡大すると全タグを読めます。
'''
for ds,title in DS.items():
 text+=f'\n### {title}\n\n| 距離 | 連結法 | 樹形図 | cut=0.7 | cut=0.8 | cut=0.9 | 目標80群 |\n| --- | --- | --- | --- | --- | --- | --- |\n'
 for metric in M:
  for method in L:
   f=ds+'/'+metric+'_'+method
   text+=f"| {M[metric]} | {L[method]} | [PNG]({f}/dendrogram.png)・[SVG]({f}/dendrogram.svg) | [内訳]({f}/clusters_cut_0.7.md) | [内訳]({f}/clusters_cut_0.8.md) | [内訳]({f}/clusters_cut_0.9.md) | [内訳]({f}/clusters_target_80.md) |\n"
text+='''
各フォルダにはlinkage.csv、内訳CSV・JSON、cut別数値もあります。[代表タグ対の比較](example_pairs.csv)、[クラスタ所属の一致度ARI](partition_agreement.csv)、各対象の全タグ対の距離表も保存しました。

## 検証

入力V4ファイルのハッシュ不変、距離の集合件数からの独立計算との一致、12条件の全2,148結合について最小の許容距離の組を選んでいることと結合高を検証しました。36個の表示用分割のタグ所属・問題ID和集合・群数も照合しました。単連結法は距離閾値グラフの連結成分と一致し、完全連結法は各群の最大ペア距離がcut以下であることも確認済みです。[verification.json](verification.json)

シルエット係数はそれぞれの元距離で計算しました。異なる距離の数値をそのまま分類精度として比較していません。コーフェネティック相関は元距離を樹形図がどれだけ再現するかの指標であり、意味の正しさではありません。独立した正解分類による評価はしていません。

## 再実行

ワークスペース直下で実行します。

```powershell
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/hierarchical_v4_experiment.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/verify_hierarchical_v4.py
.\\.venv-clustering\\Scripts\\python.exe -X utf8 abc_all/report_hierarchical_v4.py
```

入力の版・ハッシュ、NumPy/SciPy等の版、同距離時の扱いは [summary.json](summary.json) に記録しています。距離は [コサイン](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.cosine.html)・[ジャカード](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.jaccard.html) の定義に従います。追加API呼出しは0回です。
'''
(O/'README.md').write_text(text,encoding='utf-8-sig')
# Embed data: browser can open this artifact offline without a web server or fetch.
data={}
for ds in DS:
 for metric in M:
  for method in L:
   key=ds+'/'+metric+'_'+method;f=O/key
   data[key]={'image':key+'/dendrogram.svg','partitions':{}}
   for suffix in ('cut_0.7','cut_0.8','cut_0.9','target_80','target_40'):
    data[key]['partitions'][suffix]=json.loads((f/f'clusters_{suffix}.json').read_text(encoding='utf-8'))
encoded=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
page='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>V4 タグ階層クラスタリング比較</title>
<style>body{font-family:Meiryo,system-ui,sans-serif;margin:0;background:#f4f6f8;color:#182b3a}main{max-width:1400px;margin:auto;padding:26px}h1{font-size:25px;margin:0 0 10px}.controls,.stats,.panel{background:white;border:1px solid #dce2e6;border-radius:10px;padding:16px;margin:16px 0}label{display:inline-flex;flex-direction:column;gap:5px;font-size:13px;margin:0 16px 8px 0}select,input{font:inherit;padding:8px;border:1px solid #b6c4cc;border-radius:5px}.stats{display:flex;gap:32px;flex-wrap:wrap}.value{font-size:28px;font-weight:700;color:#176b80}small,.note{color:#52636e}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #e4e8eb}td:nth-child(2),td:nth-child(3){white-space:nowrap}.panel{overflow:auto}img{width:100%;height:auto;display:block}details summary{cursor:pointer;font-weight:bold;padding:5px}a{color:#176b80}.warning{color:#9c3e12;font-weight:bold}#search{width:260px}button{padding:8px;cursor:pointer}</style>
<main><h1>V4 タグ階層クラスタリング比較</h1><div class="note">修正版V4／主解・別解・補助を同じ重みで比較。全難易度194タグ、2000未満166タグ。 <a href="README.md">実験条件・検証結果</a> · <a href="comparison.png">群数の比較図</a></div>
<div class="controls"><label>問題範囲<select id="dataset"><option value="all_difficulties">全難易度</option><option value="under_2000">2000未満</option></select></label><label>距離<select id="metric"><option value="cosine">コサイン距離</option><option value="jaccard">ジャカード距離</option></select></label><label>連結法<select id="method"><option value="average">平均連結法</option><option value="single">単連結法</option><option value="complete">完全連結法</option></select></label><label>分割<select id="cut"><option value="cut_0.8">cut=0.8</option><option value="cut_0.7">cut=0.7</option><option value="cut_0.9">cut=0.9</option><option value="target_80">目標80群</option><option value="target_40">目標40群</option></select></label><label>タグ名・IDの検索<input id="search" placeholder="例：確率、DP、T029"></label></div>
<div id="stats" class="stats"></div><p id="warning" class="warning"></p><p id="description"></p>
<div class="panel"><table><thead><tr><th>クラスタ</th><th>タグ数</th><th>問題和集合</th><th>タグ</th></tr></thead><tbody id="members"></tbody></table></div>
<details class="panel"><summary>全タグの樹形図を表示</summary><p class="note">枝色は常にcut=0.7。破線は0.7・0.8・0.9。上の表は選択中のcutによる内訳です。SVGを別タブで開くと拡大できます。</p><p><a id="svg" target="_blank">拡大用SVGを開く</a></p><img id="tree" loading="lazy" alt="選択中の手法の樹形図"></details>
<p class="note">同じcut値は同じ粒度を保証しません。同距離の結合を強制分割しないため、目標40/80群に一致しない場合があります。近さはタグの同義性を意味しません。</p></main>
<script>const DATA=__DATA__;
const $=id=>document.getElementById(id);const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function render(){const key=$('dataset').value+'/'+$('metric').value+'_'+$('method').value;const d=DATA[key];const p=d.partitions[$('cut').value];const groups=p.clusters;const total=groups.reduce((a,g)=>a+g.tag_count,0);const max=Math.max(...groups.map(g=>g.tag_count));$('stats').innerHTML=[['使用タグ',total],['クラスタ',groups.length],['最大群のタグ',max],['実際のcut',Number(p.cut).toFixed(6)]].map(([k,v])=>'<div><small>'+k+'</small><div class="value">'+v+'</div></div>').join('');$('description').textContent=p.description;$('warning').textContent=p.target_clusters&&p.actual_clusters!==p.target_clusters?'同距離の結合があるため目標'+p.target_clusters+'群を実現できません。最も近い実現可能な'+p.actual_clusters+'群を表示しています。':'';const q=$('search').value.toLowerCase();const filtered=groups.filter(g=>(g.tag_ids.join(' ')+' '+g.tags.join(' ')).toLowerCase().includes(q));$('members').innerHTML=filtered.sort((a,b)=>b.tag_count-a.tag_count||a.cluster_id.localeCompare(b.cluster_id)).map(g=>'<tr><td>'+g.cluster_id+'</td><td>'+g.tag_count+'</td><td>'+g.problem_count+'</td><td>'+g.tags.map((t,i)=>esc(g.tag_ids[i]+' '+t)).join(' ／ ')+'</td></tr>').join('');$('tree').src=d.image;$('svg').href=d.image;}for(const id of ['dataset','metric','method','cut'])$(id).addEventListener('change',render);$('search').addEventListener('input',render);render();</script></html>'''
(O/'index.html').write_text(page.replace('__DATA__',encoded),encoding='utf-8')
p=R/'README.md';prior=p.read_text(encoding='utf-8-sig');head='''# 2026-11-24 V4で階層クラスタリングを再実行

[距離2種類 × 連結法3種類の比較結果](hierarchical_v4_20261124/README.md)・[操作できる結果一覧](hierarchical_v4_20261124/index.html)。V4の全難易度／2000未満で、コサイン・ジャカードと平均・単・完全連結法を比較しました。

'''
if not prior.startswith('# 2026-11-24 V4で階層'):p.write_text(head+prior,encoding='utf-8-sig')
print('README and offline comparison browser written')
