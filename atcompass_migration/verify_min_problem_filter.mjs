import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import assert from "node:assert/strict";
import crypto from "node:crypto";

const APP="C:/Users/ejham/theme2026-kaziru";
const require=createRequire(path.join(APP,"package.json"));
const Papa=require("papaparse");
const React=require("react");
const {renderToStaticMarkup}=require("react-dom/server");
const {createServer}=await import(pathToFileURL(require.resolve("vite")).href);
const text=await fs.readFile(path.join(APP,"public/all_problems.csv"),"utf8");
const parsed=Papa.parse(text,{header:true,skipEmptyLines:true,dynamicTyping:true});
assert.equal(parsed.errors.length,0);
const rows=parsed.data.map(row=>({...row,diffCalc:Number(row.difficulty)}));
const catalog=JSON.parse(await fs.readFile(path.join(APP,"src/data/tagCatalog.json"),"utf8"));
assert.equal(catalog.distance_threshold,.7);
assert.equal(catalog.clusters.length,101);
assert.equal(rows.length,1720);
assert.equal(new Set(rows.map(r=>r.problem_id)).size,898);
assert.equal(new Set(rows.map(r=>r.tag)).size,101);
assert.equal(new Set(rows.map(r=>JSON.stringify([r.problem_id,r.tag]))).size,1720);
assert.equal(crypto.createHash("sha256").update(await fs.readFile(path.join(APP,"public/all_problems.csv"))).digest("hex"),catalog.problemCatalogSha256);
const server=await createServer({root:APP,server:{middlewareMode:true,hmr:false},appType:"custom",logLevel:"error"});
const findings={version:catalog.version,cut:.7,clusters:101,problems:898,pairs:1720};
try {
 const statistics=await server.ssrLoadModule("/src/utils/statistics.js");
 const mds=await server.ssrLoadModule("/src/utils/classicalMds.js");
 const beeswarm=await server.ssrLoadModule("/src/utils/beeswarm.js");
 const peers=await server.ssrLoadModule("/src/utils/peerBaselines.js");
 const {default:Main}=await server.ssrLoadModule("/src/components/Main.jsx");
 const groups=statistics.groupByAlgorithm(rows,"tag");
 const bands=statistics.countBandsByAlgorithm(rows,"tag");
 const stats=statistics.createSummary(groups,bands);
 assert.equal(statistics.MIN_PROBLEMS_PER_TAG,2);
 assert.equal(stats.length,76);
 assert.ok(stats.every(item=>item.n>=2));
 assert.equal(Object.keys(groups).filter(tag=>groups[tag].length===1).length,25);
 const boundary=statistics.createSummary({empty:[],single:[100],pair:[100,200]},{});
 assert.equal(boundary.length,1);
 assert.equal(boundary[0].algo,"pair");
 assert.equal(boundary[0].n,2);
 assert.equal(statistics.createSummary({single:[100]},{}).length,0);
 findings.displayed_tags=76;
 findings.hidden_tags=25;
 for(const fraction of [.25,mds.DEFAULT_LOWER_FRACTION,.75]){
   const points=beeswarm.computeBeeswarm(mds.computeAnchoredClassicalMds(stats,groups,fraction));
   assert.equal(points.length,76);
   assert.ok(points.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)&&Number.isFinite(p.r)));
 }
 const summary=beeswarm.computeBeeswarm(mds.computeAnchoredClassicalMds(stats,groups,mds.DEFAULT_LOWER_FRACTION));
 const renderProps={
   summary,allRows:rows,lowerFraction:mds.DEFAULT_LOWER_FRACTION,
   onLowerFractionChange(){},username:"",onUsernameChange(){},rate:1000,rateLoading:false,rateError:null,
   onFetchRate(){},onFetchSubmissions(){},onAutoOptimize(){},isOptimizing:false,isOptimized:false,
   submissionsMap:new Map([[rows[0].problem_id,true],[rows[1].problem_id,false]]),
   submissionsLoaded:true,peerBaselines:{catalogCompatible:false,bands:{}}
 };
 const markup=renderToStaticMarkup(React.createElement(Main,renderProps));
 assert.equal((markup.match(/class="pie-node(?: pie-node--selected)?"/g)||[]).length,76);
 assert.equal((markup.match(/aria-label="C055: シミュレーション"/g)||[]).length,1);
 assert.equal((markup.match(/class="pie-node-peer-progress"/g)||[]).length,0);
 assert.ok(markup.includes("距離閾値")&&markup.includes("101")&&markup.includes("0.7"));
 assert.ok(markup.includes("現在の分類に対応する同レート帯データは準備中です"));
 assert.ok(!markup.includes("NaN")&&!markup.includes("Infinity"));
 assert.ok(markup.includes("2問以上"));
 for(const [tag,values] of Object.entries(groups)){
   if(values.length===1)assert.ok(!markup.includes('aria-label="'+tag+'"'));
 }
 const emptyMarkup=renderToStaticMarkup(React.createElement(Main,{...renderProps,summary:[]}));
 assert.equal((emptyMarkup.match(/class="pie-node(?: pie-node--selected)?"/g)||[]).length,0);
 assert.ok(emptyMarkup.includes("ノード（アルゴリズム）を選択してください"));
 const fetchOriginal=globalThis.fetch;
 try {
   globalThis.fetch=async()=>({ok:true,json:async()=>({bands:{"1000-1099":{tags:{}}},source:{taggingVersion:"hc72-jaccard-average-d0.9-v1"}})});
   const incompatible=await peers.loadPeerBaselines(undefined,catalog.version);
   assert.equal(incompatible.catalogCompatible,false);
   assert.equal(peers.getPeerRatingBand(incompatible,1000),null);
   globalThis.fetch=async()=>({ok:true,json:async()=>({bands:{"1000-1099":{tags:{"C055: シミュレーション":{problemCount:60,ac:{mean:12,median:10}}}}},source:{taggingVersion:catalog.version}})});
   const compatible=await peers.loadPeerBaselines(undefined,catalog.version);
   assert.equal(compatible.catalogCompatible,true);
   const rating=peers.getPeerRatingBand(compatible,1000);
   assert.equal(peers.createPeerProgressMap(rating).get("C055: シミュレーション").ac,12);
 } finally {globalThis.fetch=fetchOriginal;}
 findings.checks=["CSV parser and schema","unique problem-cluster pairs","catalog hash",
  "finite MDS/beeswarm coordinates at 3 settings","server-rendered 76 pie nodes; all 25 single-problem tags absent",
  "one simulation node","old baseline rejected; matching baseline accepted",
  "personal-progress render preserved"];
 findings.browser_ui_check="not performed: no connected browser in the available browser tool";
 console.log(JSON.stringify(findings,null,2));
} finally {
 await server.close();
}
await fs.writeFile(new URL("./minimum_problem_filter_verification.json",import.meta.url),JSON.stringify(findings,null,2)+"\n");
