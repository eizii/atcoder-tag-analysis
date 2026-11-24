from pathlib import Path
p=Path('abc_all/full_review/record_root_decisions.py');s=p.read_text(encoding='utf-8-sig').replace("d['editorials'][int(source)]['text']", "'\\n'.join(d['editorials'][int(j)]['text'] for j in source.split(','))")
p.write_text(s,encoding='utf-8-sig')
