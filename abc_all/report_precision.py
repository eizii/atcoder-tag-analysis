"""Summarize V3 evidence and expose a prioritized remaining review queue."""
import csv,json
from collections import Counter
from pathlib import Path
from tag_all import csv_write
R=Path(__file__).resolve().parent

def main():
 out=R/'output_v3';summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
 with (out/'problems.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 with (out/'review_queue.csv').open(encoding='utf-8-sig') as f:queue=list(csv.DictReader(f))
 catalog=list(csv.DictReader((out/'tag_catalog.csv').open(encoding='utf-8-sig')))
 rare={r['tag_id'] for r in catalog if 0<int(r['problem_count'])<=3}
 for row in queue:
  tags=set(row['tag_ids'].split(' | ')) if row['tag_ids'] else set()
  reasons=[]
  if not tags and row['problem_index'] not in {'A','B'}:reasons.append('No supported tag for a C-or-harder problem')
  if tags&rare:reasons.append('Contains a tag observed on at most three problems')
  if int(row['tag_count'])>=5:reasons.append('Many labels; review possible background and auxiliary tags')
  if row['review_scope']=='selected_tags':reasons.append('Only selected tags have been reviewed')
  row['priority']=0 if not tags and row['problem_index'] not in {'A','B'} else 1 if tags&rare or int(row['tag_count'])>=5 else 2
  row['review_reason']=' | '.join(reasons) or 'Automatic labels or untagged A/B problem awaiting semantic review'
 queue.sort(key=lambda r:(int(r['priority']),-int(r['tag_count']),r['problem_id']))
 csv_write(out/'review_queue.csv',list(queue[0]),queue)
 gaps=[]
 for row in rows:
  for term in row['out_of_vocabulary'].split(' | '):
   if term:gaps.append(dict(problem_id=row['problem_id'],term=term,review_scope=row['review_scope'],note='Vocabulary gap for the reviewed solution; not a new tag ID.'))
 csv_write(out/'vocabulary_gaps.csv',['problem_id','term','review_scope','note'],gaps)
 fetch=json.loads((R/'precision_fetch_report.json').read_text(encoding='utf-8'))
 source_audit=list(csv.DictReader((out/'source_scope_audit.csv').open(encoding='utf-8-sig')))
 rejected=list(csv.DictReader((out/'rejected_evidence.csv').open(encoding='utf-8-sig')))
 current={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))}
 supplements=list(map(json.loads,(R/'precision_sources.jsonl').open(encoding='utf-8')))
 gain=[]
 for item in supplements:
  e=item['editorial'];old=next((a for a in current[item['problem_id']]['editorials'] if a.get('url')==e['url']),None)
  if old and len(e['text'])-len(old['text'])>=100:
   gain.append(dict(problem_id=item['problem_id'],url=e['url'],old_chars=len(old['text']),new_chars=len(e['text']),added_chars=len(e['text'])-len(old['text'])))
 csv_write(out/'source_recovery_audit.csv',['problem_id','url','old_chars','new_chars','added_chars'],gain)
 stats=dict(source_exclusion_reasons=dict(Counter(r['reason'] for r in source_audit)),evidence_rejection_reasons=dict(Counter(r['reason'] for r in rejected)),review_status_counts=dict(Counter(r['tagging_status'] for r in rows)),refetched_urls=fetch['requested_urls'],accepted_supplemental_sources=len(supplements),supplemental_source_mismatches=len(fetch['errors']),sources_with_at_least_100_recovered_characters=len(gain),review_queue_size=len(queue),vocabulary_gap_terms=dict(Counter(r['term'] for r in gaps)))
 (out/'quality_audit.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(stats,ensure_ascii=False))
if __name__=='__main__':main()
