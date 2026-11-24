import json
from pathlib import Path
p=Path('abc_all/hierarchical_v4_20261124/all_difficulties')
for model in ('cosine_average','cosine_single','cosine_complete','jaccard_average'):
 g=json.loads((p/model/'clusters_cut_0.8.json').read_text(encoding='utf-8'))['clusters'];print(model)
 for r in sorted(g,key=lambda x:-x['tag_count'])[:8]:print(r['tag_count'],', '.join(r['tags'])[:450])
