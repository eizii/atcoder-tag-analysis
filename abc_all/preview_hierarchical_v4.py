from PIL import Image
from pathlib import Path
p=Path('abc_all/hierarchical_v4_20261124/all_difficulties/cosine_average/dendrogram.png');im=Image.open(p);print(im.size);im.crop((0,0,im.width,1250)).save(p.parent/'preview_top.png')
