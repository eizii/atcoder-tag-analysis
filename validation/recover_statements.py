# -*- coding: utf-8 -*-
"""Recover flagged statements from their official AtCoder task pages; no API keys."""
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path
from statement_extraction import extract_statement, self_check

HERE = Path(__file__).resolve().parent
target_ids = json.loads((HERE / "statement_recovery_targets.json").read_text(encoding="utf-8"))
destination = HERE / "recovered_statements"
destination.mkdir(exist_ok=True)
assert self_check()["status"] == "passed"
results = []
for index, problem_id in enumerate(target_ids, 1):
    if not re.fullmatch(r"abc\d+_[a-h]", problem_id):
        raise ValueError("Unexpected problem ID")
    url = f"https://atcoder.jp/contests/{problem_id.split('_')[0]}/tasks/{problem_id}?lang=ja"
    file = destination / f"{problem_id}.json"
    result = {"problem_id": problem_id, "source_url": url}
    if file.exists():
        cached = json.loads(file.read_text(encoding="utf-8"))
        if cached.get("statement"):
            result.update(status="cached", statement_length=len(cached["statement"]))
            results.append(result)
            continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AtCoderTagValidation/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read()
        statement = extract_statement(content.decode("utf-8"))
        record = {
            **result, "statement": statement,
            "html_sha256": hashlib.sha256(content).hexdigest(),
            "extractor": "section_headings_v1",
        }
        file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        result.update(status="recovered", statement_length=len(statement))
    except Exception as error:
        result.update(status="failed", error=str(error))
    results.append(result)
    if index % 10 == 0 or index == len(target_ids):
        print(json.dumps({
            "processed": index, "total": len(target_ids),
            "recovered_or_cached": sum(r["status"] != "failed" for r in results),
            "failed": sum(r["status"] == "failed" for r in results),
        }), flush=True)
    time.sleep(1)
(HERE / "statement_recovery_results.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
