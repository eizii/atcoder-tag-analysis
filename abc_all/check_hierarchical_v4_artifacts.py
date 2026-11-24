import re,json
from pathlib import Path
p=Path('abc_all/hierarchical_v4_20261124');s=(p/'index.html').read_text(encoding='utf-8');js=re.search(r'<script>([\s\S]*)</script>',s).group(1);(p/'dashboard_script_check.js').write_text(js,encoding='utf-8')
links=[]
for f in p.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8-sig')):
  if target.startswith(('https:','http:','#')):continue
  assert (f.parent/target).exists(),(f,target)
  links.append(target)
print('local document links verified',len(links));print('files',len(list(p.rglob('*'))))
