from root_crosscheck_0 import rng
import heapq
for _ in range(1000):
 n=rng.randrange(2,9)
 edges=[(i,rng.randrange(i),rng.randrange(1,10)) for i in range(1,n)]
 used={tuple(sorted((u,v))) for u,v,w in edges}
 for u in range(n):
  for v in range(u):
   if (v,u) not in used and rng.randrange(3)==0:edges.append((u,v,rng.randrange(1,10)))
 def dist(start,skip=-1):
  g=[[] for i in range(n)]
  for j,(u,v,w) in enumerate(edges):
   if j!=skip:g[u].append((v,w));g[v].append((u,w))
  ds=[10**9]*n;ds[start]=0;pq=[(0,start)]
  while pq:
   d,v=heapq.heappop(pq)
   if d!=ds[v]:continue
   for u,w in g[v]:
    if ds[u]>d+w:ds[u]=d+w;heapq.heappush(pq,(ds[u],u))
  return ds
 ds=dist(0);dt=dist(n-1)
 short={j for j,(u,v,w) in enumerate(edges) if ds[u]+w+dt[v]==ds[-1] or ds[v]+w+dt[u]==ds[-1]}
 for j,(u,v,w) in enumerate(edges):
  seen={u};stack=[u]
  while stack:
   x=stack.pop()
   for k in short-{j}:
    a,b,_=edges[k]
    if a==x and b not in seen:seen.add(b);stack.append(b)
    if b==x and a not in seen:seen.add(a);stack.append(a)
  bridge=j in short and v not in seen
  assert bridge==(dist(0,j)[-1]!=ds[-1])
print('Shortest-subgraph bridge tests',1000)
