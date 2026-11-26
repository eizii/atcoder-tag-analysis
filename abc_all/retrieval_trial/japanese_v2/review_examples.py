"""Three session-authored worked examples on final bilingual candidate inputs.

These are not external model outputs, human gold or an accuracy benchmark.
"""
import hashlib,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE/'bilingual_output'
sys.path.insert(0,str(BASE.parent));from judge import validate

SPECS={
 'abc007_3':[
  ('BFSで距離の層ごとに格子を探索する。','O(RC) time and space',[
   ('T066','primary','editorial_0','幅優先探索','重みなし格子を始点から距離の近い順に探索する。'),
   ('T055','supporting','editorial_0','幅優先探索','単に到達性を調べるのでなく最小の移動回数を求めるため最短経路のタグも該当する。'),
   ('T011','supporting','editorial_0','キュー','BFSの未処理マスを先入れ先出しで処理する。')])],
 'abc263_e':[
  ('各位置の残り回数の期待値を後ろから求め、自己遷移を移項し、区間和を累積和で取得する。','O(N log MOD) time including inverses, O(N) space',[
   ('T026','primary','editorial_0','動的計画法','DPの状態値が残りの試行回数の期待値である。'),
   ('T022','supporting','editorial_0','動的計画法','位置を状態とする漸化式で次の位置の値を再利用する。'),
   ('T086','supporting','editorial_0','累積和','次の連続する位置のDP値を区間和で取得する。'),
   ('T236','supporting','editorial_1','左辺に移項','自己ループを除いた後にA_iによる法上の除算を逆元で計算する。')]),
  ('到達確率P_iを前から配り、各位置での期待試行回数(A_i+1)/A_iを掛けて合計するユーザ解説の別解。','O(N log MOD) time including inverses, O(N) space',[
   ('T029','alternative','editorial_2','到達する確率','状態値を到達確率にした配るDPを実際に構成している。'),
   ('T075','supporting','editorial_2','imos法','等確率で遷移する連続区間への加算をimosで処理する。')])],
 'abc319_c':[
  ('9!通りの開示順を列挙して成功する順番を数える。','O(9! * 9) time',[
   ('T065','primary','editorial_0','順番','9個のマスの全開示順を調べる実行可能な全探索である。'),
   ('T060','supporting','editorial_0','順番','条件を満たす順番の個数を数え全順序数で割る。')]),
  ('開示済み集合Sの成功確率を保存し、次のマスを1/(9-|S|)ずつ選ぶ。列の最初の2枚が等しくなる遷移を捨てる。解説から別途導出した別解。','O(2^9 * 9 * 8) time, O(2^9) space',[
   ('T017','alternative','editorial_0','順番','開示済みの集合を9bitのマスクで表す512状態のDPである。'),
   ('T029','alternative','editorial_0','順番','同じ集合へ至る確率質量を足し、成功する全開示状態への確率を求める。'),
   ('T022','supporting','editorial_0','順番','集合の大きさが増える順に遷移を計算する。整数版で4盤面の全順列との一致も確認済み。')])],
}
def main():
    requests={r['custom_id']:r for r in map(json.loads,(OUT/'pilot_requests_scoped.jsonl').open(encoding='utf-8'))};records=[]
    for pid,specs in SPECS.items():
        request=requests[pid];payload=json.loads(request['messages'][1]['content']);sources={s['source_id']:s['text'] for s in payload['source_texts']};solutions=[];accepted=set()
        for i,(summary,complexity,tags) in enumerate(specs):
            labels=[]
            for tid,role,sid,anchor,reason in tags:
                text=sources[sid];pos=text.find(anchor);assert pos>=0,(pid,anchor);quote=text[pos:pos+120]
                if len(quote)<10:quote=text[max(0,pos-20):]
                labels.append(dict(tag_id=tid,role=role,evidence_source=sid,evidence_quote=quote,reason=reason));accepted.add(tid)
            solutions.append(dict(solution_id=f's{i+1}',summary=summary,complexity=complexity,tags=labels))
        rejected=[dict(tag_id=c['tag_id'],reason='この例で記載した解法では使用を確認していない。候補への追加や類似度だけでは採用しない。') for c in payload['candidates'] if c['tag_id'] not in accepted]
        result=dict(problem_id=pid,solutions=solutions,rejected=rejected,candidate_insufficient=False,missing_concepts=[],review_status='needs_review')
        validate(result,payload)
        records.append(dict(problem_id=pid,result=result,inference_mode='current_conversation_authored_example_not_external_API',independent_gold=False,scope='Specified reference solutions and one explicitly derived alternative only; other possible solutions not exhaustively audited',prompt_sha256=hashlib.sha256(json.dumps(request['messages'],ensure_ascii=False).encode()).hexdigest()))
    with (OUT/'session_examples.jsonl').open('w',encoding='utf-8') as f:
        for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print(json.dumps(dict(examples=3,all_quotes_and_candidate_ids_validated=True,independent_gold=False)))
if __name__=='__main__':main()
