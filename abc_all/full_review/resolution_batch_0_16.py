from record_resolution_0 import *
put('abc451_c','T010:primary,T076:supporting,T009:alternative','高さをminheapへ追加。削除問は最小がh以下の間popし、各問後heapサイズを出す。木は一度しか削除されず全O(Q log Q)。multisetで同じ先頭削除を行っても同計算量。',anchor='削除の回数')
put('abc451_d','T012:primary,T077:supporting,T022:supporting,T065:supporting,T073:supporting,T117:supporting','2冪を桁数別P[i]へ分類し、良い整数集合X[k]=union_{i=1..k}{x*10^i+p:x∈X[k-i],p∈P[i]}をsetで重複除去してk=1..9まで列挙。個数<=5^9-1、実数1257874なので全候補sortしてN番目を返せる。文字列連結の集合DPで値重複を数えない。',anchor='X_k=')
put('abc451_e','T067:primary,T053:alternative,T234:supporting,T233:supporting,T005:supporting,T077:supporting,T130:concept','根1に対しiの祖先候補はA1j+Aji=A1i。その中で距離Aij最小のjを親にして唯一候補木をO(N^2)構築、全始点DFSで全距離一致をO(N^2)検査する。source1は完全距離グラフのMSTが唯一の候補。密Prim O(N^2)または重み<=9999のbucket Kruskal O(N^2 alpha N+Amax)で構築後同じ検査。',anchor='各頂点を始点として DFS')
put('abc451_g','T059:primary,T089:supporting,T067:supporting,T117:supporting,T060:supporting','全域木DFSの根xor距離Avを求め、各辺のWe xor Au xor Avから上位bitの異なるxor基底を作る。基底で各Avを貪欲最小化したBvは線形写像fで、最小walk xorはBu xor Bv。Binary Trieへ順に追加し上位bitからK以下となる既出相手数を数えるO((N+M)*30)。','xor線形基底,GF(2)商空間の標準形',anchor='Binary Trie')
put('abc452_d','T025:primary,T022:supporting,T064:alternative,T073:supporting,T060:supporting','右端iと貪欲に一致したTのprefix長j別に開始位置数を持つDP。新substringのj=0を1増やしSi=T[j]ならj+1へ移す。全右端のj<|T|を足しO(|S||T|)。source1はnext文字位置表から各左端で最早一致終端をO(|T|)求める。source2は文字別位置列の二分探索で同処理をO(|S||T|log|S|)。ランダムな選択確率を保持するDPではない。',anchor='配る DP')
for pid,indices in {'abc451_e':'0,1','abc452_d':'0,1,2'}.items():rows[pid]['source_indices']=indices
rows['abc448_f']['accepted']=rows['abc448_f']['accepted'].replace(',T062:analysis_concept','')
old=set(OLD['abc448_f']['tag_ids'].split(' | '))-{''}
rows['abc448_f']['rejected']=','.join(sorted(old-{a.split(':')[0] for a in rows['abc448_f']['accepted'].split(',')}))
rows['abc448_f']['reason']=rows['abc448_f']['reason'].replace('Moはこの順序付けの由来でありクエリ処理を実行しない。','Mo内部の順序付けが由来だが、最悪距離上界のある決定的構成。')
save()
