import zipfile
from collect_statements import ROOT
files=[ROOT/"README.md",ROOT/"taxonomy.json",ROOT/"tag_rules.json",ROOT/"semantic_reviews.json",ROOT/"source_coverage.json"]
files += [p for p in (ROOT/"output").iterdir() if p.suffix in {".csv",".json"}]
with zipfile.ZipFile(ROOT/"abc_all_results_20261105.zip","w",compression=zipfile.ZIP_DEFLATED) as archive:
    for p in files: archive.write(p,p.relative_to(ROOT).as_posix())
print("Result archive created")
