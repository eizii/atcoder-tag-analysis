from record_resolution_0 import *
put('abc427_b','T076:primary,T022:supporting,T264:supporting,T073:alternative,T086:alternative','f(x)を十進各桁の和としAi=sum_{j<i}f(Aj)を順次計算する。N<=100なので二重ループO(N^2 log最大A)で十分。桁は%10と/10または文字列化で求める。累積和を持てばAi+1=Ai+f(Ai)でO(N log最大A)にもできる。',anchor='愚直に問題文')
put('abc431_f','T024:primary,T022:supporting,T165:supporting,T177:supporting,T236:supporting,T086:supporting','値vを小さい順に挿入。許容隙間数はsum_{u=v-D}^{v-1}cnt[u]+1で、同値cnt[v]個を各隙間へ分配する数C(sum_{u=v-D}^v cnt[u],cnt[v])を掛ける挿入DP。窓和と階乗逆階乗でO(N+max A+log MOD)。多次元表は不要だが前値までの解数から次値解数へのDPとして実行される。',anchor='挿入 dp')
put('abc431_g','T001:primary,T003:alternative,T014:alternative,T012:supporting,T077:supporting,T086:supporting,T064:supporting','swap後<AはAl>Arで順序キー(l,Ar,-r)、>AはAl<Arで(-l,Ar,r)、同値swapはAと一致。各lの転倒数prefixからlを決め、suffix頻度FenwickのkthでArを決め、その値の位置列でrを決める。問をk順にsortしてO(Q log Q+(N+Q)log N)。segtreeまたは順位統計付き平衡木のpair集合でも可。素のstd::multisetのkth走査は不可。',anchor='fenwick tree',uncertainty='本文冒頭のX,Y定義と不等号側・同値範囲境界に誤記があるため、最初のswap比較事実と元コードのAl>Ar側先行処理に合わせた。')
put('abc432_d','T076:primary,T005:supporting,T067:alternative,T022:analysis_concept,T077:supporting,T201:concept','黒領域を互いに重ならない長方形で保持し、各嵐の閾値で高々2分割して指定方向へ移す。全長方形対の辺接触を検査しDSU/DFS成分の面積和をsort。P<=2^Nという粗い上界でO(NP+P^2)、解説の精密解析はN<=14でP<=471を保証。DPはこの領域数上界の解析用で出力計算には不要。',anchor='より高度な計算量解析')
put('abc432_e','T003:primary,T001:alternative','値別頻度Cと値重みj*Cをsegtree/Fenwickに保持し点変更。l<=rならl*count(A<l)+sum(l<=A<=r)+r*count(A>r)。l>rなら全項lなのでNl。初期頻度集計・木構築O(N+K)、各問O(log K)、K<=5e5。',anchor='l > r')
put('abc432_f','T017:primary,T022:supporting,T077:supporting,T201:analysis_concept','平均Xが非整数なら不可。差分bi=Ai-Xの部分集合sumを前計算しdp[mask]=min_i dp[mask\i]+[sum(mask)!=0]をO(N2^N)計算。sum0ごとの復元群数を最大化すると操作数N-群数が最小。各群をAi降順にし余剰を次人へ渡すchainで構成O(N log N)。多重集合は入力の数学的表現でstd::multiset技法ではない。',anchor='bitDP')
save()

