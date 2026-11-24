"""Explicit problem-by-problem decisions for shard 2; no automatic acceptance rules."""
import csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parent;D={d['problem_id']:d for d in map(json.loads,(R/'corpus_sources.jsonl').open(encoding='utf-8'))};M=json.loads((R/'manifest.json').read_text(encoding='utf-8'))['problems'];B={r['problem_id']:r for r in csv.DictReader((R/'output_v3_2/problems.csv').open(encoding='utf-8-sig'))};path=R/'full_review/shard_2.tsv'
fields=['problem_id','scope','accepted','rejected','out_of_vocabulary','source_indices','evidence_quote','reason','review_status','uncertainty']
def append(block):
 rows=[];errors=[]
 for line in block.replace('|S|','len(S)').replace('|T|','len(T)').strip().splitlines():
  pid,tags,anchor,reason,*rest=line.split('|');gap=rest[0] if rest else '';unc=rest[1] if len(rest)>1 else ''
  accepted=[]
  for item in tags.split(',') if tags else []:
   m=re.fullmatch(r'(\d+)([pasci]?)',item);role={'':'primary','p':'primary','a':'alternative','s':'supporting','c':'concept','i':'analysis_concept'}[m[2]];accepted.append(f'T{int(m[1]):03d}:{role}')
  doc=D[pid];matches=[i for i,e in enumerate(doc['editorials']) if anchor in re.sub(r'\s+',' ',e['text'])]
  if matches:source=str(matches[0]);text=re.sub(r'\s+',' ',doc['editorials'][matches[0]]['text'])
  else:source='statement';text=re.sub(r'\s+',' ',doc['statement'])
  if anchor not in text:errors.append((pid,anchor));continue
  start=text.index(anchor);quote=text[max(0,start-20):min(len(text),start+len(anchor)+130)]
  accepted_ids={x.split(':')[0] for x in accepted};old=set(B[pid]['tag_ids'].split(' | '))-{''}
  rows.append(dict(problem_id=pid,scope='selected_tags' if unc else 'full',accepted=','.join(accepted),rejected=','.join(sorted(old-accepted_ids)) if not unc else '',out_of_vocabulary=gap,source_indices=source,evidence_quote=quote,reason=reason,review_status='needs_resolution' if unc else 'reviewed',uncertainty=unc))
 if errors:raise ValueError(errors)
 exists=path.exists()
 with path.open('a',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');
  if not exists:w.writeheader()
  w.writerows(rows)
 print('appended',len(rows),'total',sum(1 for _ in csv.DictReader(path.open(encoding='utf-8-sig'),delimiter='\t')))

if __name__=='__main__':
 append('''
abc272_e|154|調和級数|各A_i+t*iが[0,N)に入る時刻だけを列挙し時刻別バケットでMEXを走査する。総要素O(N log N)、M個の出力を含めO(N log N+M)。
abc272_h|127,257s,81s,132s,22s|多点評価|包除で選んだ不等式条件の個数を表す数え上げDPをFPSに変換する。積多項式の多点評価と指数級数との畳み込みでO(N log^2 N)。二乗DPのみの解法を主解扱いせず、確率DPへ自動変換しない。|多点評価
abc272_f|69,73s,60s|suffix array|Sを2回+aをN回+Tを2回+zをN回連結し接尾辞配列を作る。元の巡回開始位置に対応する接尾辞の順序から組数を線形走査しO(N)。
abc272_g|79,160s,134a,264s|ランダム|ランダムな2要素の差の約数Mを候補にし剰余の過半数を検査する。成功確率を増す定数回試行。素因数と4のみに絞る別解もあり、各試行O(sqrt(max A)+N*d)。
abc273_a|80|再帰関数|f(0)=1、f(n)=n*f(n-1)をそのまま再帰または階乗の積でO(N)計算する。余談のFibonacci・メモ化・剰余はこの入力の解法ではない。|階乗,基本算術
abc273_b|76,264s|割った余り|桁iごとに商と余りで四捨五入を行い元の位へ戻すO(K)シミュレーション。桁配列の繰上がりによるO(log X)実装も可能。
abc273_c|8,77s,85a|連想配列|値ごとの頻度を連想配列で求め値の降順に出力するO(N log N)。ソートで重複をまとめ異なる値の順位に対応させる座標圧縮としても実装できる。
abc273_d|8s,77s,64,76s|二分探索|行別・列別に壁座標をソートして連想配列で保持する。指示ごとに隣接壁を二分探索し移動先を境界で切る。O((N+Q) log N)。
abc273_e|15,13s,8s,130s|状態を木として保持|追加を新ノード、削除を親への移動として履歴を共有する永続スタック。SAVE/LOADはページからノードへの連想配列参照。O(Q log Q)またはハッシュで期待O(Q)。累積和は不要。
abc273_h|258,64s,81s|Stern|Stern–Brocot木の区間に分数を分割しノード寄与をマージする。片側に連続して進む深さを二分探索して圧縮しO(N(log N)^2 log max(a,b))。通常の二分木の全深さを実体化しない。
abc273_f|21,22s,77s|イベント|経験済みイベントの左右端L,Rと現在いる端を状態とする区間DP。次の左右イベントへ進み、壁なら対応ハンマーが区間内か検査する。ソート後O(N^2)。
abc273_g|22,60s,177s|残りの和|行iまで埋め残和2の列数xを状態にする。残和1の列数は全残和とxから決まり、各行の和0/1/2に応じた定数個の列選択で遷移する。O(N^2)。
abc274_a|264a|四捨五入|主解はB/Aの小数表示と四捨五入。整数だけの別解では1000倍した値を丸めて商・剰余で整数部と小数部を出す。O(1)。|実数出力,丸め処理
abc274_b|60|列目に置かれている箱の個数|全H*Wマスを読み列ごとに#の個数を加えるO(HW)の集計。全探索で候補解を探す処理やシミュレーションとは区別する。
abc274_c|22,130s|親のアメーバ|深さdepth[2i]=depth[2i+1]=depth[A_i]+1を生成順に計算するO(N)の木上の再帰的DP。辺を探索する必要はない。
abc274_d|22,262s|1 次元|移動の奇偶でx軸・y軸を独立にし、各軸で到達可能和のbool DPを±A_iへ遷移する。初手x正方向を固定しO(N^2 max A)。
abc274_e|17,22s|訪問済みの街|訪問済み都市・宝箱集合Sと現在地の最小時間をbitDPで管理する。速度はS中の宝箱数から決まり、必須都市を含む集合から原点へ戻る。O((N+M)^2*2^(N+M))。
abc274_h|72,59s,64s,129s,80s,37i,154i|Nimber|XORを加法とするNimber上のRolling Hashを構成し、区間XOR和のハッシュを線形結合する。二分探索でLCPを求め辞書順比較する。Nim積の定数回帰を前計算しO(N+Q log N)程度。Nim/MEXは体の説明上の概念でゲームを解かない。
abc274_f|65,77s,76s|シミュレーション|網の左端になる魚を全N通り固定し相対速度から各魚が網内にいる時間区間を作る。出入りイベントを時刻順に走査して重み和最大を求めO(N^2 log N)。
abc274_g|32,33s,31a,229s|最小点被覆|縦・横の障害物区切り区間を頂点とし各空白マスを辺とする二部グラフの最小点被覆へ帰着する。最小カットまたはKőnigによる最大マッチングをDinicでO((HW)^1.5)。
abc275_a|65a,77a|最も高い橋|主解は最大値とその位置の線形走査O(N)。各橋を全他橋と比較するO(N^2)全探索と高さ・添字をソートするO(N log N)別解も制約内。|最大値走査
abc275_b|264|オーバーフロー|各入力をMODで縮約して積を取り、ABC-DEFも非負剰余に直すO(1)の合同算術。積のオーバーフロー防止が解法上の焦点。
abc275_c|65,12a|正方形を列挙|1頂点と辺ベクトルを全列挙して90度回転から残り2頂点を求める。盤面を検査して4重カウントを割るか、頂点集合をsetで重複排除する。O((HW)^2)。
abc275_d|22,80s,8s|メモ化再帰|f(n)=f(floor(n/2))+f(floor(n/3))をメモ化し、引数floor(N/(2^x*3^y))のみを計算する。状態数O(log^2 N)、連想配列で記憶。
abc275_e|29,22s,236s|いる確率|dp[回数][位置]の確率を各ルーレット目へ1/Mで遷移し、端で反射・ゴールで吸収する。逆元を一度前計算してO(NMK+log MOD)。一般畳み込みは不要。
abc275_h|27,22s,10s,9a,12s,143i|二分木構造|障壁最大位置によるCartesian木を作り、部分木に一様ダメージjを与えた後の最小魔力をDPする。凸折れ線の傾き変化をsmall-to-largeとヒープ/多重集合で併合・削除してO(N log^2 N)。|Cartesian木,small-to-large
abc275_f|22|操作回数の最小値|dp[i][残す総和j][直前を残すか]で削除区間の開始ごとに1加算し最小化するO(NM)。入力配列を辞書として扱う必要も累積和もない。
abc275_g|44,77s,150c|下側凸包|各品物を価値1へ正規化した点(A/C,B/C)の下側凸包を作る。max(x,y)を各辺上で最小化しO(N log N)。整数重さの通常ナップサックDPではない。
abc276_a|73|文字目が a|末尾から文字aを線形検索し最初に見つけた添字を返すO(|S|)文字列処理。
abc276_b|77|隣接リスト|両端の隣接リストへ辺を加え、各リストを昇順ソートして次数と頂点番号を出力する。O(N+M log M)。|隣接リスト
abc276_c||末尾|右から最初の降下位置を見つけ、末尾でそれ未満の最大要素と交換して接尾辞を反転する前順列O(N)。大きな整数として演算する必要はない。|辞書順前順列
abc276_d|134,97a|素因数分解|各値の2と3の指数と残りzを分離しz一致を確認、指数の最小値との差を加算するO(N log max A)。gcdへ割った値を2,3だけで割り尽くす別解も実行可能。
abc276_e|66,5a,67a,182c|幅優先探索|Sを除くグリッドでSの異なる隣接2マスが連結か最大6組をBFS/DFSかDSUで判定するO(HW)。最大流を構成する必要はない。
abc276_h|212,86s,59s,264s|二次元累積和|長方形内の2の個数の偶奇をF2連立方程式にする。二次元累積和の4隅のみを変数として最大4Q変数へ圧縮しbitset掃き出し。零指定を最後に検査する。O(Q^3/w+N^2+NQ)。
abc276_f|1,77a,85a,236s|Fenwick tree|最大値の二重和をカード追加ごとの寄与で更新する。Fenwick木で値の小さい個数と大きい値の和を取りO(N log max A)。値域が大きい場合はソート・座標圧縮を使う別実装も可能。最後にK^2の逆元を掛ける。
''')


