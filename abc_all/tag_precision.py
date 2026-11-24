"""Build V3 from the frozen corpus with scoped evidence and explicit review decisions.

No inherited v1 labels, API calls, or edits to v2 outputs. Full/partial semantic
reviews are distinguished; a named technique remains provisional until reviewed.
"""
import argparse,csv,hashlib,json,re
from collections import Counter
from pathlib import Path
from collect_statements import load_json,save_json
from evidence_scope import shared_body_keys,executable_code,local_context,rejection_reason
from tag_all import CODE_RULES,csv_write,normalize,alias_regex
from precision_policy import POLICY_VERSION,scoped_editorial,named_evidence_v3,description_rejection

ROOT=Path(__file__).resolve().parent
VERSION='abc-all-266-evidence-v3'
DESCRIPTION_RULES={
 'T022':r'メモ化(?:再帰)?',
 'T065':r'(?:すべて|全て|全部)(?:の)?(?:組み合わせ|組合せ|場合|パターン|候補).{0,35}(?:試|調べ|列挙)|(?:二重|三重|多重)(?:の)?ループで',
 'T076':r'問題文(?:の|で)(?:通り|とおり)|そのまま(?:実装|実行|処理|行う)|順番に(?:処理|更新)|シミュレート',
 'T077':r'(?:小さい|大きい|昇|降)順に並べ(?:替え|る)|並び替え',
 'T086':r'(?:区間|部分)(?:の)?和を前計算',
 'T162':r'素数(?:である|かどうか|か否か).{0,20}(?:判定|調べ)|(?:判定|調べ).{0,20}素数',
 'T264':r'(?:割った|割り算の)(?:ときの)?(?:余り|あまり)|割り切れるか|倍数かどうか',
}
# These are alternate spellings of named techniques, not new heuristic categories.
EXTRA_ALIASES={
 'T001':['Fenwick'], 'T005':['Union_Find','union-find'],
 'T017':['bit DP','bitdp'], 'T020':['全方位 木 DP'],
 'T022':['動的計画'], 'T027':['木上のDP','木上 DP'],
 'T031':['二部グラフの最大マッチング','二部グラフ上の最大マッチング'],
 'T071':['Z algorithm','Z-algorithm'], 'T075':['いもす'],
 'T082':['半分全探索'], 'T086':['累積 和'],
 'T097':['ユークリッド互除法'], 'T098':['オイラー関数','Euler totient'],
 'T107':['Hadamard 変換','hadamard変換'], 'T127':['多項式の積'],
 'T134':['素因数 分解'], 'T176':['繰り返し二乗','繰り返し自乗'],
 'T178':['二部グラフかどうか','二部グラフであるか'],
 'T253':['エラトステネスのふるい','エラトステネスの篩'],
}

def fingerprint(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read_jsonl(path):
 with path.open(encoding='utf-8-sig') as stream:return [json.loads(line) for line in stream]
def clean_code(code):
 code=executable_code(code)
 return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',lambda m:' '*(m.end()-m.start()),code)

def read_reviews(docs,review_path=None):
 path=Path(review_path) if review_path is not None else ROOT/'precision_reviews.tsv'
 reviews={}
 if not path.exists():return reviews
 with path.open(encoding='utf-8-sig',newline='') as f:
  for row in csv.DictReader(f,delimiter='\t'):
   pid=row['problem_id'];d=docs[pid]
   # One row describes one coherent decision. Multiple rows per problem are allowed.
   indices=([i for i,e in enumerate(d['editorials']) if normalize(row['evidence_quote']) in normalize(e['text'])] if row['source_indices']=='match' else [int(i) for i in row['source_indices'].split(',')]) if row['source_indices']!='statement' else []
   if row['source_indices']=='match' and not indices:raise ValueError('No matching editorial: '+pid)
   row=dict(row,source_indices=','.join(map(str,indices)) if indices else 'statement')
   source_text='\n'.join(d['editorials'][i]['text'] for i in indices) if indices else d['statement']
   if not row['evidence_quote'] or normalize(row['evidence_quote']) not in normalize(source_text):
    raise ValueError('Review quote not found in selected source: '+pid+' '+row['evidence_quote'])
   accepted={}
   if row['accepted']:
    accepted=dict(t.split(':') for t in row['accepted'].split(','))
   review=dict(row,accepted=accepted,rejected=row['rejected'].split(',') if row['rejected'] else [],
    evidence_urls=sorted({d['editorials'][i].get('url') or d['url'] for i in indices}) if indices else [d['url']],
    evidence_sha256=hashlib.sha256(source_text.encode()).hexdigest(),reviewer='assistant',independent_human_review=False,review_date='2026-11-23')
   reviews.setdefault(pid,[]).append(review)
 return reviews

def build(output='output_v3',additional_review_files=(),baseline_dir='output_v2_uniform',version=VERSION):
 manifest=load_json(ROOT/'manifest.json')
 taxonomy={t['tag_id']:t['tag'] for t in load_json(ROOT/'taxonomy.json')}
 docs={d['problem_id']:d for d in read_jsonl(ROOT/'corpus_sources.jsonl')}
 reviews=read_reviews(docs)
 additional_review_hashes={}
 for path in additional_review_files:
  path=Path(path).resolve()
  additional_review_hashes[path.relative_to(ROOT).as_posix()]=fingerprint(path)
  for pid,entries in read_reviews(docs,path).items():reviews.setdefault(pid,[]).extend(entries)
 supplemental=read_jsonl(ROOT/'precision_sources.jsonl') if (ROOT/'precision_sources.jsonl').exists() else []
 supplemental_hash=fingerprint(ROOT/'precision_sources.jsonl') if (ROOT/'precision_sources.jsonl').exists() else None
 supplements={}
 for item in supplemental:
  assert item['problem_id'] in item['editorial']['task_ids'],'Mismatched supplemental editorial'
  supplements.setdefault(item['problem_id'],[]).append(item['editorial'])
 review_hash=fingerprint(ROOT/'precision_reviews.tsv') if (ROOT/'precision_reviews.tsv').exists() else None
 config=load_json(ROOT/'tag_rules.json')['aliases']
 for t,aliases in EXTRA_ALIASES.items():config[t]=sorted(set(config.get(t,[])+aliases))
 rules={t:[(a,alias_regex(a)) for a in aa] for t,aa in config.items()}
 shared=shared_body_keys(docs)
 pairs=[];rows=[];records=[];matrix=[];reviewed_matrix=[];audits=[];rejections=[];changes=[];counts=Counter();methods=Counter()
 baseline={d['problem_id']:d for d in read_jsonl(ROOT/baseline_dir/'problems_tagged.jsonl')}
 for position,p in enumerate(manifest['problems']):
  if position%500==0:print(json.dumps(dict(processed=position,total=manifest['problem_count'])),flush=True)
  pid=p['problem_id'];doc=docs[pid];labels={};rejected=[]
  def add(tid,e):
   assert tid in taxonomy,tid
   if e not in labels.setdefault(tid,[]):labels[tid].append(e)
  refreshed={e['url']:e for e in supplements.get(pid,[])}
  effective=[refreshed.pop(e.get('url'),e) for e in doc['editorials']]
  effective.extend(refreshed.values())
  for e in effective:
   key=(e.get('url',''),hashlib.sha256(e['text'].encode()).hexdigest())
   exact_pdf=e.get('source','').startswith('official_pdf_') and e['text'].splitlines()[0].strip()==p['title'].strip()
   if key in shared and not exact_pdf:
    audits.append(dict(problem_id=pid,url=e.get('url',''),reason='shared_unsegmented_editorial',context=e['text'][:220],excluded_chars=len(e['text'])))
    continue
   text,codes,audit=scoped_editorial(e,shared,p)
   audits.extend(dict(problem_id=pid,**a) for a in audit)
   found,excluded=named_evidence_v3(text,rules)
   for hit in found:add(hit['tag_id'],dict(method='editorial_name_rule_v3',role='unresolved',validation_status='not_reviewed',url=e.get('url',''),source=e.get('source',''),matched=hit['matched'],context=hit['context']))
   rejected.extend(dict(h,url=e.get('url','')) for h in excluded)
   code=clean_code('\n'.join(codes))
   for tid,pattern in CODE_RULES.items():
    m=re.search(pattern,code)
    if m:add(tid,dict(method='editorial_code_rule_v3',role='unresolved',validation_status='not_reviewed',url=e.get('url',''),source=e.get('source',''),matched=m.group(),context=code[max(0,m.start()-50):m.end()+90]))
   text=normalize(text)
   for tid,pattern in DESCRIPTION_RULES.items():
    for m in re.finditer(pattern,text):
     context=local_context(text,m.start(),m.end());reason=description_rejection(tid,context,m.group())
     hit=dict(tag_id=tid,matched=m.group(),context=context,url=e.get('url',''))
     if reason:rejected.append(dict(hit,reason=reason))
     else:add(tid,dict(method='solution_description_rule_v3',role='unresolved',validation_status='not_reviewed',url=e.get('url',''),source=e.get('source',''),matched=m.group(),context=context))
  if not labels and p['problem_index'] in {'A','B'}:
   question=normalize(doc['statement']).split('制約')[0].split('入力例')[0]
   if '文字列' in question and re.search(r'取り除|除い|置き換|置換|連結|反転|文字数|文字目|先頭|末尾|辞書順|大文字|小文字|母音|回文|部分文字列',question):
    add('T073',dict(method='elementary_string_task_rule',role='concept',validation_status='not_reviewed',url=p['url'],matched='elementary string manipulation'))
  automatic=set(labels);reviewed_tags=set();full_review=False;gaps=[]
  for review in reviews.get(pid,[]):
   if review['scope']=='full':
    full_review=True
    for tid in set(labels)-set(review['accepted']):rejected.append(dict(tag_id=tid,reason='semantic_review_not_supported',context=review['reason'],url=' | '.join(review['evidence_urls'])))
    labels={}
   for tid in review['rejected']:
    labels.pop(tid,None)
    rejected.append(dict(tag_id=tid,reason='semantic_review_rejected',context=review['reason'],url=' | '.join(review['evidence_urls'])))
   for tid,role in review['accepted'].items():
    # Replace the evidence for the same tag: provisional hits must not masquerade as reviewed.
    labels[tid]=[]
    add(tid,dict(method='assistant_semantic_review_v3',role=role,validation_status='assistant_reviewed',url=' | '.join(review['evidence_urls']),context=review['evidence_quote'],note=review['reason'],evidence_sha256=review['evidence_sha256'],independent_human_review=False))
    reviewed_tags.add(tid)
   if review['out_of_vocabulary']:gaps.extend(review['out_of_vocabulary'].split(','))
  tids=sorted(labels);reviewed_tags.intersection_update(tids)
  status=('assistant_reviewed' if tids else 'assistant_reviewed_no_matching_tag') if full_review else ('partially_assistant_reviewed' if pid in reviews else ('provisional_tagged' if tids else 'unresolved_no_supported_tag'))
  for tid in tids:
   es=labels[tid];counts[tid]+=1
   methods.update({e['method'] for e in es})
   reviewed=tid in reviewed_tags
   pairs.append(dict(tag=taxonomy[tid],problem_id=pid,title=p['problem_index']+' - '+p['title'],difficulty=p['difficulty'] if p['difficulty'] is not None else '',diff_band='unknown' if p['difficulty'] is None else '0-1999' if p['difficulty']<2000 else '2000+',url=p['url'],tag_id=tid,related=1,labeling_method=' | '.join(sorted({e['method'] for e in es})),role=' | '.join(sorted({e['role'] for e in es})),validation_status='assistant_reviewed' if reviewed else 'not_independently_reviewed',needs_review=0 if reviewed else 1,evidence_urls=' | '.join(sorted({e['url'] for e in es if e.get('url')})),tagging_version=version))
  row=dict(problem_id=pid,contest_id=p['contest_id'],problem_index=p['problem_index'],title=p['title'],difficulty=p['difficulty'] if p['difficulty'] is not None else '',url=p['url'],tag_ids=' | '.join(tids),tags=' | '.join(taxonomy[t] for t in tids),tag_count=len(tids),tagging_status=status,editorial_count=len(doc['editorials']),has_prior_tags=0,tagging_version=version,review_scope='full' if full_review else 'selected_tags' if pid in reviews else 'none',reviewed_tag_count=len(reviewed_tags),out_of_vocabulary=' | '.join(sorted(set(gaps))))
  rows.append(row);matrix.append(dict(problem_id=pid,**{t:int(t in tids) for t in taxonomy}));reviewed_matrix.append(dict(problem_id=pid,**{t:int(t in reviewed_tags) for t in taxonomy}))
  records.append(dict(p,statement=doc['statement'],statement_source=doc['source_url'],statement_sha256=doc['statement_sha256'],editorials=doc['editorials'],additional_editorials=supplements.get(pid,[]),tag_ids=tids,tags=[taxonomy[t] for t in tids],tagging_status=status,labels=labels,rejected_name_hits=rejected,tagging_version=version,review_scope=row['review_scope'],reviews=reviews.get(pid,[]),independent_human_review=False))
  for tid in sorted(set(baseline[pid]['tag_ids'])^set(tids)):
   changes.append(dict(problem_id=pid,tag_id=tid,tag=taxonomy[tid],action='add' if tid in tids else 'remove',review_scope=row['review_scope'],reason=' | '.join(r['reason'] for r in reviews.get(pid,[])) or 'V3 scoped evidence rules; removal is not a confirmed semantic false positive.'))
  rejections.extend(dict(problem_id=pid,**h) for h in rejected)
 out=ROOT/output;out.mkdir(parents=True,exist_ok=True)
 csv_write(out/'problems.csv',list(rows[0]),rows)
 csv_write(out/'all_problems_tagged.csv',list(pairs[0]),pairs)
 csv_write(out/'problem_tag_matrix.csv',['problem_id',*taxonomy],matrix)
 csv_write(out/'reviewed_problem_tag_matrix.csv',['problem_id',*taxonomy],reviewed_matrix)
 csv_write(out/'reviewed_assignments.csv',list(pairs[0]),[p for p in pairs if p['validation_status']=='assistant_reviewed'])
 csv_write(out/'tag_catalog.csv',['tag_id','tag','problem_count'],[dict(tag_id=t,tag=n,problem_count=counts[t]) for t,n in taxonomy.items()])
 csv_write(out/'unresolved_problems.csv',list(rows[0]),[r for r in rows if r['tagging_status'].startswith('unresolved_')])
 csv_write(out/'review_queue.csv',list(rows[0])+['priority','review_reason'],[dict(r,priority=0 if r['review_scope']=='none' and r['tag_count']==0 and r['problem_index'] not in {'A','B'} else 1 if r['tag_count']>=5 else 2,review_reason='Unreviewed/partially reviewed; absence of a tag is not a negative label.') for r in rows if r['review_scope']!='full'])
 csv_write(out/'change_audit.csv',['problem_id','tag_id','tag','action','review_scope','reason'],changes)
 csv_write(out/'source_scope_audit.csv',['problem_id','reason','url','context','note','excluded_chars'],audits)
 csv_write(out/'rejected_evidence.csv',['problem_id','tag_id','matched','reason','context','url','start','end','specific_tag_id'],rejections)
 with (out/'problems_tagged.jsonl').open('w',encoding='utf-8') as f:
  for record in records:f.write(json.dumps(record,ensure_ascii=False)+'\n')
 save_json(out/'semantic_reviews.json',reviews)
 summary=dict(version=version,as_of=manifest['as_of'],review_date='2026-11-23',problem_count=len(rows),contest_count=manifest['contest_count'],taxonomy_count=len(taxonomy),tagged_problem_count=sum(r['tag_count']>0 for r in rows),unresolved_problem_count=sum(r['tagging_status'].startswith('unresolved_') for r in rows),untagged_problem_count=sum(r['tag_count']==0 for r in rows),no_matching_tag_after_review_count=sum(r['tagging_status']=='assistant_reviewed_no_matching_tag' for r in rows),assigned_pairs=len(pairs),used_tags=len(counts),unused_tags=266-len(counts),assistant_semantic_reviewed_problems=len(reviews),fully_reviewed_problems=sum(r['review_scope']=='full' for r in rows),partially_reviewed_problems=sum(r['review_scope']=='selected_tags' for r in rows),reviewed_assignments=sum(p['validation_status']=='assistant_reviewed' for p in pairs),method_pair_counts=dict(methods),paid_api_calls=0,independent_human_review=False,annotation_policy='scoped_automatic_with_explicit_semantic_reviews',evidence_scope_policy=POLICY_VERSION,source_corpus_sha256=fingerprint(ROOT/'corpus_sources.jsonl'),taxonomy_sha256=fingerprint(ROOT/'taxonomy.json'),review_file_sha256=review_hash,supplemental_sources_sha256=supplemental_hash,supplemental_source_rows=len(supplemental),baseline_directory=baseline_dir,additional_review_files_sha256=additional_review_hashes,changed_problems=len({r['problem_id'] for r in changes}),added_pairs=sum(r['action']=='add' for r in changes),removed_pairs=sum(r['action']=='remove' for r in changes),scoped_source_exclusions=len(audits),accuracy_estimate=None,accuracy_note='No independent gold labels or random-sample evaluation. Counts and consistency checks are not an accuracy estimate.')
 save_json(out/'summary.json',summary)
 save_json(out/'policy.json',dict(extra_aliases=EXTRA_ALIASES,description_rules=DESCRIPTION_RULES,code_rules=CODE_RULES,source_policy=POLICY_VERSION))
 print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output-dir',default='output_v3');parser.add_argument('--additional-review-file',action='append',default=[]);parser.add_argument('--baseline-dir',default='output_v2_uniform');parser.add_argument('--version',default=VERSION);a=parser.parse_args();build(a.output_dir,a.additional_review_file,a.baseline_dir,a.version)

