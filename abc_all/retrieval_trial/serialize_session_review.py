# -*- coding: utf-8 -*-
"""Serialize TEN explicit decisions authored in the current assistant session.

This is NOT an LLM batch runner or independent accuracy evaluation. Fixed authored
decisions below are a worked demonstration, with source-checked exact quotes.
Never use them as human gold. Run judge.py for a separately configured API study.
"""
import argparse, hashlib, json
from pathlib import Path
from judge import validate
BASE=Path(__file__).resolve().parent;OUT=BASE/'output'

def decision_cases():
    # tag tuple: ID, role, source ID, exact source anchor, mathematical justification.
    return {
    'abc007_3':dict(summary='格子をBFSし各マスの最短距離を求める。FIFOキューを使う。',complexity='O(RC) time, O(RC) space',tags=[
        ('T066','primary','editorial_0','幅優先探索','単位重みの格子を距離順に探索するBFSが主解である。'),
        ('T011','supporting','editorial_0','キュー','BFSの未処理頂点を先入れ先出しで管理する補助手法である。')],missing=['T055 最短経路：単位重みの最短距離を計算しているが候補にない。']),
    'abc168_d':dict(summary='部屋1からBFSし、発見元または深さが1小さい隣接頂点を親にする。',complexity='O(N+M) time and space',tags=[
        ('T066','primary','editorial_0','幅優先探索','距離の小さい順の探索で各部屋の深さと最短路の親を決める。'),
        ('T011','supporting','editorial_0','幅優先探索','明示されたBFSをFIFOキューで実装する補助手法として採用する。')],missing=['T055 最短経路：最短距離に沿う案内先の構築だが候補にない。']),
    'abc184_d':dict(summary='残り手数の期待値f(a,b,c)を、各硬貨を選ぶ確率で次状態の期待値から求める。',complexity='O(100^3) time and space',tags=[
        ('T026','primary','editorial_0','この式に従ってDP','状態値は残り手数の期待値であり、次状態との重み付き平均を計算する。'),
        ('T022','supporting','editorial_0','この式に従ってDP','硬貨3種類の枚数を状態とする漸化式を表に保存する。')],missing=[],
        alternatives=[dict(summary='開始枚数から増加後の状態へ確率質量を配り、初めて100枚に達する状態で手数×確率を合計する。解説の式とは別に導出した実行可能な別解。',complexity='O(100^3) time and space',tags=[
            ('T029','alternative','statement','確率','状態値を到達確率に変更し、a/(a+b+c)などで配る確率DPも全制約で成立する。'),
            ('T022','supporting','statement','確率','総枚数が増加する順で状態を処理するため循環しない。')])]),
    'abc319_c':dict(summary='9!通りの開示順を列挙し、8本の列について最初の2枚が同じかを判定する。',complexity='O(9! * 9) time, O(9) working space',tags=[
        ('T065','primary','editorial_0','順番','全ての開示順を列挙して失敗する順列を数える制約内の解法である。')],missing=['T017 bit DP / T029 確率DP / T022 DP：開示済み集合512状態の別解が候補にない。','T060 数え上げ：成功する開示順を数える手法が候補にない。']),
    'arc069_a':dict(summary='x=min(N,M//2)個を既存Sで作り、残るcから(M-2*x)//4個作る。',complexity='O(1) time and space',tags=[],missing=[],note='貪欲な定数時間式。266タグには貪欲法がないためno_matching_tagとする。Sccはピース名であり強連結成分ではない。',reject={'T052':'Sccはパズルの名称であり、有向グラフの強連結成分を計算していない。'}),
    'abc092_b':dict(summary='初期個数はX+sum_i(1+(D-1)//A_i)で求める。',complexity='O(N) time, O(1) additional space',tags=[],missing=[],note='単純な整数除算と総和。高度な数え上げタグは付けずno_matching_tag。PDFの別問題のMSTは採用しない。',reject={'T053':'PDFに含まれる別問題のMSTであり、Chocolateの解法ではない。','T022':'単純な整数除算で各人の消費数が直接決まり、DP状態や遷移を使わない。'}),
    'abc263_e':dict(summary='自己ループを除去した期待値漸化式を後ろから計算し、区間和を累積和で取得する。',complexity='O(N log MOD) time including inverses, O(N) space',tags=[
        ('T022','supporting','editorial_0','動的計画法','位置ごとの期待値を後ろから保存して遷移を計算する。'),
        ('T086','supporting','editorial_0','累積和','次の位置の連続区間に対するDP値の和を累積和で取得する。'),
        ('T236','supporting','editorial_1','左辺に移項','自己ループを移項してA_iによる除算を法上の逆元として行う。')],missing=['T026 期待値DP：主解のDP値が残り手数の期待値なのに候補にない。','T029 確率DP：到達確率を前から配るユーザ解説の別解が候補にない。'],alternatives=[
        dict(summary='次状態の期待値の区間和をSegment Treeで管理する実行可能な実装別解。',complexity='O(N(log N+log MOD)) time, O(N) space',tags=[('T003','alternative','editorial_0','segmenttree','区間のDP値の和をSegment Treeで取得する別実装である。')]),
        dict(summary='到達確率P_iを前から配り、各マスの滞在回数期待値(A_i+1)/A_iを掛けて合計する。',complexity='O(N log MOD) time including inverses, O(N) space',tags=[('T075','supporting','editorial_2','imos法','遷移先の連続区間へ同じ確率を配る処理にimos法を使う。')])]),
    'abc404_d':dict(summary='各園の訪問回数を0,1,2から選ぶ3^N通りを列挙する。',complexity='O(3^N N M) time, O(N+M) working space',tags=[
        ('T065','primary','editorial_0','通り全探索','各園の0,1,2回の訪問回数を全て調べ、各動物を2回見たか確認する。')],missing=[],reject={'T017':'bit DPへの応用例が余談として紹介されるだけで、本問題の解法は訪問回数の列挙である。'},alternatives=[
        dict(summary='2N個の訪問枠の部分集合をbit全探索する。実測AC例もある全制約向け別解。',complexity='O(4^N N M) time',tags=[('T061','alternative','editorial_1','bit 全探索','2N個の訪問枠の部分集合を列挙する手法が明示されている。'),('T117','supporting','editorial_1','bit 全探索','訪問枠の選択をビットマスクで表して各bitを調べる。')]),
        dict(summary='DFSで訪問回数を列挙し、各動物の観測回数を多倍長整数の2bitフィールドへ詰める。',complexity='O(3^N ceil(M/w)) time after input, w is word size',tags=[('T067','alternative','editorial_2','DFS中','探索木をDFSし、各園への訪問を分岐として列挙する。'),('T171','supporting','editorial_2','多倍長整数','各動物の観測回数を2bitずつ多倍長整数に保存する。'),('T117','supporting','editorial_2','bit','ビット並列演算で全動物の飽和加算と終了条件をまとめて処理する。')]),
        dict(summary='0,1,2の列を再帰で構築し訪問回数を列挙する。',complexity='O(3^N N M) time',tags=[('T080','supporting','editorial_4','再帰','訪問回数の列挙を再帰関数で実装する補助手法である。')])]),
    'abc405_g':dict(summary='Moの順序で区間を動かし、値域を平方分割して頻度総和と逆階乗積を管理する。',complexity='O(N sqrt(Q)+Q sqrt(N)) after preprocessing, assuming Q comparable to N',tags=[
        ('T084','primary','editorial_0','Segment Tree を使用していた部分を平方分割に差し替え','更新をO(1)、値域の積取得をO(sqrt(N))にして全制約で成立させる。'),
        ('T123','supporting','editorial_0','区間内に登場する','区間内の頻度と値のしきい値に対する集計クエリを処理する。')],missing=['T060 数え上げ / T236 モジュラ逆元：重複順列数を階乗と逆階乗で計算するが候補にない。'],note='Moは既存266タグにない概念。タグ体系自体の欠落として別記する。',reject={'T003':'解説はMo+Segment Treeが時間制限に間に合わない可能性を明示し、平方分割へ差し替えている。','T001':'導入の一般的な区間和の例に登場するだけで、本問題の解法として示されていない。','T120':'一般的なSegment Treeの適用可能性の説明であり、採用解法の具体的なモノイドではない。'}),
    'abc417_d':dict(summary='テンション1000以下の最終値を後ろからDPし、大きい初期値はBの累積和の二分探索で表内へ移す。',complexity='O(N*1001+Q log N) time, O(N*1001) space',tags=[
        ('T022','primary','editorial_0','DP テーブル','値域をP+Aの上限までに制限し、決定的な状態遷移の最終値を保存する。'),
        ('T064','supporting','editorial_0','範囲内に入るまでにプレゼントを受け取る個数','大きな初期値から減少する区間をBの累積和のlower_boundで求める実装を採用する。')],missing=['T086 累積和：大きなテンションの減少区間を飛ばす二分探索の前処理に使うが候補にない。'],note='Expectationはタイトルの語であり確率・期待値DPを意味しない。',alternatives=[
        dict(summary='全質問を同時処理し、順序付き連想配列と共通差分でテンションをシミュレートする。',complexity='O((N max(P)+Q) log Q) time',tags=[('T008','alternative','editorial_1','順序付き連想配列','テンションをキーとする順序付き連想配列にクエリ集合を格納する。'),('T076','alternative','editorial_1','シミュレート','全質問をまとめた状態を、各プレゼントに応じて差分更新する。')])])}

def main():
    a=argparse.ArgumentParser();a.add_argument('--input',type=Path,default=OUT/'pilot_requests_scoped.jsonl');args=a.parse_args()
    reqs={r['custom_id']:r for r in map(json.loads,args.input.open(encoding='utf-8'))};records=[]
    for pid,spec in decision_cases().items():
        r=reqs[pid];payload=json.loads(r['messages'][1]['content']);sources={s['source_id']:s['text'] for s in payload['source_texts']};solutions=[];accepted=set()
        for i,solution in enumerate([spec,*spec.get('alternatives',[])]):
            tags=[]
            for tid,role,sid,anchor,reason in solution['tags']:
                text=sources[sid];start=text.find(anchor)
                assert start>=0,(pid,sid,anchor)
                quote=text[start:min(len(text),start+max(100,len(anchor)))]
                if len(quote)<10:quote=text[max(0,start-20):]
                tags.append(dict(tag_id=tid,role=role,evidence_source=sid,evidence_quote=quote,reason=reason));accepted.add(tid)
            solutions.append(dict(solution_id=f's{i+1}',summary=solution['summary'],complexity=solution['complexity'],tags=tags))
        rejected=[dict(tag_id=c['tag_id'],reason=spec.get('reject',{}).get(c['tag_id'],'この問題で上に記載した解法の実装・遷移には使わず、検索上の類似だけでは採用できない。')) for c in payload['candidates'] if c['tag_id'] not in accepted]
        missing=spec['missing'];result=dict(problem_id=pid,solutions=solutions,rejected=rejected,candidate_insufficient=bool(missing),missing_concepts=missing,review_status='needs_review' if missing else 'reviewed',note=spec.get('note',''),no_matching_tag=not accepted)
        validate(result,payload)
        records.append(dict(problem_id=pid,result=result,reviewer='current conversation assistant',inference_mode='session_authored_worked_example_not_API_run',independent_gold=False,blind_to_historical_reference=False,prompt_sha256=hashlib.sha256(json.dumps(r['messages'],ensure_ascii=False).encode()).hexdigest()))
    with (OUT/'session_demo_judgments.jsonl').open('w',encoding='utf-8') as f:
        for record in records:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    print(json.dumps(dict(session_examples=len(records),candidate_insufficient=sum(r['result']['candidate_insufficient'] for r in records),all_quotes_validated=True)))
if __name__=='__main__':main()
