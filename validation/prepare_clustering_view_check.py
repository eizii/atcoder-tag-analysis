# -*- coding: utf-8 -*-
import json,re
from pathlib import Path
import numpy as np
from scipy.cluster.hierarchy import fcluster
root=Path(__file__).resolve().parent.parent
html=(root/"clustering/report.html").read_text(encoding="utf-8")
data=json.loads(re.search(r'<script id="analysis-data" type="application/json">(.*?)</script>',html,re.S).group(1))
expected=[]
for model in data["models"]:
    tree=np.array(model["tree"])
    for threshold in sorted({r["threshold"] for r in model["metrics"]} | {0.9}):
        labels=fcluster(tree,threshold,criterion="distance")
        groups=sorted([np.flatnonzero(labels==label).tolist() for label in set(labels)],key=lambda g:g[0])
        expected.append(dict(model=model["key"],threshold=threshold,groups=groups))
(root/"validation/clustering_view_expected.json").write_text(json.dumps(expected),encoding="utf-8")
print(len(expected))
