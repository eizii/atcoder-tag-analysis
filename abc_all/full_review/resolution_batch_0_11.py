from record_resolution_0 import *
put('abc440_e','T010:primary,T077:supporting,T076:supporting,T012:supporting','Aを降順にし最大選択(K,0,...)から1枚を隣種類へ下げる状態をmaxheapで列挙、既出集合で重複を除く公式法は状態展開O(NX log(NX))。source1は非増加な種類列Bの左からの変更順を固定し、現在Biを増やすか次位置へ進んで増やす2遷移だけにする。状態(和,i,Bi-1,Bi)をheapに保持すれば重複なくO(N log N+X log X)。単純FIFO queueでは順序保証がない。',anchor='プライオリティーキュー')
put('abc440_f','T003:primary,T064:supporting,T001:alternative','z=#B=1。z=0なら2sumA-minA、z=NならsumA。その他は係数1のz頭に少なくとも1頭B=2が必要十分。A最小z頭の和を求め、B=2を含まなければその最大Aを最小B=2のAへ交換。値別B1/B2個数・和のsegtreeでkthと最小B2を二分探索し各更新O(log Amax)。3本のFenwickとbit上探索でも可。',anchor='実装方針')
put('abc440_g','T022:primary,T005:supporting,T067:alternative,T201:concept,T012:supporting,T077:supporting','各階の空マス成分をDSU/DFSで縮約し重みをコイン総数、隣階接触を辺にする。高階から梯子未使用/使用許容の最大回収DPと上下往復辺ごとの値を計算。隣へ戻る際の同成分二重計上だけを除くため各隣接リストの上位2値を保持し、全隣接対を列挙しない。コードのup1も含め各始点答えを前計算。V,E=O(FHW)、set重複除去とsort込みO(FHW log(HW)+Q alpha(HW))。',anchor='上から')
put('abc441_e','T086:primary,T060:supporting,T001:alternative,T003:alternative','D[i]=prefixA-prefixBとして求めるのはi<jかつD[i]<D[j]の組数。頻度と現在D未満総数を持ち、Aなら旧D頻度を足してD++、BならD--後の頻度を引く。差が±1/0だけなのでO(N)。頻度Fenwick/segtreeでprefix個数を問うO(N log N)別解も可。',anchor='O(N)')
put('abc441_g','T002:primary,T003:supporting,T120:supporting,T264:supporting','nodeは(たこ焼max,表数,裏数)。lazy更新は(反転回数a,最後の反転以後の加算b)で、後続反転が無ければb加算、有れば以前の加算を破棄して反転数を足す。a=0か正の偶数か奇数かでmaxを加算/リセットし表裏数を交換。合成とmappingがO(1)なのでO(N+Q log N)。',anchor='遅延伝播セグメント木')
rows['abc440_e']['source_indices']='0,1'
save()
