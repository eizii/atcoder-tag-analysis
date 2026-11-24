from record_resolution_0 import DOC
import re
pid='abc440_g'
print(re.sub(r'\s+',' ',' '.join(DOC[pid]['editorials'][0].get('codes',[])))[1400:])
