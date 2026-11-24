from pathlib import Path
p=Path('abc_all/full_review/append_shard_1_1390.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace("','すべて','","','全て','").replace("','転倒','","','コストの最小値','").replace("T022:primary,T027:supporting,T067:alternative,T066:alternative','dp'","T022:primary,T027:supporting,T067:alternative,T066:alternative','動的計画法'").replace("','再帰','","','最後の項','")
p.write_text(s,encoding='utf-8-sig')
