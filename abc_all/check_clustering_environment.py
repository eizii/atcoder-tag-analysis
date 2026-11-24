import sys,numpy,scipy,matplotlib,sklearn
from pathlib import Path
print(sys.version)
print({'numpy':numpy.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'sklearn':sklearn.__version__})
print('agents',list(Path('.').rglob('AGENTS.md'))[:20])
