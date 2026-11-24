import itertools,random,heapq

def sb(a,b,c,d):
 ln,ld,rn,rd=0,1,1,0
 loops=0
 while True:
  loops+=1
  mn,md=ln+rn,ld+rd
  if mn*b<=a*md:
   k=(a*ld-b*ln)//(b*rn-a*rd);assert k>=1
   ln+=k*rn;ld+=k*rd
  elif mn*d>=c*md:
   k=(d*rn-c*rd)//(c*ld-d*ln);assert k>=1
   rn+=k*ln;rd+=k*ld
  else:return mn,md,loops
cnt=0
for a,b,c,d in itertools.product(range(1,11),repeat=4):
 if a*d>=b*c:continue
 p,q,_=sb(a,b,c,d)
 brute=next(z for z in range(1,b+d+1) if a*z//b+1<=(c*z-1)//d)
 assert q==brute,(a,b,c,d,p,q,brute)
 cnt+=1
print('Stern-Brocot strict-bound tests',cnt)

def prefix(s):
 p=[0]*len(s)
 for i in range(1,len(s)):
  j=p[i-1]
  while j and s[i]!=s[j]:j=p[j-1]
  if s[i]==s[j]:j+=1
  p[i]=j
 return p
cnt=0
for n in range(1,10):
 for word in itertools.product('AB',repeat=n):
  s=''.join(word);got=prefix(s[::-1]+'#'+s)[-1]
  want=max(k for k in range(1,n+1) if s[-k:]==s[-k:][::-1])
  assert got==want
  cnt+=1
print('Palindrome KMP tests',cnt)
rng=random.Random(0)
for _ in range(1000):
 n=rng.randrange(2,9);x=rng.randrange(1,10);u=[rng.randrange(1,11) for i in range(n)];d=[rng.randrange(1,11) for i in range(n)]
 def ok(h):
  lo,hi=0,h
  for uu,dd in zip(u,d):
   lo=max(0,lo-x,h-dd);hi=min(h,hi+x,uu)
   if lo>hi:return False
  return True
 want=max(h for h in range(min(uu+dd for uu,dd in zip(u,d))+1) if ok(h))
 S,T=n,n+1;g=[[] for i in range(n+2)]
 for i in range(n):
  g[S].append((i,d[i]));g[i].append((S,0));g[i].append((T,u[i]));g[T].append((i,0))
  if i:g[i].append((i-1,x));g[i-1].append((i,x))
 ds=[10**9]*(n+2);ds[S]=0;pq=[(0,S)]
 while pq:
  cost,v=heapq.heappop(pq)
  if cost!=ds[v]:continue
  for w,costw in g[v]:
   if cost+costw<ds[w]:ds[w]=cost+costw;heapq.heappush(pq,(ds[w],w))
 assert ds[T]==want,(u,d,x,ds[T],want)
print('Sparse Dijkstra reduction tests',1000)
