# 72クラスタ版への差し替え

ローカルの作業ブランチ: feature/cluster-tags-72
基にしたコミット: 002538bdfc4b99e93bc8e2f69b29f804c8d9608d
作業場所: ac_analyze_test/
GitHubへのpush・mainへの反映は行っていません。

## 確認するもの

- [更新した可視化](ac_analyze_test/clustering/report.html)
- [従来のCSVと同形式の差し替えデータ](ac_analyze_test/output/all_problems.csv)
- [72クラスタの対応表と説明](ac_analyze_test/clustering/README.md)

898問の細かい115タグを72群へ対応付け、重複するクラスタを除いて1,472組になりました。
既存のCSV出力に含まれなかったabc175_bの全探索タグも、完全一致から対応付けました。
従ってリポジトリのCSVは899問・1,473行です。898問だけのCSVもclustering/にあります。
以前からタグが空だった696問は未分類のままです。

元の細かいタグと差し替え前のタグは問題JSONに保持しています。
prompts/tags.jsonを72クラスタ版に変更し、今後の分類時は115種類の細かいタグから選んで同じ72群へ変換します。
APIを呼び出す再タグ付けは実行していません。

## 検証

- 問題JSONとCSVの一致・72タグのみを使用することを含む4件のテストに合格。
- HTMLの分割結果を276通りの対象・閾値でSciPyと照合。
- 初期表示72群、検索、対象切り替え、閾値変更、CSV保存の処理をNodeのDOMモックで確認。
- デンドログラムPNGの日本語ラベルと閾値線を目視確認。
- 1,601ファイルについて、再取り込みの前後で内容のハッシュが変わらないことを確認。
- ブラウザー実画面での操作は未確認。全問の意味的なタグ付けの正しさを保証する検証ではありません。

## 差分ファイル

[cluster-tags-72.patch](cluster-tags-72.patch) に新規ファイルを含む全変更を保存しています。適用先は上記コミットを基にしたリポジトリです。

~~~powershell
git switch -c feature/cluster-tags-72
git apply --check ../cluster-tags-72.patch
git apply ../cluster-tags-72.patch
~~~
