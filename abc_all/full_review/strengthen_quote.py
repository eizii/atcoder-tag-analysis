from pathlib import Path
p=Path('abc_all/full_review/root_decisions.txt');lines=p.read_text(encoding='utf-8-sig').splitlines()
for i,l in enumerate(lines):
 if l.startswith('2256|'):
  a=(l.split('|')+['']*7)[:7];a[5]='for 文などを用いて、各';a[6]='0';lines[i]='|'.join(a)
p.write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
