from pathlib import Path
p=Path('abc_all/full_review/root_resolutions.txt');s=p.read_text(encoding='utf-8-sig').replace('|線形マトロイド交差| | | |0','|線形マトロイド交差|||0').replace('T022,T017~,T064~,T128^','T022,T017~,T064~')
p.write_text(s,encoding='utf-8-sig')
