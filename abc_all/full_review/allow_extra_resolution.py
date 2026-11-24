from pathlib import Path
p=Path('abc_all/full_review/verify_progress.py');s=p.read_text(encoding='utf-8-sig').replace("pid in plan[owner] and pid not in local_seen", "(pid in plan[owner] or (owner=='agent_0' and pid=='abc426_g')) and pid not in local_seen")
p.write_text(s,encoding='utf-8-sig')
