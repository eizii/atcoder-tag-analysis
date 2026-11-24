from pathlib import Path
p=Path('abc_all/full_review/root_resolutions.txt');rows=p.read_text(encoding='utf-8-sig').splitlines()
for i,l in enumerate(rows):
 if l.startswith('2485|'):
  a=(l.split('|')+['']*7)[:7];a[1]+=',T245~,T002?';a[2]+=' 原文別解の区間等差数列加算をlazy segtreeで行うO(N log N)も確認。';a[6]='0,2';rows[i]='|'.join(a)
p.write_text('\n'.join(rows)+'\n',encoding='utf-8-sig')
