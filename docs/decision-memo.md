# CTIE v1 意思決定メモ

## 決定
CTIE の v1 は、以下の3機能に限定して開発する。

1. Morning Brief
2. Market Overview
3. Source Vault

Event Radar / 投稿案生成 / watchlist / onchain監視 は v1では実装しない。

---

## 背景
当初案は機能としては魅力的だったが、MVPとしてはスコープが広すぎた。

Crypto Times は高頻度速報型ではないため、
価値の源泉は「大量ニュースの圧縮」ではなく
「重要論点の整理」と「出典まで遡れる透明性」にある。

---

## Blue Team評価（推進側）
- Crypto Timesの情報量に合った設計
- 自社記事だけに依存せず、official/market sourceで補完できる
- LLM依存を抑え、スコアリング先行で品質を担保しやすい
- Source Vaultにより、編集・投資のどちらでも使いやすい
- quiet dayを許容しており、長期的な信頼性が高い
- モジュール分離がきれいで、source追加が容易

---

## Red Team評価（懐疑側）
- MVPにしてはやりたいことが多かった
- audienceが多すぎると誰にも刺さらない
- スコアリングは設計より運用が難しい
- 出典紐付けは見た目より重い
- 日本語品質はプロンプトだけでは解決しない

---

## 最終判断
Red Teamの懸念は妥当。v1は「朝の論点整理」と「出典確認」に絞る。

**まずは"信用できる朝刊"を作る。賢い万能機は後でいい。**

---

## 修正版フェーズ
- v1: Morning Brief / Market Overview / Source Vault
- v1.5: Event Radar / Distribution Draft
- v2: watchlist / signal alert / X・prediction market・onchain補助 / portfolio lens

---

## 成功条件
- 自社記事を核にする
- 外部ソースで補完する
- 出典トレーサビリティを死守する
- MVPを削る
- "今日は薄い"を認める
- LLMに判定を丸投げしない

## 失敗条件
- なんでもできる万能化
- 配信機能から先に作る
- socialノイズを早く入れすぎる
- importance設計を放置する
- 編集レビューをゼロにする
