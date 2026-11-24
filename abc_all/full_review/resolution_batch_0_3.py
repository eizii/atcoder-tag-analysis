from record_resolution_0 import *
put('abc424_f','T002:primary,T003:alternative,T059:alternative,T079:supporting,T001:supporting','非交差区間族は一点を覆う区間が包含順になる。各点を含む最短区間を双対/lazysegtreeの区間chmin・点取得で保持し両端の包含を検査するO((N+Q)log N)。括弧列の区間sumとprefix最小のsegtree別解も可。hash別解は両端に同一乱数を置き区間xor=0をFenwickで検査、誤判定率<=Q/2^B。',anchor='セグメント木による解法1')
put('abc424_g','T022:primary,T150:supporting,T077:supporting,T100:analysis_concept','B降順に曲をソート。j曲目まで、採用数k、必要延べ人数sの最大得点DPで、採る/採らないを遷移しs<=Rk=sum min(Ai,k)のみ許す。全prefix条件の十分性は最大残容量へ割当てる交換/帰納法。O(NM^3)、NM<=1e4で実行可能。Havel-Hakimi型手順は条件の証明。',anchor='dp[j][k][s]')
put('abc425_d','T066:primary,T076:supporting','世代ごとの新黒マス集合Tを保持。前世代で黒くなったマスの隣だけを次候補とし、現時点の黒近傍数1の白を全て列挙し終えてから一斉に黒にする。各マスは1度だけ黒になり4近傍検査なのでO(HW)、空集合で停止。',anchor='T_i=')
put('abc425_e','T177:primary,T022:supporting,T060:supporting,T134:alternative,T122:alternative,T236:supporting,T202:supporting','多項係数S!/prod Ci!を逐次二項係数の積にする。Pascal表mod MをS<=5000までO(S^2)前計算し各ケースO(N)。source1はMの素数冪ごとに階乗p指数とp除去部を分離し後者だけ逆元、CRT/Garnerで復元。source2はMの全素因数除去部と各指数を直接mod Mで合成しCRT不要。いずれも合成M全対応。',anchor='二項係数を')
put('abc425_f','T017:primary,T021:alternative,T022:supporting,T060:supporting,T177:supporting','残位置集合maskから1字ずつ消すDP。同じ残文字の連続部分では左端だけ削除可として文字列遷移の重複を除きO(N2^N)。source1は先頭に番兵を加え区間を左端文字へ縮約するDP。最終分割の左右代表文字が異なる場合だけdp左*dp右*C(長さ-2,左長-1)を加算しO(N^3)。二項係数は操作順の交ぜ方。',anchor='bit DP')
for pid,indices in {'abc421_f':'0,1','abc422_d':'0,1','abc422_e':'0,1','abc419_e':'0,1','abc419_f':'0,1,2','abc423_e':'0,1','abc424_e':'0,1,2','abc425_e':'0,1,2','abc425_f':'0,1'}.items():rows[pid]['source_indices']=indices
save()
