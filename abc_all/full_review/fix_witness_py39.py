from pathlib import Path
p=Path('abc_all/full_review/validate_root_alternatives.py');s=p.read_text(encoding='utf-8-sig').replace('x.bit_count()',"bin(x).count('1')").replace('(rows[i]^x^(z-1 if mask>>i&1 else 0)).bit_count()',"bin(rows[i]^x^(z-1 if mask>>i&1 else 0)).count('1')").replace('mask.bit_count()',"bin(mask).count('1')")
p.write_text(s,encoding='utf-8-sig')
