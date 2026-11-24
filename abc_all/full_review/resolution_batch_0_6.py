from record_resolution_0 import *
put('abc429_d','T077:primary,T083:supporting,T086:alternative,T008:alternative','座標順に同一点人数Pをまとめ円環2周へ伸ばす。各始点iで人数和>=Cとなる最短右端Riを尺取りし、その人数和Yiに直前地点からiまでの整数開始位置数を掛ける。O(N log N)、総和のみで期待値計算ではない。prefix和からRiを得る実装やmap集計も可。',anchor='尺取り法')
put('abc429_e','T066:primary,T011:supporting,T092:alternative,T079:supporting,T117:supporting','全安全頂点を始点に(start,v,距離)の多始点BFS。各頂点に異なる始点の最初2件だけ保存展開し、その距離和を出すO(N+M)。source1のColor Codingは安全頂点を2色に分け各色BFSを反復。ID各bitによる決定的分割なら必ず最近2点が分離されO((N+M)log N)。乱択D回なら各頂点失敗2^-D、全体失敗<=N2^-D。',anchor='始点からの最短距離だけではなく')
put('abc429_f','T003:primary,T055:concept,T120:supporting,T022:supporting','高さ3では最短路に左移動が不要。各列の壁状態を、前列3距離から今列3距離へのmin-plus 3x3写像にする。合成をモノイドとしてsegtreeに載せ、一マス反転は当該列だけ更新。O(N+Q log N)、全体写像の上→下距離に水平N-1を加える。set別解の実根拠は無いため採用しない。',anchor='モノイド')
put('abc430_f','T075:primary,T086:supporting,T073:supporting','値iの可能順位は区間[l,r]。l=左向き連続R数+右向き連続L数+1、r=N-左連続L数-右連続R数。強制的に前後となる連鎖以外を左右に自由挿入でき区間全体が実現する。4種連長を前後走査し各[l,r]を差分+1、累積して全CiをO(N)計算。',anchor='定理2.')
put('abc430_g','T002:primary,T003:supporting,T080:supporting,T117:supporting,T064:alternative','Beatsノードに集合OR/AND bitmaskと要素数max/達成数を保持。更新対象bitがOR xor ANDに無ければ全要素へ同じ増減を一括適用、他は子へ再帰。失敗で不一致bit数が減り境界更新の増加O(Q log N)なのでO((N+Q)log N+60N)。別解は60本の01区間代入木で真に変わる区間だけ二分探索列挙しmax/個数の区間加算木へ適用、全区間数O(Q)。','Segment Tree Beats',anchor='mapping が成功する条件')
rows['abc429_e']['source_indices']='0,1'
save()

