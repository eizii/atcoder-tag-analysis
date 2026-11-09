"""Apply ONLY reviewed staged paths, after checking current files and saved backups."""
import argparse,hashlib,json
from pathlib import Path
from build_dataset import ROOT,APP,load,save,sha
def apply(do_apply=False):
    manifest=load(ROOT/"change_manifest.json")
    for rel,entry in manifest.items():
        target=(APP/rel).resolve()
        assert APP.resolve() in target.parents
        staged=ROOT/"staged_app"/rel
        assert sha(staged)==entry["staged_sha256"]
        if entry["before_sha256"] is None:assert not target.exists(),str(target)
        else:
            assert target.exists() and sha(target)==entry["before_sha256"],"Current application changed: "+rel
            assert sha(ROOT/"app_backup"/rel)==entry["before_sha256"]
    if not do_apply:
        print(json.dumps({"ready":True,"files":list(manifest)}));return
    for rel,entry in manifest.items():
        target=APP/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/"staged_app"/rel).read_bytes())
        assert sha(target)==entry["staged_sha256"]
    save(ROOT/"applied.json",{"version":load(ROOT/"policy.json")["version"],"files":manifest,"backups":"app_backup","published":False})
    print(json.dumps({"applied":list(manifest),"published":False}))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true")
    apply(p.parse_args().apply)
