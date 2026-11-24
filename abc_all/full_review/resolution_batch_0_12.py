from record_resolution_0 import *
put('abc442_c','T177:primary,T060:supporting','各頂点の利害辺次数dを数え、査読候補人数c=N-1-dに対してC(c,3)=c(c-1)(c-2)/6。O(N+M)。mod逆元は使わない。',anchor='二項係数')
put('abc442_d','T086:primary,T001:alternative,T003:alternative','隣接x,x+1のswapでprefix和が変わるのはS[x]だけ。元配列をswapしS[x]=S[x-1]+新Axを更新、区間和はS[r]-S[l-1]で全O(N+Q)。source1のFenwick/通常segtreeによる2点更新もO(N+Q log N)で満点。',anchor='値が変化するのは')
put('abc442_f','T022:primary,T086:supporting','各行の白prefix長Aiは非増加が必要十分。dp[i,j]=行iのj境界塗替費用+min_{k>=j}dp[i-1,k]。行内費用はprefix和/差分更新、前行のsuffix最小で遷移をO(1)にし全O(N^2)。source1の境界格子経路DPもO(N^2)。',anchor='後ろから累積 min')
put('abc443_d','T022:primary,T187:alternative,T010:supporting,T055:concept,T076:alternative','前からRi=min(Ri,Ri-1+1)、後ろからRi=min(Ri,Ri+1+1)を行うと最終Ri=min_j(元Rj+|i-j|)。最適位置はこの上界を同時達成し、元総和との差が答え。O(N)。source1は超頂点→i重みRiと隣接重み1のDijkstra、source2は最上行駒からheapで制約伝播、共にO(N log N)。',anchor='本解法の時間計算量')
put('abc443_e','T022:primary','到達可能dp[i,j]を下から更新。下3マスのどれか可なら空マスへ進める。壁がその列の元の最下壁であればそこへ進入後は列上方の壁を順に壊せるため上方全てを可にする。初期列Cも全行可。最下壁前計算と各列1度の上方一括有効化でO(N^2)。',anchor='最も下の壁マス')
put('abc444_f','T064:primary,T076:supporting,T077:supporting','候補X>=2について長さ>=2X-1を全て分割した正準葉分布を求める。各元棒の長さ種類は各深さfloor(A/2^k)と+1のみなので個数をまとめO(log A)。X以上葉がH=(N+M+1)/2以上あり、その最小H本の和Sに対し総長-S>=H-1なら可。分布sortと残余棒の追加切断可能数で判定し二分探索。X=1は自明可。O(N log^2 A+N log N log A)。',anchor='二分探索で解きます')
put('abc444_g','T022:primary,T134:supporting,T065:supporting,T182:supporting,T176:supporting,T264:supporting','Cx-A,Cy-BをGaussian整数gとしnorm(g)=N、g mod C=(-A,-B)を数える。p≡3mod4の奇指数なら0。2の指数は固定、p≡1mod4はp=a^2+b^2を探索しπ^(E-k)*conjπ^kのk=0..E分布をC^2剰余状態で作る。π冪の前周期/周期O(C^2)から端を列挙し中央を周期集計、冪は高速累乗。素数ごと分布を愚直合成O(C^4)、最後に4単位回転を加える。全体O(MC^4+P^1.5)＋周期前処理。','Gaussian整数の一意分解,複素剰余積の分布DP',anchor='問題2 元の問題')
for pid,indices in {'abc442_d':'0,1','abc442_f':'0,1','abc443_d':'0,1,2'}.items():rows[pid]['source_indices']=indices
save()

