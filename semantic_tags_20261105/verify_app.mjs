import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { pathToFileURL, fileURLToPath } from "node:url";
const ROOT=path.dirname(fileURLToPath(import.meta.url));
const APP="C:/Users/ejham/theme2026-kaziru";
const require=createRequire(path.join(APP,"package.json"));
const Papa=require("papaparse");
const React=require("react");
const {renderToStaticMarkup}=require("react-dom/server");
const {createServer}=await import(pathToFileURL(require.resolve("vite")).href);
const catalog=JSON.parse(await fs.readFile(path.join(APP,"src/data/tagCatalog.json"),"utf8"));
const topics=JSON.parse(await fs.readFile(path.join(APP,"src/data/problemTopics.json"),"utf8"));
const bytes=await fs.readFile(path.join(APP,"public/all_problems.csv"));
const parsed=Papa.parse(bytes.toString("utf8"),{header:true,skipEmptyLines:true,dynamicTyping:true});
assert.deepEqual(parsed.errors,[]);
assert.deepEqual(parsed.meta.fields,["tag","problem_id","title","difficulty","diff_band","url"]);
const rows=parsed.data.map(r=>({...r,diffCalc:Number(r.difficulty)}));
assert.equal(rows.length,1648);
assert.equal(new Set(rows.map(r=>r.problem_id)).size,898);
assert.equal(new Set(rows.map(r=>JSON.stringify([r.problem_id,r.tag]))).size,rows.length);
assert.ok(rows.every(r=>Number.isFinite(r.diffCalc)&&r.diffCalc<2000));
assert.equal(catalog.classification_method,"semantic_learning_units");
assert.equal(catalog.clusters.length,82);
assert.equal(catalog.visible_unit_count,82);
assert.equal(crypto.createHash("sha256").update(bytes).digest("hex"),catalog.problemCatalogSha256);
const old=Papa.parse(await fs.readFile(path.join(ROOT,"before/all_problems.csv"),"utf8"),{header:true,skipEmptyLines:true,dynamicTyping:true}).data;
const meta=r=>JSON.stringify([r.title,r.difficulty,r.diff_band,r.url]);
const previousById=new Map(old.map(r=>[r.problem_id,meta(r)]));
assert.equal(new Set(rows.map(r=>r.problem_id)).size,previousById.size);
for(const r of rows)assert.equal(meta(r),previousById.get(r.problem_id));
const byTag=new Map(catalog.clusters.map(g=>[g.label,g]));
const direct=new Map(catalog.clusters.flatMap(g=>g.member_tags.map(t=>[t.tag_id,g.cluster_id])));
assert.notEqual(direct.get("T058"),direct.get("T132"));
assert.equal(direct.get("T132"),direct.get("T196"));
assert.notEqual(direct.get("T031"),direct.get("T032"));
assert.notEqual(direct.get("T169"),direct.get("T178"));
assert.equal(new Set(["T069","T071","T072"].map(t=>direct.get(t))).size,3);
assert.equal(new Set(["T053","T233","T234"].map(t=>direct.get(t))).size,1);
const tagsOf=pid=>new Set(rows.filter(r=>r.problem_id===pid).map(r=>r.tag));
assert.ok(tagsOf("abc189_e").has("アフィン変換の合成"));
assert.ok(tagsOf("abc437_f").has("距離の式変形・座標変換"));
assert.deepEqual([...tagsOf("abc312_d")],["文字列上のDP"]);
assert.deepEqual(topics.abc312_d,["括弧列"]);
assert.ok(topics.abc194_e.includes("MEX"));
assert.ok(![...byTag.keys()].some(t=>["括弧列","MEX","Fibonacci 数","線形代数"].includes(t)));
for(const g of catalog.clusters){
 const members=rows.filter(r=>r.tag===g.label);
 assert.equal(members.length,g.problem_count);
 assert.equal(new Set(members.map(r=>r.problem_id)).size,g.problem_count);
}
const server=await createServer({root:APP,server:{middlewareMode:true,hmr:false},appType:"custom",logLevel:"error"});
const result={version:catalog.version,problems:898,units:82,visible_units:82,pairs:rows.length,checks:[]};
try{
 const stats=await server.ssrLoadModule("/src/utils/statistics.js");
 const mds=await server.ssrLoadModule("/src/utils/classicalMds.js");
 const beeswarm=await server.ssrLoadModule("/src/utils/beeswarm.js");
 const peers=await server.ssrLoadModule("/src/utils/peerBaselines.js");
 const {default:Main}=await server.ssrLoadModule("/src/components/Main.jsx");
 const {default:Card}=await server.ssrLoadModule("/src/components/AlgorithmCard.jsx");
 const groups=stats.groupByAlgorithm(rows,"tag");
 const summary=stats.createSummary(groups,stats.countBandsByAlgorithm(rows,"tag"));
 assert.equal(summary.length,82);
 assert.equal(stats.MIN_PROBLEMS_PER_TAG,1);
 const boundary=stats.createSummary({empty:[],single:[100],pair:[100,200]},{});
 assert.deepEqual(new Set(boundary.map(g=>g.algo)),new Set(["single","pair"]));
 assert.ok(summary.every(g=>g.n>=1));
 for(const f of [.25,mds.DEFAULT_LOWER_FRACTION,.75]){
  const points=beeswarm.computeBeeswarm(mds.computeAnchoredClassicalMds(summary,groups,f));
  assert.equal(points.length,82);
  assert.ok(points.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)&&Number.isFinite(p.r)));
 }
 const placed=beeswarm.computeBeeswarm(mds.computeAnchoredClassicalMds(summary,groups,mds.DEFAULT_LOWER_FRACTION));
 const props={
  summary:placed,allRows:rows,lowerFraction:mds.DEFAULT_LOWER_FRACTION,onLowerFractionChange(){},
  username:"",onUsernameChange(){},rate:1000,rateLoading:false,rateError:null,onFetchRate(){},
  onFetchSubmissions(){},onAutoOptimize(){},isOptimizing:false,isOptimized:false,
  submissionsMap:new Map([[rows[0].problem_id,true],[rows[1].problem_id,false]]),
  submissionsLoaded:true,peerBaselines:{catalogCompatible:false,bands:{}}
 };
 const markup=renderToStaticMarkup(React.createElement(Main,props));
 assert.equal((markup.match(/class="pie-node(?: pie-node--selected)?"/g)||[]).length,82);
 assert.equal((markup.match(/aria-label="逐次シミュレーション"/g)||[]).length,1);
 assert.equal((markup.match(/class="pie-node-peer-progress"/g)||[]).length,0);
 assert.ok(markup.includes("学習単位")&&markup.includes("898")&&!markup.includes("2問以上"));
 assert.ok(!markup.includes("距離閾値"));
 assert.ok(!markup.includes("NaN")&&!markup.includes("Infinity"));
 assert.ok(markup.includes("現在の分類に対応する同レート帯データは準備中"));
 assert.ok(markup.includes("pie-node-progress"));
 for(const g of catalog.clusters)if(g.problem_count===1)assert.ok(markup.includes('aria-label="'+g.label+'"'));
 const stringUnit=catalog.clusters.find(g=>g.cluster_id==="L018");
 const stringRows=rows.filter(r=>r.tag===stringUnit.label);
 const card=renderToStaticMarkup(React.createElement(Card,{
  algo:summary.find(g=>g.algo===stringUnit.label),problems:stringRows,
  submissionsMap:new Map([["abc312_d",true]]),memberTags:stringUnit.detail_methods,
  definition:stringUnit.description,problemTopics:topics
 }));
 assert.ok(card.includes("題材：括弧列")&&card.includes("problem-item--ac"));
 assert.equal((card.match(/class="problem-item(?: [^"]*)?"/g)||[]).length,stringRows.length);
 assert.ok(card.includes(stringUnit.description));
 assert.ok(card.includes("含まれる手法：文字列DP"));
 const empty=renderToStaticMarkup(React.createElement(Main,{...props,summary:[]}));
 assert.equal((empty.match(/class="pie-node(?: pie-node--selected)?"/g)||[]).length,0);
 const fetchOriginal=globalThis.fetch;
 try{
  globalThis.fetch=async()=>({ok:true,json:async()=>({source:{taggingVersion:"hc101-jaccard-average-d0.7-v1"},bands:{}})});
  assert.equal((await peers.loadPeerBaselines(undefined,catalog.version)).catalogCompatible,false);
  globalThis.fetch=async()=>({ok:true,json:async()=>({source:{taggingVersion:catalog.version},bands:{}})});
  assert.equal((await peers.loadPeerBaselines(undefined,catalog.version)).catalogCompatible,true);
 }finally{globalThis.fetch=fetchOriginal;}
 result.checks=["6-column CSV schema","all 898 problem IDs and metadata preserved",
 "unique problem-unit assignments and catalog counts","semantic splits and merges",
 "topic/solution separation and source-reviewed refinements","82 rendered pie nodes; all 15 singleton units included",
 "finite MDS/beeswarm coordinates at 3 settings","selected-unit definition and topic rendering",
 "personal progress ring and selected-card AC status","old peer baseline rejected; matching version accepted","empty render"];
 result.browser_ui_check="not performed: Windows browser URL could not be determined confidently; Computer Use stopped";
 await fs.writeFile(path.join(ROOT,"verification.json"),JSON.stringify(result,null,2)+"\n");
 console.log(JSON.stringify(result,null,2));
}finally{await server.close();}
