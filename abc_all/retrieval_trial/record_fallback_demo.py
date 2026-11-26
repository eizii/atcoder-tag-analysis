"""Worked example of the current assistant's all-label fallback on ABC319 C.

No external API invocation. No independent/human-gold accuracy claim.
"""
import hashlib,json
from pathlib import Path
from judge import validate
BASE=Path(__file__).resolve().parent;OUT=BASE/'output'
def main():
    r=json.loads((OUT/'fallback_request_abc319c.jsonl').read_text(encoding='utf-8'));p=json.loads(r['messages'][1]['content'])
    text=next(s['text'] for s in p['source_texts'] if s['source_id']=='editorial_0');quote=text[:150]
    def tag(tid,role,reason):return dict(tag_id=tid,role=role,evidence_source='editorial_0',evidence_quote=quote,reason=reason)
    result=dict(problem_id='abc319_c',solutions=[
        dict(solution_id='s1',summary='9!通りの開示順を全列挙し、成功した順序数を数える。',complexity='O(9! * 9)',tags=[tag('T065','primary','全開示順の列挙が実行可能な主解である。'),tag('T060','supporting','成功する開示順の個数を数え、全順序数9!で割る。')]),
        dict(solution_id='s2',summary='開示済み集合Sの確率を保存し、未開示マスを1/(9-|S|)で追加する。同一直線上の最初の2枚が等しくなる遷移を除く。全開示状態への到達確率が答え。解説から別途導出した別解。',complexity='O(2^9 * 9 * 8) time, O(2^9) space',tags=[tag('T017','alternative','開示済み集合を9bitマスクで表す512状態のDPである。'),tag('T029','alternative','状態値は成功条件を満たして集合Sに到達する確率質量であり、確率を配る。'),tag('T022','supporting','集合サイズが増加する順に漸化式を計算する。'),tag('T060','supporting','同じ遷移で順序数を数える整数DPと、確率を保存するDPが対応する。')])],rejected=[],candidate_insufficient=False,missing_concepts=[],review_status='reviewed')
    accepted={t['tag_id'] for s in result['solutions'] for t in s['tags']}
    result['rejected']=[dict(tag_id=c['tag_id'],reason='記載した全探索解法および集合確率DP別解の計算には使わない。') for c in p['candidates'] if c['tag_id'] not in accepted]
    validate(result,p)
    record=dict(problem_id='abc319_c',result=result,reviewer='current conversation assistant',inference_mode='session_authored_fallback_worked_example_not_API_run',independent_gold=False,blind_to_historical_reference=False,trigger='candidate_insufficient in session_demo_judgments.jsonl',prompt_sha256=hashlib.sha256(json.dumps(r['messages'],ensure_ascii=False).encode()).hexdigest(),alternative_verification='alternative_witness_check.json; four exact permutation comparisons')
    (OUT/'session_fallback_judgment.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('fallback schema and quotes valid')
if __name__=='__main__':main()
