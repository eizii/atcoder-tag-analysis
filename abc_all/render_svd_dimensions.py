# -*- coding: utf-8 -*-
"""Render existing SVD 8/16/64 linkages without changing prior experiments."""
import csv,json,hashlib,zipfile,re
from pathlib import Path
import numpy as np
from scipy.cluster.hierarchy import dendrogram,fcluster,is_valid_linkage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'svd_experiment_20261112'
OUT=ROOT/'svd_dimension_dendrograms_20261119'
DIMS=[8,16,64]
CUTS=[.7,.8,.9]
DATASETS={'all_difficulties':'全難易度','under_2000':'2000未満'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    protected={str(p.relative_to(SOURCE)):sha(p) for p in SOURCE.rglob('*') if p.is_file()}
    available={f.name for f in font_manager.fontManager.ttflist}
    font=next((f for f in ['Meiryo','Yu Gothic','MS Gothic'] if f in available),'DejaVu Sans')
    matplotlib.rcParams.update({'font.family':[font,'DejaVu Sans'],'axes.unicode_minus':False,'svg.fonttype':'none'})
    checks=[]
    md=['# SVD 8・16・64次元のデンドログラム','', '2026-11-19作成。既存のSVD実験の保存済みlinkageから描画。再学習・タグ付与変更なし。制約なしの通常の平均連結法。', '',
        '全難易度は156タグ、2000未満は138タグが比較対象。文字列処理1タグは別枠。各画像の赤破線がcut、枝色はcutで分けた群の目印。色は分野を表さず、別の図の同じ色と対応しません。', '',
        '次元数を変えると距離空間も変わります。同じcutが同じ学習粒度を意味するわけではありません。タグ名は左側、距離は右へ増加します。', '',
        '| データ | SVD次元 | cut=0.7 | cut=0.8 | cut=0.9 |','|---|---:|---|---|---|']
    for ds,title in DATASETS.items():
        for k in DIMS:
            mf=SOURCE/ds/('svd_'+str(k));dest=OUT/ds/('svd_'+str(k));dest.mkdir(parents=True,exist_ok=True)
            with (mf/'tag_vectors.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            labels=[r['tag_id']+' '+r['tag']+' (n='+r['problem_count']+')' for r in rows]
            z=np.loadtxt(mf/'linkage.csv',delimiter=',',skiprows=1)
            is_valid_linkage(z,throw=True);assert len(z)+1==len(labels)
            cells=[]
            for cut in CUTS:
                n_clusters=len(set(fcluster(z,cut,criterion='distance')))
                fig,ax=plt.subplots(figsize=(19,max(18,len(labels)*.20)))
                tree=dendrogram(z,labels=labels,orientation='right',leaf_font_size=9,color_threshold=np.nextafter(cut,np.inf),above_threshold_color='#78818b',ax=ax)
                ax.axvline(cut,color='#b82739',ls='--',lw=1.2)
                ax.set_xlim(0,max(1.03,float(z[-1,2])+.03,cut+.03))
                ax.yaxis.set_ticks_position('left');ax.tick_params(axis='y',length=3,pad=4,labelleft=True,labelright=False,left=True,right=False)
                assert ax.yaxis.get_ticks_position()=='left'
                assert tree['leaves']==dendrogram(z,no_plot=True)['leaves']
                assert len(tree['ivl'])==len(labels) and len(set(tree['leaves']))==len(labels)
                ax.set_xlabel('距離 = 1 − コサイン類似度 / 平均連結法')
                ax.set_title(f'{title}：SVD {k}次元 / cut={cut:.1f}\n{len(labels)}タグ → {n_clusters}クラスタ（共起なしの1タグは別枠）',fontsize=14,pad=16)
                ax.grid(axis='x',alpha=.22);ax.set_axisbelow(True)
                fig.text(.025,.012,f'SVD {k}次元の比較用表示。最適次元数と確認したものではありません。n=タグの問題数。文字列処理は共起情報なしのため別枠。\n赤破線がカット位置。枝色は繰り返され、分野を表しません。同じcutでも次元数が違えば同じ粒度を意味しません。',fontsize=9)
                fig.tight_layout(rect=(.015,.042,.995,.995))
                stem=f'dendrogram_cut_{cut:.1f}'
                for ext in ['png','svg']:fig.savefig(dest/(stem+'.'+ext),dpi=140,facecolor='white')
                plt.close(fig)
                with Image.open(dest/(stem+'.png')) as im:im.verify()
                with Image.open(dest/(stem+'.png')) as im:width,height=im.size
                assert width>2000 and height>2000
                svg=(dest/(stem+'.svg')).read_text(encoding='utf-8');assert '<svg' in svg
                checks.append(dict(dataset=ds,dimensions=k,cut=cut,tags=len(labels),clusters=n_clusters,labels='left',leaf_order_unchanged=True,png_width=width,png_height=height,source_linkage_sha256=sha(mf/'linkage.csv')))
                rel=(dest/(stem+'.png')).relative_to(OUT).as_posix()
                cells.append(f'{n_clusters}群：[PNG]({rel})・[SVG]({rel[:-3]}svg)')
            md.append(f'| {title} | {k} | '+' | '.join(cells)+' |')
            print(f'{ds} / SVD {k}: saved cuts 0.7, 0.8, 0.9',flush=True)
    assert protected=={str(p.relative_to(SOURCE)):sha(p) for p in SOURCE.rglob('*') if p.is_file()}
    (OUT/'README.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    with (OUT/'figure_index.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
    (OUT/'verification.json').write_text(json.dumps(dict(passed=True,source_files_unchanged=True,prior_source_sha256=protected,font=font,figures=checks),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for link in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text(encoding='utf-8')):assert (OUT/link).exists()
    target=OUT/'svd_8_16_64_dendrograms.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file() and p!=target:z.write(p,p.relative_to(OUT))
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print(json.dumps(dict(passed=True,png_figures=len(checks),svg_figures=len(checks),source_files_unchanged=True,zip_bytes=target.stat().st_size),ensure_ascii=False))

if __name__=='__main__':main()
