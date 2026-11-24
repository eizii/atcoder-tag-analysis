# AtCompassへのSVD分類の反映

- 反映先：C:/Users/ejham/theme2026-kaziru
- 条件：2000未満、SVD32次元、コサイン距離、平均連結法、cut=0.2、制約なし
- 表示：86クラスタ＋文字列処理1タグ＝87タグ。1問のタグ5件も表示
- 問題：対象2,473問、タグ付与済み1,693問を表示、未付与780問
- CSV：3,391組の問題–クラスタ対応。群内で同じ問題を重複計上しない
- 分類の意味的妥当性、学習単位の粒度がそろったことを保証するものではない

## 変更と保存

manifest.jsonは変更前後のハッシュ、before/は変更前のファイル、staged/は反映したファイルです。既存の未コミット変更を含む状態を保存しました。

tag_to_cluster.csvは全139タグの対応表、unassigned_problems.csvは未付与780問です。

## 検証

- data_verification.json：保存済みSVDの分割との一致、元問題のメタデータ、群ごとの問題集合、バックアップハッシュを照合済み
- app_verification.json：Reactで87ノード、1問のタグ、選択カード、AC/WA表示、3設定の有限な配置座標、同レート帯集計の版判定、開発サーバーのCSV配信を検証済み
- npm run build：成功
- npm run lint：エラー0、変更前からの未使用変数showProgressLegendの警告1件
- npm run format:check：Prettierが環境に未導入のため実行不可
- 実ブラウザーでの操作確認：native pipeとbrowser access hostが利用できないため未確認

開発サーバー：http://127.0.0.1:5173/
公開・コミット・pushは行っていません。
