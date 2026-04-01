# Crypto Times Intelligence Engine (CTIE) v1 PRD

## 1. 概要
Crypto Times の自社記事を核に、必要最小限の市場データと一次ソースを統合し、
日本語で「今日の重要論点」「マーケット概況」「出典確認」を提供する
社内向けインテリジェンス基盤を構築する。

v1では、ニュース件数の圧縮ではなく、
少数精鋭の論点を素早く把握し、出典まで遡れることを価値の中心に置く。

---

## 2. 背景
Crypto Times は高頻度フラッシュ型ではない。
そのため、「大量速報をAIで絞る」設計をそのまま移植しても、価値が出にくい。

一方で現場には以下の課題がある。

- 情報源が散在している
- 何が重要か毎回人間が判断している
- AI要約だけでは不安で、結局出典を探し直している
- 同じ論点を毎回別の形に作り直している

---

## 3. v1の目的

### Primary Goal
編集部および投資/リサーチ担当が、
「その日押さえるべき重要論点」を日本語で短時間に把握できる状態を作る。

### Secondary Goal
- 重要論点に対して、すぐ出典確認できる状態を作る
- 市況のざっくり整理を、価格だけでなく背景込みで確認できる状態を作る
- 後続の Event Radar / Distribution Draft の基礎データ基盤を作る

---

## 4. 対象ユーザー

### Primary Users
1. 編集部 — 朝の論点整理、記事化候補の抽出、出典確認
2. 投資/リサーチ/CVCチーム — 市況の初動把握、テーマの重要論点確認、仮説作りの起点

### Secondary Users
- 経営・BD・マーケは v1では主対象外（参照利用は可）

---

## 5. v1スコープ

### In Scope（3機能のみ）

#### 5.1 Morning Brief
直近24時間の重要論点を3〜7件返す。
各論点: 何が起きたか / なぜ重要か / 関連テーマ・アセット / 不確実な点 / 出典

#### 5.2 Market Overview
BTC/ETH/SOL概況 / 時価総額 / ドミナンス / 24時間の主要材料 / 一言レジーム判定

#### 5.3 Source Vault
source名 / URL / 公開時刻 / source種別 / タイトル / 生成物との紐付け

### Out of Scope
Event Radar / Distribution Draft / Portfolio watchlist / オンチェーン監視 / Polymarket / 自動投稿 / 多言語 / Slack双方向

---

## 6. Jobs To Be Done
- JTBD-1: 朝5分で、今日の重要論点を把握したい
- JTBD-2: 相場がどう動いているかを、価格だけでなく背景込みで知りたい
- JTBD-3: AIの要約ではなく、元ソースにすぐ当たりたい

---

## 7. 成功の定義

### 定量KPI
- 朝刊閲覧率 / Source Vault利用率 / Morning Brief修正率 / 重要論点miss件数 / citation付与率 100%

### 定性KPI
- 朝の論点整理が速くなったか / 出典再検索が減ったか / 薄い日に正直に返せているか

---

## 8. データソース方針
- Layer 1 Owned: Crypto Times CMS/RSS
- Layer 2 Official: プロジェクト公式、規制当局、ETF公式
- Layer 3 Market: CoinGecko等
- Layer 4 Signal: X/Prediction market/Onchain（v1では補助、P1判定の主根拠にしない）

---

## 9. 重要度判定ポリシー
LLMに丸投げしない。ルールベース + スコアリングが先。LLMは日本語整形・要約・構造化を担当。

評価軸: Source Reliability / Market Impact / Novelty / Japan Relevance / Time Sensitivity / Cross-source Confirmation
ペナルティ: Duplication / Hype / Weak Evidence

---

## 10. 機能要件
- FR-1: Owned/Official/Market sourceを定期取得
- FR-2: タイトル、URL、公開時刻、本文、source種別を正規化
- FR-3: 同一URL、ハッシュ類似、近似タイトルを重複排除
- FR-4: Morning Brief生成（sourceが紐づくこと）
- FR-5: Market Overview生成（数値は構造化ソースから）
- FR-6: Source Vault取得
- FR-7: 監査ログ（prompt version / source / run追跡）

---

## 11. 非機能要件
- NFR-1: 朝刊バッチ成功率 99%
- NFR-2: すべての生成物にsource紐付け
- NFR-3: Chat応答 5〜15秒、朝刊完成 07:05 JST
- NFR-4: 取得失敗/citation欠落/空出力/source不足をログ可視化
- NFR-5: quiet day対応（水増ししない）

---

## 12. v1アーキテクチャ原則
- Skillは薄いルーターに留める
- コアロジックはAPI/service layerに置く
- LLMは整形担当、判定担当ではない
- 出典がない主張は出さない
- 事実/解釈/不確実性を分ける

---

## 13. 開発フェーズ（v1）
- Week 1: source定義 / DB schema / ingestion最小版
- Week 2: Morning Brief MVP / scoring初期版 / citation紐付け
- Week 3: Market Overview / Source Vault / skill wrapper
- Week 4: QA / quiet dayルール調整 / ログ・障害対応

---

## 14. リスクと対策
- source不足 → quiet day許容 + official/marketで補完
- LLMのもっともらしい誤り → 数値は構造化ソース優先 + citation必須
- スコープ肥大化 → v1は3機能のみ

---

## 15. リリース判定
- Morning Briefが安定して返る
- Market Overviewが最低限の数値と背景を返る
- Source Vaultで元URLに遡れる
- citation付与率 100%
- quiet dayが破綻していない
