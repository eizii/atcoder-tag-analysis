# -*- coding: utf-8 -*-
"""Bundle all four saved SVD dimensions and render four-panel comparisons."""
import csv,hashlib,json,re,shutil,zipfile
from pathlib import Path
import numpy as np
from scipy.cluster.hierarchy import dendrogram,fcluster
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'svd_experiment_20261112'
EXTRA=ROOT/'svd_dimension_dendrograms_20261119'
OUT=ROOT/'svd_8_16_32_64_bundle_20261119'
DATASETS={'all_difficulties':'全難易度','under_2000':'2000未満'}
DIMS=[8,16,32,64]
CUTS=[.7,.8,.9]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    protected={str(p.relative_to(ROOT)):sha(p) for base in [SOURCE,EXTRA] for p in base.rglob('*') if p.is_file()}
    fonts={f.name for f in font_manager.fontManager.ttflist};font=next((f for f in ['Meiryo','Yu Gothic','MS Gothic'] if f in fonts),'DejaVu Sans')
    matplotlib.rcParams.update({'font.family':[font,'DejaVu Sans'],'axes.unicode_minus':False,'svg.fonttype':'none'})
    records=[];combined=[];copied=[]
    md=['# SVD 8・16・32・64次元：まとめ','', '全難易度・2000未満、cut=0.7・0.8・0.9。制約なしのSVD＋平均連結法。保存済みの計算結果から作成し、再学習・タグ付与変更はしていません。','',
    '## 4次元設定を横に並べた比較画像','',
    '左から8・16・32・64次元です。画像は横に長いため、拡大して確認してください。タグ名は各パネルの左側です。','',
    '| データ | cut=0.7 | cut=0.8 | cut=0.9 |','|---|---|---|---|']
    for ds,title in DATASETS.items():
        cache={};target=OUT/ds;target.mkdir(exist_ok=True)
        for dim in DIMS:
            folder=SOURCE/ds/('svd_'+str(dim))
            with (folder/'tag_vectors.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            z=np.loadtxt(folder/'linkage.csv',delimiter=',',skiprows=1);labels=[r['tag_id']+' '+r['tag']+' (n='+r['problem_count']+')' for r in rows]
            cache[dim]=(z,labels)
            dest=target/('svd_'+str(dim));dest.mkdir(exist_ok=True)
            for cut in CUTS:
                clusters=len(set(fcluster(z,cut,criterion='distance')))
                records.append(dict(dataset=ds,dimensions=dim,cut=cut,tags=len(labels),clusters=clusters))
                original=(SOURCE if dim==32 else EXTRA)/ds/('svd_'+str(dim))
                for ext in ['png','svg']:
                    name=f'dendrogram_cut_{cut:.1f}.'+ext
                    shutil.copy2(original/name,dest/name);assert sha(original/name)==sha(dest/name)
                    copied.append(dict(path=(dest/name).relative_to(OUT).as_posix(),sha256=sha(dest/name)))
        cells=[]
        for cut in CUTS:
            count_labels=[];n=len(cache[8][1]);xmax=max(1.03,max(float(cache[k][0][-1,2]) for k in DIMS)+.03)
            fig,axes=plt.subplots(1,4,figsize=(76,max(18,n*.20)))
            for ax,dim in zip(axes,DIMS):
                z,labels=cache[dim];count=len(set(fcluster(z,cut,criterion='distance')))
                tree=dendrogram(z,labels=labels,orientation='right',leaf_font_size=9,color_threshold=np.nextafter(cut,np.inf),above_threshold_color='#78818b',ax=ax)
                ax.yaxis.set_ticks_position('left');ax.tick_params(axis='y',length=3,pad=4,labelleft=True,labelright=False,left=True,right=False)
                assert ax.yaxis.get_ticks_position()=='left' and tree['leaves']==dendrogram(z,no_plot=True)['leaves']
                assert len(set(tree['leaves']))==n
                ax.axvline(cut,color='#b82739',ls='--',lw=1.2);ax.set_xlim(0,xmax);ax.grid(axis='x',alpha=.22);ax.set_axisbelow(True)
                ax.set_title(f'SVD {dim}次元：{count}クラスタ',fontsize=17,pad=16)
                ax.set_xlabel('距離 = 1 − コサイン類似度 / 平均連結法',fontsize=12)
                count_labels.append(f'{dim}次元={count}群')
            fig.suptitle(f'{title}：SVD 8・16・32・64次元 / cut={cut:.1f}\n{n}タグを比較（文字列処理1タグは別枠）',fontsize=24,y=.995)
            fig.text(.01,.01,'各パネルのタグ名は左側。タグの並びは次元ごとに異なります。枝色は群の目印で、異なるパネルの同じ色と対応しません。\n同じcutが同じ学習粒度を意味するわけではありません。次元数は比較用の設定です。',fontsize=14)
            fig.tight_layout(rect=(.003,.043,.997,.97),w_pad=3)
            stem=f'comparison_8_16_32_64_cut_{cut:.1f}'
            for ext in ['png','svg']:fig.savefig(target/(stem+'.'+ext),dpi=140,facecolor='white')
            plt.close(fig)
            with Image.open(target/(stem+'.png')) as im:im.verify()
            with Image.open(target/(stem+'.png')) as im:width,height=im.size
            combined.append(dict(dataset=ds,cut=cut,dimensions=DIMS,labels='left_on_every_panel',common_distance_axis=True,leaf_orders_unchanged=True,png_width=width,png_height=height,clusters=count_labels))
            rel=(target/(stem+'.png')).relative_to(OUT).as_posix();cells.append(f'[PNG]({rel})・[SVG]({rel[:-3]}svg)')
            print(ds+f' / cut={cut:.1f}: '+', '.join(count_labels),flush=True)
        md.append('| '+title+' | '+' | '.join(cells)+' |')
    md.extend(['','## 個別画像','', '| データ | 次元数 | cut=0.7 | cut=0.8 | cut=0.9 |','|---|---:|---|---|---|'])
    for ds,title in DATASETS.items():
        for dim in DIMS:
            cells=[]
            for cut in CUTS:
                rec=next(r for r in records if (r['dataset'],r['dimensions'],r['cut'])==(ds,dim,cut))
                stem=ds+f'/svd_{dim}/dendrogram_cut_{cut:.1f}'
                cells.append(f'{rec["clusters"]}群：[PNG]({stem}.png)・[SVG]({stem}.svg)')
            md.append(f'| {title} | {dim} | '+' | '.join(cells)+' |')
    md.extend(['','nはタグに付与された問題数です。全難易度は156タグ、2000未満は138タグが比較対象で、共起のない文字列処理1タグは別枠です。',''])
    (OUT/'README.md').write_text('\n'.join(md),encoding='utf-8')
    with (OUT/'figure_index.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    assert all(sha(ROOT/p)==digest for p,digest in protected.items())
    for link in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text(encoding='utf-8')):assert (OUT/link).exists()
    (OUT/'verification.json').write_text(json.dumps(dict(passed=True,source_files_unchanged=True,source_sha256=protected,individual_images_copied=copied,combined_figures=combined,markdown_links_valid=True),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    zip_path=OUT/'svd_8_16_32_64_dendrograms.zip'
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file() and p!=zip_path:z.write(p,p.relative_to(OUT))
    with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None;entries=len(z.namelist())
    print(json.dumps(dict(passed=True,individual_figures=24,combined_figures=6,zip_entries=entries,zip_bytes=zip_path.stat().st_size),ensure_ascii=False))
if __name__=='__main__':main()
