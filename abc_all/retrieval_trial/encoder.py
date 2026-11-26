# -*- coding: utf-8 -*-
"""Frozen multilingual E5 ONNX embeddings; no remote inference."""
from pathlib import Path
import hashlib,json,time
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
ROOT=Path(__file__).resolve().parent.parent
class Encoder:
 def __init__(self,max_length=256,threads=4):
  self.max_length=max_length;cache=ROOT/'retrieval_model_cache';self.manifest=json.loads((cache/'model_manifest.json').read_text(encoding='utf-8'))
  options=ort.SessionOptions();options.intra_op_num_threads=threads;options.inter_op_num_threads=1
  self.session=ort.InferenceSession(str(cache/'model_qint8_avx512_vnni.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
  self.raw=Tokenizer.from_file(str(cache/'tokenizer.json'));self.tokenizer=Tokenizer.from_file(str(cache/'tokenizer.json'));self.tokenizer.enable_truncation(max_length=max_length);self.tokenizer.enable_padding(pad_id=1,pad_token='<pad>');self.input_names={i.name for i in self.session.get_inputs()}
 def token_length(self,text):return len(self.raw.encode(text).ids)
 def encode(self,texts,prefix='query: ',batch_size=16,progress=True):
  result=[];start=time.perf_counter();truncated=0
  for offset in range(0,len(texts),batch_size):
   batch=[prefix+t for t in texts[offset:offset+batch_size]];truncated+=sum(self.token_length(t)>self.max_length for t in batch);encoded=self.tokenizer.encode_batch(batch)
   allinputs={'input_ids':np.array([e.ids for e in encoded],dtype=np.int64),'attention_mask':np.array([e.attention_mask for e in encoded],dtype=np.int64),'token_type_ids':np.array([e.type_ids for e in encoded],dtype=np.int64)}
   out=self.session.run(None,{k:v for k,v in allinputs.items() if k in self.input_names})[0]
   if out.ndim==3:
    mask=allinputs['attention_mask'][...,None];out=(out*mask).sum(axis=1)/mask.sum(axis=1)
   out=out.astype(np.float32);out/=np.linalg.norm(out,axis=1,keepdims=True);result.append(out)
   if progress and (offset//batch_size)%40==0:print(json.dumps({'encoded':min(offset+batch_size,len(texts)),'total':len(texts),'seconds':round(time.perf_counter()-start,1)}),flush=True)
  self.last_stats={'texts':len(texts),'truncated':truncated,'seconds':time.perf_counter()-start,'max_tokens':self.max_length,'prefix':prefix}
  return np.concatenate(result)
if __name__=='__main__':
 e=Encoder();v=e.encode(['幅優先探索で重みなしグラフの最短距離を求める。','BFS explores an unweighted graph by distance layers.','連結成分をUnion Findで管理する。']);print(v.shape, v@v.T,e.last_stats)
