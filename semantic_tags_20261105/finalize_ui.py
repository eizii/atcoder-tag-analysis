from build_dataset import ROOT,APP,load,save,sha
rel="src/components/AlgorithmCard.jsx"
manifest=load(ROOT/"change_manifest.json")
target=APP/rel
assert sha(target)==manifest[rel]["staged_sha256"]
s=target.read_text(encoding="utf-8")
old="{memberTags.length > 1 && ("
new="{memberTags.length > 0 && (memberTags.length > 1 || memberTags[0] !== algo.algo) && ("
assert s.count(old)==1
s=s.replace(old,new)
target.write_text(s,encoding="utf-8")
(ROOT/"staged_app"/rel).write_bytes(target.read_bytes())
manifest[rel]["staged_sha256"]=sha(target)
save(ROOT/"change_manifest.json",manifest)
applied=load(ROOT/"applied.json")
applied["files"]=manifest
save(ROOT/"applied.json",applied)
