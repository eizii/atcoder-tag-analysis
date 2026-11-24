from record_resolution_0 import *
put('abc437_g','T032:primary,T230:supporting,T178:supporting,T067:supporting,T076:supporting,T264:supporting','木を二部彩色し頂点v・色kの3N状態を作る。degree回の色巡回から色別削除回数Avkを求め、source→左色と右色→sinkに容量Avk、木辺の異色組に容量1。最大流N-1なら実現可能。辺数O(N)、流量O(N)なので増加路法O(N^2)で制約内。各木辺の流れた色組を指定し、現在両端色が一致する指定辺を走査削除してO(N^2)で順列復元。',anchor='最大流問題')
put('abc438_c','T013:primary,T076:supporting','左からstackへ要素を足し末尾4個同値なら4回pop。操作順によらず最終長が一定なのでこの削除順で最小を得る。各要素push/pop高々一回のO(N)。',anchor='スタック')
put('abc438_g','T001:primary,T077:supporting,T097:supporting,T264:supporting,T086:supporting,T003:alternative','gcd(N,M)ごと同剰余列へ分け互いに素な小問題にする。Bを添字Ni mod Mの順に並べると、各Akと組になるBは循環連続区間。完全周期分を集計し残りを高々2区間へ分割。x=Ak昇順offlineでB<=xの値和/個数をFenwickに入れ、区間sum min(x,B)を得る。segtreeでも可。O((N+M)log(N+M))。',anchor='Fenwick Tree')
put('abc439_a','T176:alternative,T117:alternative','2をN回掛けて2^Nを得て2Nを引くO(N)、N<=11。元解説に二分累乗O(log N)と1<<Nのbitshiftも実行例があり双方を別解として確認。','算術',anchor='繰り返し二乗法')
put('abc439_d','T008:primary,T077:alternative,T012:supporting,T060:supporting,T264:supporting','Aj=5tの位置jごと、左右の7t個数と3t個数を掛ければ条件を満たす。前方・後方走査のmap頻度でO(N log N)。source0はt別イベントを位置順sortし全組からjが中央の組を除外する同計算量別解。setはt候補の列挙だけ。',anchor='イベントソート')
put('abc439_f','T014:primary,T001:alternative,T003:alternative,T060:supporting,T086:supporting,T022:supporting','相異なる列が門松的なのは先頭が上昇・末尾が下降。各位置iで左の小値数beg[i]、右の小値数fin[i]を順序統計木/Fenwick/segtreeで求める。長さ3分sum beg*fin、長さ>=4分はS=2S+begの重みprefix漸化式でsum S*finを加算。O(N log N)。',source=1,anchor='累積和の要領')
rows['abc439_d']['source_indices']='0,1'
rows['abc439_f']['source_indices']='0,1'
save()
