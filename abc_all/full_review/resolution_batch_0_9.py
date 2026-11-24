from record_resolution_0 import *
put('abc435_e','T012:primary,T014:supporting,T064:supporting,T002:alternative,T003:supporting,T085:supporting','白区間を端点順setで管理。新黒区間に交わる白区間だけlower_boundから走査削除し、両端の残片を戻して白長総和を更新。各問区間増加<=1なので全削除O(Q)、全体O(Q log Q)。source1は動的lazysegtreeの区間0代入/sumでO(Q log N)、全端点を先読み圧縮し長さ重み付きlazysegtreeでもO(Q log Q)。',anchor='操作回数はすべてのクエリ')
put('abc435_g','T022:primary,T086:supporting,T060:supporting','色cの最右ドミノ終端iのdp[i,c]=S[i-2]-dp[i-2,c]（色許容区間内のみ）。偶奇別に色配列Tと個数・総和を保持し全体変換t→S[k-4]-tを符号/offsetでO(1)遅延、色の許容出入りだけ個別変更する。出入り総O(M)でS[k]=S[k-1]+|T|S[k-2]-sumTをO(N+M)。','配列全体へのアフィン変換の遅延保持',anchor='T_k')
put('abc436_d','T066:primary,T011:supporting,T144:alternative,T007:supporting,T055:concept','各文字のwarp先一覧を前計算しBFS。文字cを初めて取り出した時だけ同文字全マスへ距離+1を展開し、以後cのwarpは省く。全一覧の合計HWなのでO(HW)。source1は文字ごとの超頂点へ重み1、そこから各warpへ0辺を張る0-1 BFSでO(HW)。',anchor='各文字ごとに最初')
put('abc436_e','T182:primary,T005:alternative,T067:alternative,T201:concept,T060:supporting,T177:supporting','Pの巡回分解で各cycle長sを求めsum s(s-1)/2を返すO(N)。最小交換数N-cycle数を1減らす交換は同じcycle内の任意2頂点に限る。DSU/DFSでi-Piの成分サイズを求めても可。',anchor='同じ連結成分にある')
put('abc436_g','T132:primary,T127:supporting,T022:supporting,T060:supporting','x=2q+r,r各0/1へ分解しS[s]=#r:sum Ai*ri=sを多項式積で求める。f(M)=sum_s S[s]f(floor((M-s)/2))。現係数列cをSと畳込み、同じfloor先へ2項ずつ集約しMを半減する。係数幅O(sum A)<=1e4、約60回でf(0)=1のみ残る。前計算O(N*sumA log sumA)、反復O(sumA log sumA log M)。多重集合は数学的表現のみ。',anchor='c _ M=1')
rows['abc435_e']['source_indices']='0,1'
rows['abc436_d']['source_indices']='0,1'
save()
