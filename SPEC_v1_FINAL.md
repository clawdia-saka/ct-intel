# CTIE v1 確定仕様

## プロダクト
- **名前:** Crypto Times Intelligence Engine (CTIE)
- **配布:** GitHub（OpenClaw Skill）
- **ユーザー:** OpenClawユーザー全般（暗号資産に興味ある個人）
- **構成:** `skills/ct-intel/` で完結するPythonスキル

## 設計思想
- スクリプトはデータ取得+スコアリング+構造化（JSON返却）
- LLM整形はエージェント側（SKILL.mdで指示）
- スクリプト内からLLMは呼ばない
- CT記事を優先表示（マーケティング価値、CTへの流入導線）
- ルールベーススコアリング（差別化ポイント）
- quiet day: 薄い日は正直に「大きな材料は限定的」と返す
- 言語: ユーザーの言語に合わせる（SKILL.mdで指示）
- API key: 基本不要、一部高度機能はオプショナル

## 7モジュール

### M1: 今日の重要論点（Morning Brief）
- CT記事 + 海外メディアRSSから重要ニュースを取得
- ルールベーススコアリング（P1/P2/P3）
- CT記事は優先表示
- 各論点にsource URLを紐付け（citation 100%）
- quiet day対応

### M2: 暗号資産市況（Crypto Market）
- BTC / ETH / SOL 価格（USD/JPY）、24h変化率、時価総額
- グローバル: 総時価総額、BTC占有率
- 主要材料（M1のP1/P2から）

### M3: 出典確認（Source Vault）
- 元記事URL + ソース種別（owned/official/market）一覧
- source名、タイトル、公開時刻
- 生成物との紐付け

### M4: 今後のイベント（Event Radar）
- 簡易版: イベント種別ごとにソース分離
  - マクロ（CPI/FOMC等）: 公式ソース参照
  - Token Unlock: 専業ベンダー参照（Tokenomist/CryptoRank）
  - Protocol Event: 記事抽出 + 公式
- LLM補完禁止、抽出のみ
- Confidence rank: A(official) / B(vendor) / C(article) / D(unverified→出さない)

### M5: Polymarket予測市場（Prediction & Whales）
- Polymarket Data API直叩き
- 大額高確定性押注のスキャン
- 事件タイトルをユーザー言語に翻訳（エージェント側）

### M6: API/原データ（Raw Data）
- 最新記事 + ニュースの生データそのまま返す
- 二次開発・データ統合用

### M7: マクロ/コモディティ（Macro & Commodities）
- GOLD、原油（WTI/Brent）
- 為替（USD/JPY、DXY）
- 米国指標（S&P500、NASDAQ、米国債利回り）
- M2とは独立モジュール

## データソース
- **Layer 1 Owned:** crypto-times.jp RSS（+ WP REST API fallback）
- **Layer 2 Official:** CoinDesk RSS, The Block RSS, Cointelegraph RSS, DL News RSS
- **Layer 3 Market:** CoinGecko API（暗号資産）、別ソース（マクロ/コモディティ）
- **Polymarket:** Polymarket Data API
- **Event:** 公式ソース + 専業ベンダー + 記事抽出

## スコアリング（ルールベース、LLM不使用）
```
FINAL_SCORE =
  0.25 * source_reliability +
  0.25 * market_impact +
  0.15 * novelty +
  0.15 * japan_relevance +
  0.10 * time_sensitivity +
  0.10 * cross_source_confirmation
  - duplication_penalty - hype_penalty - weak_evidence_penalty
```
- P1: 80+ / P2: 60-79 / P3: 40-59 / archive: <40
- CT記事: source_reliabilityにboost（優先表示）
- quiet day: P1=0 かつ P2<2

## 技術要件
- Python 3.10+
- 依存: requests, beautifulsoup4, feedparser（軽量）
- DB: なし or SQLiteのみ（ローカルキャッシュ用）
- API key: 基本不要
- FastAPI不要

## ディレクトリ構成
```
ct-intel/
├── SKILL.md              # ルーティング + 出力指示
├── README.md             # GitHub用
├── run.py                # CLIエントリ（ツールルーター）
├── requirements.txt      # requests, beautifulsoup4, feedparser
├── config/
│   └── settings.py       # ソース定義、スコアリング重み
├── tools/
│   ├── __init__.py
│   ├── common.py         # 共通ユーティリティ
│   ├── morning_brief.py  # M1
│   ├── crypto_market.py  # M2
│   ├── source_vault.py   # M3
│   ├── event_radar.py    # M4
│   ├── polymarket.py     # M5
│   ├── raw_data.py       # M6
│   └── macro.py          # M7
├── engine/
│   ├── __init__.py
│   ├── sources.py        # RSS/API取得
│   ├── scorer.py         # ルールベーススコアリング
│   └── dedup.py          # 重複排除
├── data/                 # ローカルキャッシュ（gitignore）
│   └── .gitkeep
└── LICENSE               # MIT
```

## 配布
- GitHub公開リポジトリ
- インストール: git clone → pip install -r requirements.txt
- OpenClaw skill として利用
