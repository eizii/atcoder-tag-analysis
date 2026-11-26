from pathlib import Path
import json,urllib.request,hashlib,time
ROOT=Path(__file__).resolve().parent;CACHE=ROOT/'retrieval_model_cache';CACHE.mkdir(exist_ok=True)
MODEL='intfloat/multilingual-e5-small'
REVISION='614241f622f53c4eeff9890bdc4f31cfecc418b3'
EXPECTED={'model_qint8_avx512_vnni.onnx':'dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88','tokenizer.json':'0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39'}
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'atcoder-tag-retrieval-prototype/0.1'})
 return urllib.request.urlopen(req,timeout=90)
rev=REVISION;files=['onnx/model_qint8_avx512_vnni.onnx','onnx/tokenizer.json']
result={'model':MODEL,'revision':rev,'files':{}}
for name in files:
 dest=CACHE/Path(name).name
 if not dest.exists():
  print('downloading',name,flush=True)
  with get('https://huggingface.co/'+MODEL+'/resolve/'+rev+'/'+name) as src,dest.with_suffix(dest.suffix+'.part').open('wb') as dst:
   while True:
    block=src.read(1024*1024)
    if not block:break
    dst.write(block)
  dest.with_suffix(dest.suffix+'.part').replace(dest)
 result['files'][dest.name]={'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size}
 assert result['files'][dest.name]['sha256']==EXPECTED[dest.name],f'Unexpected model file: {dest.name}'
 print(dest.name,dest.stat().st_size,flush=True)
(CACHE/'model_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
