from pathlib import Path
p=Path('abc_all/full_review/append_shard_1_1190.py')
s=p.read_text(encoding='utf-8-sig')
for a,b in [('全域木','連結性を保ったまま森'),('2 進','進数表現'),("','スタック','","','stack','"),("','abc','","','文字として受け取る','"),("','移動','","','while','"),("','線形','","','ソート','"),("','範囲','","','オーバーフロー','"),("','deque','","','両端キュー','"),("T077:primary,T264:supporting','ソート'","T077:primary,T264:supporting','切れ込み'"),("','等差数列','","','逆元','"),("','XOR','","','ビット演算','")]:s=s.replace(a,b)
p.write_text(s,encoding='utf-8-sig')
