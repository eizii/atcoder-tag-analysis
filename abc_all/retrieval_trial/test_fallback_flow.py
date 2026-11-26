"""Contract test: simulate provider replies; never contact an API or score tags."""
import json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
import run_with_fallback as driver
BASE=Path(__file__).resolve().parent
def main():
    calls=[]
    def simulated_run(cmd,check):
        script=Path(cmd[3]).name;args=cmd[4:];calls.append(script)
        get=lambda k:args[args.index(k)+1]
        dest=Path(get('--output'))
        if script=='build_requests.py':
            assert json.loads(Path(get('--problem-ids-file')).read_text())==['abc319_c']
            dest.write_text((BASE/'output/fallback_request_abc319c.jsonl').read_text(encoding='utf-8'),encoding='utf-8');return
        requests=driver.readrows(Path(get('--input')))
        fallback=dest.name=='fallback.jsonl'
        with dest.open('w',encoding='utf-8') as f:
            for r in requests:
                insufficient=r['custom_id']=='abc319_c'
                result=dict(problem_id=r['custom_id'],result=dict(candidate_insufficient=insufficient,review_status='reviewed'),prompt_sha256='fixture_only')
                f.write(json.dumps(result)+'\n')
        if fallback:assert get('--max-tokens')=='20000'
    (BASE/'cache').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fallback_contract_',dir=str(BASE/'cache')) as tmp:
        argv=['run_with_fallback.py','--base-url','http://not-called.invalid/v1','--model','fixture','--output-dir',tmp,'--pilot']
        with patch.object(sys,'argv',argv),patch.object(driver.subprocess,'run',simulated_run):driver.main()
        merged=driver.readrows(Path(tmp)/'merged.jsonl');assert len(merged)==20
        flagged=next(r for r in merged if r['problem_id']=='abc319_c');assert flagged['result']['review_status']=='needs_review' and flagged['fallback_from_prompt_sha256']=='fixture_only'
    assert calls==['judge.py','build_requests.py','judge.py']
    print(json.dumps(dict(fallback_flow_contract_passed=True,simulated_provider=True,real_api_calls=0)))
if __name__=='__main__':main()
