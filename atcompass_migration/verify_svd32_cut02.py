# -*- coding: utf-8 -*-
"""Independent frozen-data membership and app-export integrity verification."""
import csv,json,hashlib
from pathlib import Path
import numpy as np
from scipy.cluster.hierarchy import fcluster
from svd32_cut02 import ROOT,APP,OUT,SOURCE,SVD,FIELDS,VERSION

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    catalog=json.loads((APP/'src/data/tagCatalog.json').read_text(encoding='utf-8'))
    rows=read(APP/'public/all_problems.csv');matrix=read(SOURCE/'problem_tag_matrix.csv');problems=read(SOURCE/'problems.csv');vectors=read(SVD/'tag_vectors.csv')
    src={r['problem_id']:r for r in problems};m={r['problem_id']:r for r in matrix};ids=[r['tag_id'] for r in vectors]
    labels=fcluster(np.loadtxt(SVD/'linkage.csv',delimiter=',',skiprows=1),.2,criterion='distance')
    expected={frozenset(t for t,l in zip(ids,labels) if l==value) for value in set(labels)}
    actual={frozenset(t['tag_id'] for t in g['member_tags']) for g in catalog['clusters'] if not g['separate_from_svd']}
    assert expected==actual and len(actual)==86
    members=[t['tag_id'] for g in catalog['clusters'] for t in g['member_tags']]
    assert len(members)==len(set(members))==139 and set(members)==set(ids)|{'T073'}
    assert catalog['version']==VERSION and len(catalog['clusters'])==87 and catalog['display_min_problem_count']==1
    assert list(rows[0])==FIELDS and len(rows)==3391
    assert len({(r['tag'],r['problem_id']) for r in rows})==len(rows)
    for r in rows:
        original=src[r['problem_id']]
        for key in ['title','difficulty','url']:assert r[key]==original[key],(r['problem_id'],key)
        value=float(r['difficulty']);assert 0<=value<2000
        low=int(value//400)*400;assert r['diff_band']==f'{low}-{low+399}'
    for group in catalog['clusters']:
        tids=[t['tag_id'] for t in group['member_tags']]
        want={pid for pid,r in m.items() if any(int(r[t]) for t in tids)}
        got={r['problem_id'] for r in rows if r['tag']==group['label']}
        assert want==got and len(got)==group['problem_count'] and len(got)>0
    displayed={r['problem_id'] for r in rows};unassigned=read(OUT/'unassigned_problems.csv')
    missing={r['problem_id'] for r in unassigned}
    assert len(displayed)==1693 and len(missing)==780 and not displayed&missing and displayed|missing==set(src)
    for r in vectors:assert sum(int(mrow[r['tag_id']]) for mrow in matrix)==int(r['problem_count'])
    assert sha(APP/'public/all_problems.csv')==catalog['problemCatalogSha256']
    for name,digest in catalog['source_sha256'].items():assert sha(ROOT.parent/name)==digest
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    for name,entry in manifest.items():
        assert sha(APP/name)==entry['staged_sha256']
        if entry['before_sha256']:assert sha(OUT/'before'/name)==entry['before_sha256']
    result=dict(passed=True,display_tags=87,clustered_tags=86,separate_tags=1,source_problems=2473,displayed_problems=1693,unassigned_problems=780,problem_cluster_pairs=len(rows),singleton_problem_tags=sum(g['problem_count']==1 for g in catalog['clusters']),source_metadata_preserved=True,exact_saved_svd_partition=True,duplicate_problem_cluster_pairs=0,backup_hashes_verified=True)
    (OUT/'data_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
