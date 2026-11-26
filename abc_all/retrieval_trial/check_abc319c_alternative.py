"""Check the claimed O(2^9 * 9 * 8) subset-count DP against permutation counts.

Same subset transition can instead propagate probability mass 1/(9-|S|).
This verifies feasibility/correctness of ONE derived alternative, not tag accuracy.
"""
import itertools, json, math
from fractions import Fraction
from pathlib import Path
LINES=((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))

def subset_count(values):
    dp=[0]*512;dp[0]=1
    for mask in range(512):
        for v in range(9):
            if mask>>v&1:continue
            bad=False
            for line in LINES:
                if v not in line:continue
                opened=[u for u in line if mask>>u&1]
                if len(opened)==1 and values[opened[0]]==values[v]:bad=True;break
            if not bad:dp[mask|1<<v]+=dp[mask]
    return dp[-1]

def permutation_count(values):
    count=0
    for order in itertools.permutations(range(9)):
        rank=[0]*9
        for t,v in enumerate(order):rank[v]=t
        for line in LINES:
            a,b,c=sorted(line,key=rank.__getitem__)
            if values[a]==values[b]:break
        else:count+=1
    return count

def main():
    cases=[list(range(9)),[1,1,2,3,4,5,6,7,8],[1,2,1,3,2,4,5,6,7],[1,2,3,2,3,1,3,1,2]]
    rows=[]
    for values in cases:
        d=subset_count(values);b=permutation_count(values);assert d==b
        rows.append(dict(values=values,valid_orders=d,permutation_orders=b,success_probability=str(Fraction(d,math.factorial(9)))))
    out=Path(__file__).resolve().parent/'output'/'alternative_witness_check.json'
    out.write_text(json.dumps(dict(problem_id='abc319_c',checks=rows,all_match=True,complexity='O(2^9 * 9 * 8)',not_an_accuracy_metric=True),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(cases=len(rows),all_match=True)))
if __name__=='__main__':main()
