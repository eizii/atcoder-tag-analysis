from record_resolution_0 import *
put('abc420_f','T013:primary,T086:supporting,T060:supporting,T027:supporting,T022:supporting','各行を底に上向き.連長hを作り、単調stackでCartesian木をO(M)構成。部分木境界からiを最小とする区間の幅別個数（増加・平坦・減少の3区分）を得る。高さmin(h[i],floor(K/幅))を掛ける和はfloor(K/w),w*floor(K/w)等のprefix和でO(1)。面積制約を含め全体O(NM)。','Cartesian Tree',anchor='横幅ごとに')
put('abc421_f','T076:primary,T002:alternative,T003:alternative,T013:supporting,T012:alternative,T014:supporting','next配列で挿入をO(1)。削除ではxからとyからを交互に1歩進め、相手に着いた方向の区間和を出しnextを直結。訪問数は削除数の2倍以下で全体O(Q)。source1は削除無し最終順をstackで前計算し、位置上の区間sum/0代入lazysegtree、または通常segtreeと非0位置setの償却削除でO(Q log Q)。','連結リスト,削除数による償却解析',anchor='削除される要素数')
put('abc422_d','T081:primary,T080:supporting,T076:alternative,T264:supporting','総和Kをfloor(K/2),ceil(K/2)へ再帰分割し深さNの葉に置く。各層の最大最小差<=1が保たれ、最小アンバランスは2^N|Kなら0、他1。公式は長さ1から倍化する反復実装。source1の均等間隔に余りを配置する直接構成もO(2^N)。','均等分割構成',anchor='計算量は')
put('abc422_e','T079:primary,T065:supporting,T081:alternative,T080:supporting','異なる2点を乱択し決まる直線上の全点数を検査。過半数直線があれば1試行成功確率>1/4、100回で失敗約3.2e-13、O(100N)。source1の決定的別解は集合を半分に割り各側の過半数候補（高々3本）を併合して全点検査するO(N log N)。','直線方程式',anchor='乱択アルゴリズム')
put('abc422_f','T022:primary,T055:concept','経路長を初期券枚数とし、状態(v,n)から隣接(u,n-1)へn*W[v]で遷移。最適路に重複頂点は無く初期枚数<=N-1。全(1,n)を0で開始するDAG DPをn降順に計算し(i,0)を得るO(NM)、二層配列でO(N)メモリ。',anchor='DAG になっている',uncertainty='Dijkstra別解は元解説も時間内かもしれないと留保しており、実行時間未検証のため採用しない。')
save()
