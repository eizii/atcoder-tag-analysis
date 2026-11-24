from pathlib import Path
p=Path('abc_all/full_review/root_resolutions.txt')
s=p.read_text(encoding='utf-8-sig');rows=[]
for l in s.splitlines():
 a=l.split('|')
 if len(a)>7:
  print(a[0],len(a));a=[*a[:4],*a[-3:]]
 rows.append('|'.join(a))
p.write_text('\n'.join(rows)+'\n',encoding='utf-8-sig')
