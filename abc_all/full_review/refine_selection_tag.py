from pathlib import Path
p=Path('abc_all/full_review/root_resolutions.txt');s=p.read_text(encoding='utf-8-sig').replace('T025,T022~,T073~,T219~','T025,T022~,T073~');p.write_text(s,encoding='utf-8-sig')
