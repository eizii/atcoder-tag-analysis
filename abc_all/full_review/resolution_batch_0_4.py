from record_resolution_0 import *
put('abc426_c','T076:primary,T002:alternative,T009:alternative,T010:alternative,T012:alternative','版別台数を持ち最古OからXiまで加算しYiへ移しOを増加する。Oは二度戻らずO(N+Q)。source1は(版,台数)のmultiset/minheapをまとめて削除挿入しO((N+Q)log(N+Q))、区間sum/0代入lazysegtreeでも可。setは台数を別配列に集約して版キーのみ管理するなら可能（pairをそのままsetへ変更は不可）。',anchor='最古のバージョン')
put('abc426_d','T073:primary','最終文字bの元個数Cbと最長連長Mbを数える。操作しないbは連続区間内に限られ、外のbは2回、反対文字は1回必要十分。min_b[2(Cb-Mb)+(N-Cb)]をO(N)で計算。','連長圧縮,操作回数の下界と構成',anchor='C_0-M_0')
put('abc426_f','T002:primary,T003:supporting,T064:supporting,T001:alternative','未在庫切れ商品数c*kを暫定購入数にし区間在庫を-k。区間minが負の間、segtree max_rightでその位置を探し不足分を答えから引き、在庫をINFに、個数を0にする。各商品1イベントなのでO((N+Q)log N)。個数sum用は通常segtreeまたはFenwick。元解説のO(N+QlogN)表記よりこの実装上界を採る。',anchor='在庫切れイベント')
put('abc426_g','T081:primary,T080:supporting,T150:supporting,T022:supporting','添字区間を分割統治し中央を跨ぐクエリをその節で処理。中央左向き・右向きの容量<=500ナップサックDPを作り、各問は容量配分jの最大dp左[L,j]+dp右[R,C-j]を走査。片側の問は再帰へ。O(K(N log N+Q))、K=max C。',anchor='列に対する分割統治')
rows['abc426_c']['source_indices']='0,1'
save()
