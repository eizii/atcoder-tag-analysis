from pathlib import Path
import numpy as np
from scipy.cluster.hierarchy import fcluster
p=Path('abc_all/hierarchical_v4_20261124')
for ds in ('all_difficulties','under_2000'):
 for model in ('cosine_complete','jaccard_complete'):
  z=np.loadtxt(p/ds/model/'linkage.csv',delimiter=',',skiprows=1);print(ds,model,'minimum below 1',len(set(fcluster(z,np.nextafter(1.,0),criterion='distance'))))
