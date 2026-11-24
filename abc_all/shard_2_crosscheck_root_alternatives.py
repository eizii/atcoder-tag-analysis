from itertools import product
from collections import deque
import json
from pathlib import Path

def dcmod(a,m):
 if len(a)==1:return a[0]%m
 h=len(a)//2;left=a[:h];right=a[h:];x=[];z=0
 for v in reversed(left):z=(z+v)%m;x.append(z)
 y=[];z=0
 for v in right:z=(z+v)%m;y.append(z)
 x.sort();y.sort();j=len(y);wrap=0
 for v in x:
  while j and y[j-1]+v>=m:j-=1
  wrap+=len(y)-j
 return dcmod(left,m)+dcmod(right,m)+len(y)*sum(x)+len(x)*sum(y)-m*wrap

def brute_mod(a,m):return sum(sum(a[i:j])%m for i in range(len(a)) for j in range(i+1,len(a)+1))

def edit(s,t):
 d=list(range(len(t)+1))
 for i,a in enumerate(s,1):
  nd=[i]
  for j,b in enumerate(t,1):nd.append(min(nd[-1]+1,d[j]+1,d[j-1]+(a!=b)))
  d=nd
 return d[-1]
def bandbfs(s,t,k):
 n,m=len(s),len(t);q=deque([(0,0)]);d={(0,0):0}
 while q:
  i,j=q.popleft();v=d[i,j]
  for x,y,w in [(i+1,j,1),(i,j+1,1),(i+1,j+1,0 if i<n and j<m and s[i]==t[j] else 1)]:
   if x>n or y>m or abs(x-y)>k or v+w>k:continue
   if v+w<d.get((x,y),10**9):d[x,y]=v+w;(q.append if w else q.appendleft)((x,y))
 return (n,m) in d

def wave(s,t,k):
 n,m=len(s),len(t)
 def snake(i,j):
  while i<n and j<m and s[i]==t[j]:i+=1;j+=1
  return i
 old={0:snake(0,0)}
 if old.get(m-n,-1)==n:return True
 for e in range(1,k+1):
  new={}
  for diag in range(-e,e+1):
   best=-1
   for prev,delta in [(diag,1),(diag+1,1),(diag-1,0)]:
    if prev not in old:continue
    x=old[prev]+delta;y=x+diag
    if 0<=x<=n and 0<=y<=m:best=max(best,x)
   if best>=0:new[diag]=snake(best,best+diag)
  old=new
  if old.get(m-n,-1)==n:return True
 return False

def rmqcontrib(a):
 n=len(a);keys=list(zip(a,range(n)));dd=[0]*(n+4)
 for i,v in enumerate(a):
  lo,hi=0,i
  while lo<hi:
   mid=(lo+hi)//2
   if max(keys[mid:i],default=(-1,-1))<keys[i]:hi=mid
   else:lo=mid+1
  l=i-lo
  lo,hi=i,n-1
  while lo<hi:
   mid=(lo+hi+1)//2
   if max(keys[i+1:mid+1],default=(-1,-1))<keys[i]:lo=mid
   else:hi=mid-1
  r=lo-i
  dd[1]+=v;dd[l+2]-=v;dd[r+2]-=v;dd[l+r+3]+=v
 for _ in range(2):
  for j in range(1,len(dd)):dd[j]+=dd[j-1]
 return dd[1:n+1]
def windowbrute(a):return [sum(max(a[i:i+k]) for i in range(len(a)-k+1)) for k in range(1,len(a)+1)]
counts={}
c=0
for n in range(1,7):
 for a in product(range(4),repeat=n):
  for m in range(1,5):assert dcmod(a,m)==brute_mod(a,m),(a,m);c+=1
counts['abc378_e_mod_divide_conquer']=c
strings=[''.join(x) for n in range(1,6) for x in product('ab',repeat=n)];c=0
for s in strings:
 for t in strings:
  dist=edit(s,t)
  for k in range(4):
   assert bandbfs(s,t,k)==(dist<=k),(s,t,k,'bfs')
   assert wave(s,t,k)==(dist<=k),(s,t,k,'wave');c+=1
counts['abc386_f_band_01bfs_and_wavefront']=c
c=0
for n in range(1,7):
 for a in product(range(4),repeat=n):assert rmqcontrib(a)==windowbrute(a),a;c+=1
counts['abc407_f_rmq_binary_and_second_difference']=c
out={'status':'all_passed','comparisons':counts,'notes':['Sources were read independently; tests compare each reference-derived alternative against direct brute force on bounded exhaustive instances.','RMQ test uses direct maxima as a black-box static query; O(log N) segment-tree queries give the stated O(N log^2 N) boundary method.']}
Path('abc_all/full_review/shard_2_crosscheck_root_alternatives.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(out))
