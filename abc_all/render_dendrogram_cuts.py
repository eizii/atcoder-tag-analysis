"""Render cut=0.8/0.9 without changing the frozen clustering inputs."""
import csv, hashlib, json, zipfile
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy.cluster.hierarchy import dendrogram, fcluster, is_valid_linkage

ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'comparison_20261105'
OUT = BASE / 'dendrogram_cuts_08_09'
DATASETS = {'all_difficulties': '全難易度（難易度不明を含む）', 'under_2000': '2000未満'}
CUTS = (0.8, 0.9)
EXPECTED = {'all_difficulties': {0.8: 135, 0.9: 102}, 'under_2000': {0.8: 113, 0.9: 89}}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sources = [ROOT / 'taxonomy.json', BASE / 'comparison_summary.json']
for key in DATASETS:
    sources.extend([BASE / key / 'linkage.csv', BASE / key / 'problem_tag_matrix.csv', BASE / (key + '_dendrogram.png'), BASE / (key + '_dendrogram.svg')])
before = {str(p.relative_to(ROOT)): sha(p) for p in sources}
names = {r['tag_id']: r['tag'] for r in json.loads((ROOT / 'taxonomy.json').read_text(encoding='utf-8'))}
available = {f.name for f in font_manager.fontManager.ttflist}
font = next((n for n in ['Meiryo', 'Yu Gothic', 'Noto Sans CJK JP', 'MS Gothic'] if n in available), 'DejaVu Sans')
matplotlib.rcParams.update({'font.family': [font, 'DejaVu Sans'], 'axes.unicode_minus': False, 'svg.fonttype': 'none'})
OUT.mkdir(exist_ok=True)
records = []
for key, title in DATASETS.items():
    folder = BASE / key
    with (folder / 'problem_tag_matrix.csv').open(encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        tids = next(reader)[1:]
        x = np.array([[int(v) for v in row[1:]] for row in reader], dtype=np.uint8)
    support = x.sum(axis=0)
    active = np.flatnonzero(support)
    labels = [f'{tids[j]}  {names[tids[j]]}  (n={int(support[j])})' for j in active]
    z = np.loadtxt(folder / 'linkage.csv', delimiter=',', skiprows=1)
    assert is_valid_linkage(z, throw=True) and len(z) + 1 == len(active)
    previous_leaves = None
    for cut in CUTS:
        partition = fcluster(z, cut, criterion='distance')
        count = len(set(partition))
        assert count == EXPECTED[key][cut]
        fig, ax = plt.subplots(figsize=(19, max(18, len(labels) * 0.185)))
        tree = dendrogram(z, labels=labels, orientation='left', leaf_font_size=8,
                          color_threshold=np.nextafter(cut, np.inf), above_threshold_color='#737b85', ax=ax)
        if previous_leaves is not None:
            assert tree['leaves'] == previous_leaves
        previous_leaves = tree['leaves']
        ax.axvline(cut, color='#bc2634', linestyle='--', linewidth=1.3, label=f'distance cut = {cut:.1f}')
        ax.set_xlim(0, 1.035)
        ax.set_xticks(np.arange(0, 1.01, 0.1))
        ax.grid(axis='x', color='#dce1e6', linewidth=0.5, alpha=0.8)
        ax.set_axisbelow(True)
        ax.set_xlabel('Jaccard距離 / 平均連結法', fontsize=12)
        ax.set_title(f'{title}：デンドログラム\ncut={cut:.1f} / {len(labels)}タグ → {count}クラスタ / {len(x):,}問', fontsize=15, pad=18)
        ax.legend(loc='lower left', fontsize=10)
        fig.text(0.025, 0.014, '2026-11-05固定データ・同じ自動付与ルール / n=タグの問題数 / 問題数による除外なし\n同一データ内では樹形とタグ順序は共通。赤破線がカット位置。枝色は繰り返され、色自体は分野を表しません。', fontsize=9)
        fig.tight_layout(rect=(0.015, 0.04, 0.995, 0.995))
        stem = f'{key}_cut_{cut:.1f}_dendrogram'
        for ext in ['png', 'svg']:
            fig.savefig(OUT / (stem + '.' + ext), dpi=150, facecolor='white')
        plt.close(fig)
        records.append({'dataset': key, 'cut': cut, 'problems': len(x), 'active_tags': len(labels), 'clusters': count, 'png': stem + '.png', 'svg': stem + '.svg'})
assert before == {str(p.relative_to(ROOT)): sha(p) for p in sources}
manifest = {'source_snapshot': 'comparison_20261105', 'distance': 'jaccard', 'linkage': 'average', 'font': font, 'cut_rule': 'merge distance <= cut', 'minimum_problem_filter': None, 'source_sha256': before, 'checks': ['original_inputs_and_figures_unchanged', 'valid_linkage', 'active_tag_count_matches_linkage', 'cluster_counts_match_sweep', 'identical_leaf_order_across_cuts'], 'figures': records}
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
readme = ['# distance cut 0.8・0.9のデンドログラム', '', '2026-11-05の固定データから保存済みの平均連結法の樹形を読み込み、カット位置と色分けを変更した。元のcut=0.7のファイルは変更していない。', '', '| 対象 | cut | 元タグ数 | クラスタ数 | PNG | SVG |', '|---|---:|---:|---:|---|---|']
for r in records:
    readme.append(f"| {DATASETS[r['dataset']]} | {r['cut']:.1f} | {r['active_tags']} | {r['clusters']} | [画像]({r['png']}) | [拡大用]({r['svg']}) |")
readme.extend(['', '- Jaccard距離・平均連結法。結合距離がcut以下なら同一クラスタとする。', '- 1タグのみ、1問のみのクラスタも含める。問題数による除外は行っていない。', '- 各データ内で樹形と葉の順序は共通。cutの変更で樹形そのものは変わらない。', '- nは各タグに付与された問題数。枝色に分野名の意味はない。色は繰り返される。', '- タグ付与は自動付与の比較用データであり、全件の独立した人手検証は未実施。', '- manifest.jsonに入力ハッシュと検証項目を記録。', ''])
(OUT / 'README.md').write_text('\n'.join(readme), encoding='utf-8')
with zipfile.ZipFile(OUT / 'dendrogram_cuts_08_09.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for p in sorted(OUT.iterdir()):
        if p.suffix in {'.png', '.svg', '.json', '.md'}:
            zf.write(p, p.name)
print(json.dumps({'output_dir': str(OUT), 'font': font, 'figures': records, 'checks': manifest['checks']}, ensure_ascii=False, indent=2))
