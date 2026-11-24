from record_resolution_0 import *
put('abc418_g','T025:primary,T022:supporting,T066:supporting,T008:supporting,T017:analysis_concept','各演算の美しい言語について、長さu以下の接尾辞での受理ベクトルをキーにBFSで代表prefixを列挙しDFAを作る。uを増やして安定化し、全16演算でu<=3、状態<=7。各位置で全状態のsuffix個数と最大長を遷移してO(N)。powerset/bitDPはNFA変換の背景説明のみ。','有限オートマトン学習,正規言語',anchor='実際に全て')
put('abc419_e','T022:primary,T264:supporting,T077:alternative','同じ添字mod L群を一つの剰余kへ揃える費用f[i,k]=sum((k-A)%M)をO(NM)計算。群番号と剰余和jのminDPをk全遷移してO(LM^2)。別解source1は各群の実在値だけ遷移後、剰余環を2周し+sで緩和。桶ソートならO(NM)、通常ソートでも実行可能。',anchor='dp_{L, 0}')
put('abc419_f','T170:primary,T017:supporting,T025:supporting,T022:supporting,T257:alternative,T066:supporting','長さi、包含済みmask、Aho-Corasick状態vの個数DP。26文字の遷移先と出力maskを前計算しO(2^N L M*26)。source1の包除は禁じる文字列集合Fごとに該当出力状態を禁止する同オートマトンDPで同計算量。M=総文字数<=80。',anchor='dp の状態数')
put('abc419_g','T067:primary,T065:supporting,T059:alternative,T061:supporting,T117:supporting','端点以外の葉を除き次数2の鎖を長さ付き辺へ縮約。巡回次元K=M-N+1<=21で頂点<=2K+2、辺<=3K+1。縮約グラフの単純パスDFS列挙はO(N+K2^K)。別解はサイクル基底を64bit辺集合で表し全組合せCと固定パスP0のxorが単純パスか検査し同計算量。群は証明、逆元は使用しない。','サイクル基底,次数2鎖の縮約',anchor='本問題の解法')
save()
