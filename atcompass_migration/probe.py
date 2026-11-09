# -*- coding: utf-8 -*-
import csv,json,hashlib
from collections import Counter
from pathlib import Path
app=Path("C:/Users/ejham/theme2026-kaziru")
with (app/"public/all_problems.csv").open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
counts=Counter(r["tag"] for r in rows)
peers=json.loads((app/"public/peer-baselines.json").read_text(encoding="utf-8"))
print(json.dumps(dict(rows=len(rows),problems=len({r["problem_id"] for r in rows}),tags=len(counts),
simulation={k:v for k,v in counts.items() if "simul" in k.lower() or "シミュ" in k},
peer_top_keys=list(peers),peer_band_keys={k:list(v) for k,v in peers["bands"].items()},
csv_hash=hashlib.sha256((app/"public/all_problems.csv").read_bytes()).hexdigest()),ensure_ascii=False,indent=2))
