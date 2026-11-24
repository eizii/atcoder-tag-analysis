from pathlib import Path
p=Path('abc_all/full_review/root_decisions.txt');s=p.read_text(encoding='utf-8-sig').replace('d|n','d divides n');p.write_text(s,encoding='utf-8-sig')
