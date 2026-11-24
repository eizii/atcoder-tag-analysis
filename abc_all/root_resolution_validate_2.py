import csv,json,re,hashlib
from pathlib import Path
R=Path('abc_all');p=R/'full_review/root_resolution_2.tsv';rows=list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter='\t'));fields=list(rows[0]);D={x['problem_id']:x for x in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf8'))};Q=list(csv.DictReader((R/'full_review/resolution_queue_agent_2.tsv').open(encoding='utf-8-sig'),delimiter='\t'));T={x['tag_id'] for x in json.loads((R/'taxonomy.json').read_text(encoding='utf8'))}
for r in rows:
 if r['problem_id']=='abc482_g':r['accepted']=r['accepted'].replace(',T118:concept','').replace(',T265:analysis_concept','');r['rejected']='T118'
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fields,delimiter='\t');w.writeheader();w.writerows(rows)
assert len(rows)==85==len({x['problem_id'] for x in rows})
assert [x['problem_id'] for x in rows]==[x['problem_id'] for x in Q]
for r in rows:
 d=D[r['problem_id']];src=d['statement'] if r['source_indices']=='statement' else d['editorials'][int(r['source_indices'])]['text'];assert r['evidence_quote'] in re.sub(r'\s+',' ',src),r['problem_id'];assert r['review_status']=='reviewed' and r['scope']=='full' and not r['uncertainty'];assert len(r['reason'])>20
 for item in r['accepted'].split(',') if r['accepted'] else []:
  tag,role=item.split(':');assert tag in T and role in ['primary','alternative','supporting','concept','analysis_concept']
report={'assigned':85,'saved':85,'status':'complete','quotes_match':True,'ids_exactly_match_assigned_queue':True,'all_full_reviewed':True,'taxonomy_roles_valid':True,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'notes':['Read problem statements, all available original editorial bodies, and code for cases whose algorithm or boundary handling required it.','Main methods and feasible confirmed alternatives are recorded; speculative references and known hackable alternatives are not promoted to accepted methods.','Source typos corrected explicitly in reasons: abc459_c k update, abc470_g count factor, abc478_f root sentinel.']};(R/'full_review/root_resolution_2_checkpoint.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report))
base={r['problem_id']:r for r in csv.DictReader((R/'output_v3_2/problems.csv').open(encoding='utf-8-sig'))};allrows=list(csv.DictReader((R/'full_review/shard_2.tsv').open(encoding='utf-8-sig'),delimiter='\t'))+rows;out=[]
for r in allrows:
 acc=dict(x.split(':') for x in r['accepted'].split(',') if x);old=set(base[r['problem_id']]['tag_ids'].split(' | '))
 for tag in ['T029','T026']:
  if tag in acc or tag in old:out.append({'problem_id':r['problem_id'],'tag_id':tag,'role':acc.get(tag,''),'decision':'accepted' if tag in acc else 'removed','previously_present':tag in old,'reason':r['reason']})
with (R/'full_review/shard_2_probability_expectation_summary.tsv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,list(out[0]),delimiter='\t');w.writeheader();w.writerows(out)
print(json.dumps({'dp_summary_rows':len(out),'adopted_T029':sum(r['tag_id']=='T029' and r['decision']=='accepted' for r in out),'adopted_T026':sum(r['tag_id']=='T026' and r['decision']=='accepted' for r in out),'removed':[r['problem_id']+':'+r['tag_id'] for r in out if r['decision']=='removed']},ensure_ascii=False))
