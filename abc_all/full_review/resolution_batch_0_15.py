from record_resolution_0 import *
put('abc449_e','T001:primary,T077:supporting,T064:supporting,T086:supporting,T264:supporting,T010:alternative,T003:alternative','頻度順（同頻度は値順）に値を並べ、最小頻度群を次頻度まで持ち上げる段階長k*(次頻度-現頻度)のprefix和を作る。Xiが属する段階kと巡回内順位を二分探索・剰余で求める。問をk順にしFenwickの追加とkthで値を得るO((M+Q)log(M+Q)+N)。segtreeでも可。source1はQをheap順処理し頻度変化O(sqrt N)回だけ全値列を再構築するO(M sqrt N+Q log Q)。',anchor='Fenwick Tree')
put('abc449_f','T266:primary,T009:supporting,T008:alternative,T077:supporting,T064:supporting,T002:alternative,T085:supporting','黒点(R,C)を含む窓の左上位置は[R-h+1,R]×[C-w+1,C]。その和集合を全窓数から引く。rの出入イベントで走査し、等長w区間の開始点multiset隣接gap=max(0,右-左-w)の総和を更新して未被覆幅を保つO(N log N)。mapで重複数管理も可。source1はc端点圧縮と区間加算/min・達成長lazysegtreeで同計算量。',anchor='平面走査')
put('abc449_g','T127:primary,T022:supporting,T236:supporting,T086:supporting,T264:supporting,T060:supporting,T132:alternative,T196:supporting,T176:supporting','9n+Nを10で割り、N個の10冪の和の異なる値数へ帰着。F(x)=(1+x+...+x^9)^(M-1)、prefix係数G=F/(1-x)のN,N-9,...次係数和-floor(N/9)が答え。P F′=(M-1)P′Fからf[n]=(1/n)sum_{j=1..9}(Mj-n)f[n-j]でO(N)計算（n<MODで逆元あり）。FPS log/exp O(N log N)、FFT畳込み二分累乗O(N log N log M)の確認済み別解も可。',anchor='微分方程式を立式')
put('abc450_d','T264:primary,T077:supporting,T007:supporting','AiをmodKにしてsort。先頭を取りKを加え末尾へ戻すN回のdeque回転で、各剰余を最小にする全配置を調べ末尾-先頭の最小を得るO(N log N)。同じ答えはK-円環の最大隣接剰余gapなので配列走査でも可。',anchor='deque')
put('abc450_f','T002:primary,T022:supporting,T077:supporting','後退鎖が常在するので1からNへ到達できれば強連結。追加辺をX昇順sortし、最大到達r別の数をDP。(X,Y)を採るとX<=r<Yの全数がYへ、r>=Yは採否2通り。旧dp[X,Y)和を保存し[Y,N]を2倍してYへ保存和を加える。r<Xは将来Nへ届かず省略可。区間sum/乗算と点加算lazysegtreeでO(N+M log N)。',anchor='区間和取得')
rows['abc449_e']['source_indices']='0,1'
rows['abc449_f']['source_indices']='0,1'
save()
