"""Build a release solely from completed, per-problem semantic decisions.

The main dataset contains feasible primary, alternative and supporting methods.
Concepts used only in explanations are preserved in separate outputs.
"""
import csv,hashlib,json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from tag_all import normalize,csv_write
R=Path(__file__).resolve().parent.parent;W=R/'full_review'
ROLES={'primary','alternative','supporting'}
CONCEPTS={'concept','analysis_concept'}
DATE='2026-11-24';VERSION='abc-all-266-semantic-v4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''),delimiter='\t'))
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def merge():
 manifest=json.loads((R/'manifest.json').read_text(encoding='utf-8'))
 docs={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))}
 taxonomy={t['tag_id']:t['tag'] for t in json.loads((R/'taxonomy.json').read_text(encoding='utf-8'))}
 files=[*(W/f'shard_{i}.tsv' for i in range(4)),*(W/f'root_resolution_{i}.tsv' for i in ('root','0','2'))]
 by={};seen=set();hashes={}
 for f in files:
  assert f.exists(),f
  hashes[f.name]=sha(f);local=set()
  for r in read(f):
   pid=r['problem_id'];assert pid in docs and pid not in local,(f.name,pid)
   local.add(pid)
   if f.name.startswith('shard_'):
    assert pid not in seen,(f.name,pid)
    seen.add(pid)
   else:assert pid in by,(f.name,pid,'override without base')
   by[pid]=r
 assert set(by)=={p['problem_id'] for p in manifest['problems']},'Incomplete problem coverage'
 for pid,r in by.items():
  assert r.get('review_status','reviewed')=='reviewed' and r['scope']=='full',(pid,'incomplete review')
  d=docs[pid];s=r['source_indices']
  indices=[] if s=='statement' else [i for i,e in enumerate(d['editorials']) if normalize(r['evidence_quote']) in normalize(e['text'])] if s=='match' else list(map(int,s.split(',')))
  text='\n'.join(d['editorials'][i]['text'] for i in indices) if indices else d['statement']
  assert len(r['evidence_quote'])>=10 and normalize(r['evidence_quote']) in normalize(text),(pid,'quote')
  accepted={}
  for a in filter(None,r['accepted'].split(',')):
   t,role=a.split(':');assert t in taxonomy and role in ROLES|CONCEPTS and t not in accepted,(pid,a)
   accepted[t]=role
  assert len(r['reason'])>=10,(pid,'reason')
  r['review_date']=DATE;r['source_indices']=','.join(map(str,indices)) if indices else 'statement'
 fields=list(next(iter(by.values())))
 with (W/'merged_full_reviews.tsv').open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=fields,delimiter='\t',extrasaction='ignore');writer.writeheader();writer.writerows(by[p['problem_id']] for p in manifest['problems'])
 return manifest,docs,taxonomy,by,hashes

def build():
 manifest,docs,taxonomy,by,hashes=merge();out=R/'output_v4';out.mkdir(exist_ok=True)
 old={d['problem_id']:d for d in map(json.loads,(R/'output_v3_2/problems_tagged.jsonl').open(encoding='utf-8'))}
 supplements={}
 for d in map(json.loads,(R/'precision_sources.jsonl').open(encoding='utf-8')):supplements.setdefault(d['problem_id'],[]).append(d['editorial'])
 rows=[];pairs=[];analysis=[];records=[];matrix=[];amatrix=[];allmatrix=[];changes=[];reviews={};counts=Counter();rolecounts=Counter()
 for p in manifest['problems']:
  pid=p['problem_id'];r=by[pid];d=docs[pid]
  accepted=dict(a.split(':') for a in filter(None,r['accepted'].split(',')))
  indices=[] if r['source_indices']=='statement' else list(map(int,r['source_indices'].split(',')))
  source='\n'.join(d['editorials'][i]['text'] for i in indices) if indices else d['statement']
  urls=sorted({d['editorials'][i].get('url') or p['url'] for i in indices}) if indices else [p['url']]
  review=dict(r,accepted=accepted,rejected=[],evidence_urls=urls,evidence_sha256=hashlib.sha256(source.encode()).hexdigest(),reviewer='assistant',independent_human_review=False)
  reviews[pid]=[review];labels={};alabels={}
  for t,role in accepted.items():
   evidence=dict(method='assistant_semantic_review_v4',role=role,validation_status='assistant_reviewed',url=' | '.join(urls),context=r['evidence_quote'],note=r['reason'],evidence_sha256=review['evidence_sha256'],independent_human_review=False)
   (labels if role in ROLES else alabels)[t]=[evidence]
   pair=dict(tag=taxonomy[t],problem_id=pid,title=p['problem_index']+' - '+p['title'],difficulty=p['difficulty'] if p['difficulty'] is not None else '',diff_band='unknown' if p['difficulty'] is None else '0-1999' if p['difficulty']<2000 else '2000+',url=p['url'],tag_id=t,related=1,labeling_method=evidence['method'],role=role,validation_status='assistant_reviewed',needs_review=0,evidence_urls=' | '.join(urls),tagging_version=VERSION)
   (pairs if role in ROLES else analysis).append(pair);rolecounts[t,role]+=1
   if role in ROLES:counts[t]+=1
  tids=sorted(labels);status='assistant_reviewed' if tids else 'assistant_reviewed_no_matching_tag'
  rows.append(dict(problem_id=pid,contest_id=p['contest_id'],problem_index=p['problem_index'],title=p['title'],difficulty=p['difficulty'] if p['difficulty'] is not None else '',url=p['url'],tag_ids=' | '.join(tids),tags=' | '.join(taxonomy[t] for t in tids),tag_count=len(tids),tagging_status=status,editorial_count=len(d['editorials']),has_prior_tags=0,tagging_version=VERSION,review_scope='full',reviewed_tag_count=len(tids),out_of_vocabulary=r['out_of_vocabulary'],analysis_concept_tag_ids=' | '.join(sorted(alabels))))
  matrix.append(dict(problem_id=pid,**{t:int(t in labels) for t in taxonomy}))
  amatrix.append(dict(problem_id=pid,**{t:int(t in alabels) for t in taxonomy}))
  allmatrix.append(dict(problem_id=pid,**{t:int(t in accepted) for t in taxonomy}))
  records.append(dict(p,statement=d['statement'],statement_source=d['source_url'],statement_sha256=d['statement_sha256'],editorials=d['editorials'],additional_editorials=supplements.get(pid,[]),tag_ids=tids,tags=[taxonomy[t] for t in tids],tagging_status=status,labels=labels,analysis_concept_labels=alabels,rejected_name_hits=[],tagging_version=VERSION,review_scope='full',reviews=[review],independent_human_review=False))
  prior=set(old[pid]['tag_ids']);now=set(tids)
  for t in sorted(prior^now):changes.append(dict(problem_id=pid,tag_id=t,tag=taxonomy[t],action='add' if t in now else 'remove',old_role=' | '.join(sorted({e['role'] for e in old[pid]['labels'].get(t,[])})),new_role=accepted.get(t,''),review_scope='full',reason=r['reason']))
  for t in sorted(prior&now):
   oldroles=sorted({e['role'] for e in old[pid]['labels'].get(t,[])})
   if oldroles!=[accepted[t]]:changes.append(dict(problem_id=pid,tag_id=t,tag=taxonomy[t],action='role_change',old_role=' | '.join(oldroles),new_role=accepted[t],review_scope='full',reason=r['reason']))
 pf=list(pairs[0]);rf=list(rows[0])
 for name,data,fields in [('problems.csv',rows,rf),('all_problems_tagged.csv',pairs,pf),('reviewed_assignments.csv',pairs,pf),('analysis_concept_assignments.csv',analysis,pf),('all_role_assignments.csv',pairs+analysis,pf),('problem_tag_matrix.csv',matrix,['problem_id',*taxonomy]),('reviewed_problem_tag_matrix.csv',matrix,['problem_id',*taxonomy]),('analysis_concept_problem_tag_matrix.csv',amatrix,['problem_id',*taxonomy]),('all_roles_problem_tag_matrix.csv',allmatrix,['problem_id',*taxonomy]),('unresolved_problems.csv',[],rf),('review_queue.csv',[],rf),('change_audit.csv',changes,list(changes[0]))]:csv_write(out/name,fields,data)
 catalog=[dict(tag_id=t,tag=n,problem_count=counts[t],primary_count=rolecounts[t,'primary'],alternative_count=rolecounts[t,'alternative'],supporting_count=rolecounts[t,'supporting'],concept_count=rolecounts[t,'concept'],analysis_concept_count=rolecounts[t,'analysis_concept']) for t,n in taxonomy.items()]
 csv_write(out/'tag_catalog.csv',list(catalog[0]),catalog)
 with (out/'problems_tagged.jsonl').open('w',encoding='utf-8') as f:
  for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 save(out/'semantic_reviews.json',reviews)
 summary=dict(version=VERSION,as_of=manifest['as_of'],review_date=DATE,problem_count=len(rows),contest_count=manifest['contest_count'],taxonomy_count=len(taxonomy),tagged_problem_count=sum(r['tag_count']>0 for r in rows),unresolved_problem_count=0,untagged_problem_count=sum(r['tag_count']==0 for r in rows),no_matching_tag_after_review_count=sum(r['tag_count']==0 for r in rows),assigned_pairs=len(pairs),analysis_concept_pairs=len(analysis),used_tags=len(counts),unused_tags=len(taxonomy)-len(counts),assistant_semantic_reviewed_problems=len(rows),fully_reviewed_problems=len(rows),partially_reviewed_problems=0,reviewed_assignments=len(pairs),paid_api_calls=0,independent_human_review=False,annotation_policy='per_problem_full_semantic_reference_review_with_feasible_alternatives',source_corpus_sha256=sha(R/'corpus_sources.jsonl'),taxonomy_sha256=sha(R/'taxonomy.json'),merged_reviews_sha256=sha(W/'merged_full_reviews.tsv'),input_review_sha256=hashes,supplemental_sources_sha256=sha(R/'precision_sources.jsonl'),baseline_directory='output_v3_2',changed_problems=len({r['problem_id'] for r in changes if r['action']!='role_change'}),added_pairs=sum(r['action']=='add' for r in changes),removed_pairs=sum(r['action']=='remove' for r in changes),role_changes=sum(r['action']=='role_change' for r in changes),accuracy_estimate=None,accuracy_note='No independent gold labels. Full review means all tags of the recorded feasible reference methods were assessed, not all conceivable methods or 266 independent negatives per problem.')
 save(out/'summary.json',summary)
 save(out/'policy.json',dict(main_roles=sorted(ROLES),separate_roles=sorted(CONCEPTS),primary='Technique used in the main full-constraint method',alternative='Confirmed feasible full-constraint alternative',supporting='Technique operationally used by an adopted method',concept='Subject or explanatory concept; not an executed method',analysis_concept='Proof, complexity, or test-construction concept; not an executed method',full_review_scope=summary['accuracy_note'],unadopted_candidates='Recorded in uncertainty and excluded from the accepted tags'))
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':build()
