import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
function parseCsv(text) {
  const rows=[]; let row=[],field='',quoted=false;
  text=text.replace(/^\uFEFF/,'');
  for(let i=0;i<text.length;i++) {
    const c=text[i];
    if(c==='"') { if(quoted&&text[i+1]==='"'){field+='"';i++;}else quoted=!quoted; }
    else if(c===','&&!quoted){row.push(field);field='';}
    else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(field);if(row.some(x=>x!==''))rows.push(row);row=[];field='';}
    else field+=c;
  }
  if(quoted)throw new Error('Unclosed CSV quote');
  if(field||row.length){row.push(field);rows.push(row);}
  return rows;
}
function encodeCsv(rows) {
  return '\uFEFF'+rows.map(row=>row.map(value=>{
    const s=String(value??'');
    return /[",\r\n]/.test(s)?'"'+s.replaceAll('"','""')+'"':s;
  }).join(',')).join('\r\n')+'\r\n';
}
const data=JSON.parse(await fs.readFile(path.join(root,'tagging_data.json'),'utf8'));
const input=await fs.readFile(path.join(root,'all_problems.csv'));
const tagsInput=await fs.readFile(path.join(root,'tags.md'));
for(const [buf,key] of [[input,'all_problems_csv'],[tagsInput,'tags_md']]){
  if(crypto.createHash('sha256').update(buf).digest('hex')!==data.input_sha256[key])throw new Error('Input changed: '+key);
}
const taxonomy=[...tagsInput.toString('utf8').matchAll(/^([0-9]+)\. (.+)$/gm)]
  .map(m=>({id:Number(m[1]),tag:m[2].trim()}));
if(taxonomy.length!==266||new Set(taxonomy.map(t=>t.id)).size!==266||new Set(taxonomy.map(t=>t.tag)).size!==266)throw new Error('Taxonomy must have 266 unique tags');
const tmap=new Map(taxonomy.map(t=>[t.id,t]));
const rows=parseCsv(input.toString('utf8')),header=rows.shift();
if(header.join(',')!=='tag,problem_id,title,difficulty,diff_band,url')throw new Error('Unexpected CSV schema');
const problems=new Map();
for(const row of rows){
  if(row.length!==header.length)throw new Error('CSV width mismatch');
  const p=Object.fromEntries(header.map((h,i)=>[h,row[i]]));
  if(!(p.tag in data.aliases))throw new Error('Unmapped tag '+p.tag);
  if(!problems.has(p.problem_id))problems.set(p.problem_id,{...p,oldTags:[],labels:new Map()});
  const existing=problems.get(p.problem_id);
  for(const h of header.filter(h=>h!=='tag'))if(existing[h]!==p[h])throw new Error('Conflicting metadata '+p.problem_id+' '+h);
  existing.oldTags.push(p.tag);
}
const fmap=new Map(data.features.map(f=>[f.problem_id,f]));
const missing=new Set(data.retrieval_errors.map(e=>e.problem_id));
const audit=[];
function add(p,id,method,note,needsReview=0) {
  if(!tmap.has(id))throw new Error('Invalid tag ID '+id+' '+p.problem_id);
  const prior=p.labels.get(id);
  if(prior) {
    if(!prior.methods.includes(method))prior.methods.push(method);
    if(note&&!prior.notes.includes(note))prior.notes.push(note);
    prior.needsReview=Math.max(prior.needsReview,needsReview);
  } else p.labels.set(id,{id,methods:[method],notes:note?[note]:[],needsReview});
}
const specializedDP=new Set([17,19,20,21,23,24,25,26,27,28,29,147,150,151,191,262,263]);
function specialize(p,parent,children,note) {
  if(!p.labels.has(parent)||!children.some(id=>p.labels.has(id)))return;
  p.labels.delete(parent);
  audit.push([p.problem_id,p.title,'granularity_refinement',tmap.get(parent).tag,
    children.filter(id=>p.labels.has(id)).map(id=>tmap.get(id).tag).join(' | '),note,fmap.get(p.problem_id)?.editorial_url??'',0]);
}
for(const p of problems.values()) {
  const f=fmap.get(p.problem_id);
  for(const oldTag of p.oldTags){
    const id=data.aliases[oldTag];
    if(id===null){
      audit.push([p.problem_id,p.title,'out_of_vocabulary',oldTag,'','266項目に貪欲法がないため、別のアルゴリズムへ置換しない。元タグはoriginal_tagsに保存。',f?.editorial_url??'',1]);
      continue;
    }
    const semantic=oldTag==='gcd'||oldTag==='部分列DP';
    const note=oldTag==='gcd'?'gcdは最大公約数の操作名。Euclidとの対応は意味上の推定であり同義語ではない。':
      oldTag==='部分列DP'?'文字列を扱う2問の部分列DPを文字列DPに対応付け。':
      '元CSVのタグをtags.mdの266項目に正規化。';
    add(p,id,'original_tag',note,missing.has(p.problem_id)||semantic?1:0);
    if(semantic&&oldTag==='gcd')audit.push([p.problem_id,p.title,'semantic_mapping',oldTag,tmap.get(id).tag,note,f?.editorial_url??'',1]);
  }
  if(f)for(const id of f.automatic_tag_ids){
    add(p,id,'editorial_rule','公式解説の解法本文または実装で名前を検出。主解・別解の優劣は未評価。');
  }
  for(const [id,note] of data.manual_adds[p.problem_id]??[]){
    add(p,id,'editorial_reasoning',note,missing.has(p.problem_id)?1:0);
  }
  for(const id of data.corrections[p.problem_id]?.remove??[]){
    p.labels.delete(id);
    audit.push([p.problem_id,p.title,'corrected_original_tag',tmap.get(id).tag,
      (data.manual_adds[p.problem_id]??[]).map(([i])=>tmap.get(i).tag).join(' | '),
      data.corrections[p.problem_id].note,f?.editorial_url??'',0]);
  }
  specialize(p,22,[...specializedDP],'基礎DPより具体的なDPの種類が確認できたため細分化。');
  specialize(p,66,[144],'0-1 BFSを一般的な幅優先探索から分離。');
  specialize(p,3,[2],'遅延評価を伴うセグメント木として細分化。');
  specialize(p,4,[95],'Disjoint Sparse Tableとして細分化。');
  specialize(p,70,[89],'Binary Trieとして細分化。');
  specialize(p,53,[233,234],'具体的な全域木アルゴリズム名に細分化。');
  specialize(p,54,[225,226,227],'LCAの具体的な求め方に細分化。');
  if(missing.has(p.problem_id)){
    audit.push([p.problem_id,p.title,'editorial_unavailable',p.oldTags.join(' | '),'',
      '公式解説を取得できなかったため既存タグと既知解法に基づく暫定分類。取得制限・キャッシュ未収録等。',
      '',1]);
    for(const label of p.labels.values())label.needsReview=1;
  }
  if(!p.labels.size)throw new Error('Problem without labels '+p.problem_id);
}
const longHeader=['tag','problem_id','title','difficulty','diff_band','url','tag_id','related','labeling_method','original_tags','editorial_url','needs_review','note'];
const longRows=[longHeader],matrix=[['problem_id',...taxonomy.map(t=>t.tag)]];
const counts=new Map(taxonomy.map(t=>[t.id,0]));
let inheritedOnly=0,addedPairs=0,refinedProblems=0;
for(const p of problems.values()){
  const originally=new Set(p.oldTags.map(t=>data.aliases[t]).filter(id=>id!==null));
  let changed=false,onlyInherited=true;
  for(const label of [...p.labels.values()].sort((a,b)=>a.id-b.id)){
    counts.set(label.id,counts.get(label.id)+1);
    if(!originally.has(label.id)){addedPairs++;changed=true;}
    if(label.methods.some(m=>m!=='original_tag'))onlyInherited=false;
    longRows.push([tmap.get(label.id).tag,p.problem_id,p.title,p.difficulty,p.diff_band,p.url,
      'T'+String(label.id).padStart(3,'0'),1,label.methods.join(' | '),p.oldTags.join(' | '),
      fmap.get(p.problem_id)?.editorial_url??'',label.needsReview,label.notes.join(' ')]);
  }
  if([...originally].some(id=>!p.labels.has(id)))changed=true;
  if(changed)refinedProblems++;
  if(onlyInherited)inheritedOnly++;
  matrix.push([p.problem_id,...taxonomy.map(t=>p.labels.has(t.id)?1:0)]);
}
const catalog=[['tag_id','tag','problem_count','original_number'],
  ...taxonomy.map(t=>['T'+String(t.id).padStart(3,'0'),t.tag,counts.get(t.id),t.id])];
const review=[['problem_id','title','review_type','old_tag','new_tags','reason','editorial_url','needs_review'],...audit];
const files={
'all_problems_tagged.csv':longRows,
'problem_tag_matrix.csv':matrix,
'tag_catalog.csv':catalog,
'tagging_review.csv':review
};
for(const [name,table] of Object.entries(files)){
  const encoded=encodeCsv(table),decoded=parseCsv(encoded);
  if(JSON.stringify(decoded)!==JSON.stringify(table.map(r=>r.map(v=>String(v??'')))))throw new Error('CSV roundtrip mismatch '+name);
  await fs.writeFile(path.join(root,name),encoded,'utf8');
}
const matrixNonzero=matrix.slice(1).reduce((s,r)=>s+r.slice(1).reduce((a,b)=>a+b,0),0);
const pairs=longRows.slice(1).map(r=>r[1]+'\t'+r[6]);
if(new Set(pairs).size!==pairs.length||matrixNonzero!==longRows.length-1)throw new Error('Long/matrix mismatch');
for(let i=0;i<taxonomy.length;i++){
  const total=matrix.slice(1).reduce((s,r)=>s+r[i+1],0);
  if(total!==counts.get(taxonomy[i].id))throw new Error('Catalog mismatch');
}
const summary={
  date:data.date,input_rows:rows.length,problem_count:problems.size,taxonomy_count:taxonomy.length,
  assigned_pairs:longRows.length-1,used_tags:[...counts.values()].filter(n=>n>0).length,
  unused_tags:[...counts.values()].filter(n=>n===0).length,
  editorial_text_available:fmap.size,editorial_text_unavailable:missing.size,
  added_pairs:addedPairs,refined_problems:refinedProblems,
  manual_reasoning_problems:Object.keys(data.manual_adds).length,
  inherited_only_problems:inheritedOnly,
  audit_rows:audit.length,
  pending_review_rows:audit.filter(r=>r[7]===1).length,
  needs_review_pairs:longRows.slice(1).filter(r=>r[11]===1).length,
  input_sha256:data.input_sha256,
  checks:['unique_problem_ids','input_metadata_consistency','taxonomy_membership','no_duplicate_pairs','all_problems_labeled','csv_roundtrip','matrix_long_reconciliation','catalog_frequency_reconciliation','input_hash_preservation']
};
await fs.writeFile(path.join(root,'tagging_summary.json'),JSON.stringify(summary,null,2)+'\n','utf8');
const byTag=['# タグ別の問題一覧','',
  'tags.md末尾の266項目を使用。★は要確認を含む付与。自動推定・元タグ継承を含むため、必要度や最適度の確定評価ではありません。','',
  '[付与方法・行列の使い方](tagging_notes.md) / [問題とタグのCSV](all_problems_tagged.csv) / [確認事項](tagging_review.csv)',''];
for(const t of taxonomy){
  byTag.push('## T'+String(t.id).padStart(3,'0')+' '+t.tag+'（'+counts.get(t.id)+'問）','');
  if(!counts.get(t.id)){byTag.push('今回のデータでは付与なし。','');continue;}
  for(const p of problems.values())if(p.labels.has(t.id)){
    const label=p.labels.get(t.id);
    byTag.push('- '+(label.needsReview?'★ ':'')+'['+p.problem_id+' '+p.title.replaceAll('[','\\[').replaceAll(']','\\]')+']('+p.url+')');
  }
  byTag.push('');
}
await fs.writeFile(path.join(root,'tags_with_problems.md'),byTag.join('\n')+'\n','utf8');
console.log(JSON.stringify(summary,null,2));
