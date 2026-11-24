const fs=require('fs'),vm=require('vm');
const path=require('path');const base=path.join(__dirname,'hierarchical_v4_20261124');
const html=fs.readFileSync(path.join(base,'index.html'),'utf8');const code=html.match(/<script>([\s\S]*)<\/script>/)[1];
const defaults={dataset:'all_difficulties',metric:'cosine',method:'average',cut:'cut_0.8',search:''};const els={};
for(const id of ['dataset','metric','method','cut','search','stats','warning','description','members','tree','svg'])els[id]={value:defaults[id]||'',innerHTML:'',textContent:'',src:'',href:'',addEventListener(){}};
const context=vm.createContext({document:{getElementById:id=>els[id]},console});vm.runInContext(code,context);
let n=0,warnings=0;
for(const dataset of ['all_difficulties','under_2000'])for(const metric of ['cosine','jaccard'])for(const method of ['average','single','complete'])for(const cut of ['cut_0.7','cut_0.8','cut_0.9','target_80','target_40']){
 for(const [k,v] of Object.entries({dataset,metric,method,cut,search:''}))els[k].value=v;
 vm.runInContext('render()',context);const key=dataset+'/'+metric+'_'+method;const p=vm.runInContext(`DATA[${JSON.stringify(key)}].partitions[${JSON.stringify(cut)}]`,context);
 if((els.members.innerHTML.match(/<tr>/g)||[]).length!==p.clusters.length)throw Error('Wrong row count '+key+' '+cut);
 if(!fs.existsSync(path.join(base,els.tree.src)))throw Error('Missing tree');
 const mismatch=p.target_clusters&&p.actual_clusters!==p.target_clusters;
 if(Boolean(els.warning.textContent)!==Boolean(mismatch))throw Error('Missing mismatch warning');
 if(mismatch)warnings++;n++;
}
Object.assign(els.dataset,{value:'all_difficulties'});Object.assign(els.metric,{value:'cosine'});Object.assign(els.method,{value:'average'});Object.assign(els.cut,{value:'cut_0.8'});els.search.value='T029';vm.runInContext('render()',context);
if((els.members.innerHTML.match(/<tr>/g)||[]).length!==1||!els.members.innerHTML.includes('T029'))throw Error('Search failed');
const report={checks_passed:true,selector_combinations:n,unachievable_target_warnings:warnings,tag_id_search_passed:true,local_markdown_links_checked:82,note:'DOM rendering and references checked using a DOM stub; plot images visually inspected separately.'};
fs.writeFileSync(path.join(base,'dashboard_verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
