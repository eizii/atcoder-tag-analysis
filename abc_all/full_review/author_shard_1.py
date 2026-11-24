"""Individually authored reviews for manifest indices 750..1499."""
import csv,json,re,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))}
P=R/'full_review/shard_1.tsv'
FIELDS=['problem_id','scope','accepted','rejected','out_of_vocabulary','source_indices','evidence_quote','reason','review_status','uncertainty']
def norm(x):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',x))
def save(entries):
 old={r['problem_id']:r for r in csv.DictReader(P.open(encoding='utf-8-sig'),delimiter='\t')} if P.exists() else {}
 for pid,tags,anchor,reason,gap,source in entries:
  text=D[pid]['statement'] if source=='statement' else D[pid]['editorials'][int(source)]['text']
  n=norm(text);a=norm(anchor);assert a in n,(pid,anchor)
  pos=n.index(a);quote=n[max(0,pos-40):min(len(n),pos+len(a)+80)].strip()
  old[pid]=dict(problem_id=pid,scope='full',accepted=tags,rejected='',out_of_vocabulary=gap,source_indices=str(source),evidence_quote=quote,reason=reason,review_status='reviewed',uncertainty='')
 with P.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS,delimiter='\t');w.writeheader();w.writerows(old.values())
 print('authored reviews',len(old))

def E(pid,tags,anchor,reason,gap='',source=0):return pid,tags,anchor,reason,gap,source
if __name__=='__main__':
 save([
 E('abc167_e','T177:primary,T060:supporting,T176:supporting,T236:supporting','M ×','同色境界k本をN-1本から選び、先頭色M・異色境界M-1の積M*C(N-1,k)*(M-1)^(N-1-k)をk<=Kで合計。階乗逆元と冪計算を用いてO(N+K log N)。'),
 E('abc167_f','T077:primary,T128:supporting,T073:supporting','ソート','各文字列を必要な閉じ括弧Aと残る開き括弧Bへ線形圧縮。B>=A群をA昇順、他群をB降順にソートし、残高が負にならず最後0か検査。O(総文字数+N log N)。','貪欲法'),
 E('abc168_a','T264:primary','n % 10','N mod 10で一の位を取り、3・0,1,6,8・それ以外の区分で読みを決定。固定個数の分岐でO(1)。'),
 E('abc168_b','T073:primary','文字列操作','長さを調べ、K超なら先頭K文字を切り出し末尾に...を連結、他は原文。O(|S|)。'),
 E('abc168_c','','余弦定理','時針角2π(H+M/60)/12と分針角2πM/60の差から、余弦定理で距離sqrt(A²+B²-2AB cosθ)を計算。O(1)。対象の266タグに余弦定理・三角関数のタグはない。','余弦定理,三角関数'),
 E('abc168_d','T066:primary,T055:supporting','幅優先探索','頂点1からBFSで無向グラフの距離と親を求め、距離が1小さい親を道しるべにする。連結制約より全頂点へ到達し、O(N+M)。'),
 E('abc168_e','T097:supporting,T008:primary,T060:primary,T176:supporting','既約分数','ゼロベクトルを別処理し、(A,B)をgcdで符号付き既約方向へ正規化。直交する方向の頻度a,bごとに(2^a+2^b-1)を掛け、空集合を引いてゼロ単体を加える。MapとgcdでO(N log max|A,B|+N log N)。'),
 E('abc168_f','T085:primary,T077:supporting,T066:primary','重複を除いてソート','全線分端点のx,yを座標圧縮し、区画間の壁を構築、原点区画からBFSして到達区画面積を合計。外周に達すればINF。O((N+M)^2)。'),
 E('abc169_a','','計算結果を出力','二つの整数の積A*Bを直接計算するO(1)算術。独立した対応タグなし。','基本算術'),
 E('abc169_b','T171:alternative','128bit','0の存在を先に確認。非0列では積pを保ち、p>10^18/aなら打切り、または多倍長/128bit積が閾値を超えた時点で打切る。O(N)、多倍長は各段高々一定桁に留める実行可能別解。','オーバーフロー対策'),
 E('abc169_c','','100 倍','Bを小数文字列から100倍の整数bへ正確に変換し、A*bの整数除算100で切捨てる。O(入力桁数)。浮動小数の直接乗算は使わない。','固定小数点,整数演算'),
 E('abc169_d','T134:primary','素因数分解','試し割りで素因数指数eを取り出し、1+2+...+k<=eとなる最大kを各素因数で加算。O(sqrt N)の素因数分解が支配する。','貪欲法'),
 E('abc169_e','T077:primary','中央値','A列・B列を別々に昇順にソート。奇数は中央上限-中央下限+1、偶数は中央2要素の和の上限-下限+1を返す。O(N log N)。','中央値の単調性'),
 E('abc169_f','T150:primary,T022:supporting,T060:supporting','dp[i][ j]','先頭i要素を処理した選択和jの組数を状態とする。要素をUへ選ぶ場合j+A_iへ、Tだけ/どちらにも入れない2通りをjへ加算。O(NS)の数え上げナップサックDPであり確率状態ではない。'),
 E('abc170_a','T065:alternative','if 文を5','5個の値を順に検査して0の添字を返す全探索、または15-sum(x)を直接返す算術別解。個数固定でO(1)。'),
 E('abc170_b','T065:primary,T264:alternative','X + 1 通り','鶴aを0..Xまで列挙して2a+4(X-a)=Yか検査しO(X)。別解は2X<=Y<=4XかつY偶数というO(1)の剰余・範囲判定。'),
 E('abc170_c','T065:primary','順に調べ','候補をX,X-1,X+1,...の近距離・小さい値優先で列挙し、禁止列にない最初の候補を返す。値範囲0..101で十分、直接線形会員検査でもO(XN)。'),
 E('abc170_d','T253:primary,T077:supporting','エラトステネス','Aをソート・頻度集計し、存在するxの真の倍数を不適として篩う。頻度1かつ他要素の倍数でない値を数える。O(Amax log Amax+N log N)。配列名dpは倍数のマーキングで、依存状態の最適化/数え上げDPを意味しない。'),
 E('abc170_e','T009:primary','順序付き多重集合','園ごとのレートMultisetと、非空園の最大レートの全体Multisetを維持。移動元/先の旧最大を外し、園内変更後の最大を再挿入して全体最小を返す。O((N+Q)log N)。'),
 E('abc170_f','T187:primary,T055:supporting,T010:supporting','Dijkstra','(マス,方向)を状態とし、前進を1/Kコスト・転向をコスト切上げとして最短距離を求めるDijkstra。整数化した余剰歩数で同等に実装可能で、状態4HW、O(HW log(HW))。')
 ])

