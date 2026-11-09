"""Download public AtCoder Problems metadata. No model API calls."""
import json
import pathlib
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
BASE = ROOT / "metadata"
BASE.mkdir(parents=True, exist_ok=True)
for name in ["contests.json", "problems.json", "contest-problem.json", "problem-models.json"]:
    dest = BASE / name
    if dest.exists():
        print(json.dumps({"file": name, "cached": True, "items": len(json.loads(dest.read_text(encoding="utf-8")))}), flush=True)
        continue
    request = urllib.request.Request("https://kenkoooo.com/atcoder/resources/" + name,
        headers={"User-Agent": "AtCompassResearch/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read()
    obj = json.loads(raw)
    dest.write_bytes(raw)
    print(json.dumps({"file": name, "items": len(obj), "bytes": len(raw)}), flush=True)
    time.sleep(1.2)
