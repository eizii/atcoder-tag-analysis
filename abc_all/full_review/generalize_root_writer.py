from pathlib import Path
p=Path('abc_all/full_review/record_root_decisions.py');s=p.read_text(encoding='utf-8-sig').replace('import csv,json,re','import csv,json,re,sys').replace("DATA=Path(__file__).with_name('root_decisions.txt')","DATA=Path(__file__).with_name(sys.argv[1] if len(sys.argv)>1 else 'root_decisions.txt')").replace("Path(__file__).with_name('shard_3.tsv').open", "Path(__file__).with_name(sys.argv[2] if len(sys.argv)>2 else 'shard_3.tsv').open")
p.write_text(s,encoding='utf-8-sig')
