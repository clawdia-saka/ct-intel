# 📰 CTIE — Crypto Times Intelligence Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![API Key不要](https://img.shields.io/badge/API%20Key-不要-brightgreen.svg)](#)
[![7モジュール](https://img.shields.io/badge/モジュール-7-orange.svg)](#モジュール一覧)

暗号資産市場の重要論点を自動抽出・スコアリングし、7つのモジュールで提供するインテリジェンスエンジン。

[Crypto Times](https://crypto-times.jp/)の記事を核に、海外主要メディア・CoinGecko市場データ・Polymarket予測市場を統合。6軸ルールベーススコアリングで重要度を自動判定します。

対応プラットフォーム: OpenClaw / Claude Code / Antigravity / CLI

---

## インストール

```bash
git clone https://github.com/clawdia-saka/ct-intel.git
cd ct-intel
pip install -r requirements.txt
```

| プラットフォーム | 推奨インストール先 |
|----------------|------------------|
| OpenClaw | `~/.openclaw/workspace/skills/ct-intel/` |
| Claude Code | `~/.claude/skills/ct-intel/` |
| Antigravity / CLI | 任意のディレクトリ |

依存パッケージ: `requests`, `beautifulsoup4`, `feedparser`（軽量）

---

## 使い方

```bash
python3 run.py <ツール名> [JSONパラメータ]
```

---

## モジュール一覧

| # | ツール名 | 機能 |
|---|---------|------|
| M1 | `get_morning_brief` | 今日の重要論点（CT+海外ニュースをスコアリング、P1/P2/P3で分類） |
| M2 | `get_crypto_market` | 暗号資産市況（BTC/ETH/SOL/XRP、USD/JPY価格、時価総額、主要材料） |
| M3 | `get_source_vault` | 出典確認（全ソースのURL・公開時刻・種別一覧） |
| M4 | `get_event_radar` | 今後のイベント（マクロ / トークンアンロック / プロトコル / 上場 / ガバナンス） |
| M5 | `scan_polymarket` | Polymarket予測市場（高確定性・大額ベットのスキャン） |
| M6 | `get_raw_data` | 原データ（CT+海外の記事全文を加工なしで取得） |
| M7 | `get_macro` | マクロ/コモディティ（GOLD / 原油 / 為替 / 米国指標 / Fear & Greed） |

---

## 実行例

```bash
# 今日の重要論点
python3 run.py get_morning_brief

# 暗号資産市況（アセット指定可）
python3 run.py get_crypto_market '{"assets": "BTC,ETH,SOL,XRP"}'

# 出典一覧（件数指定可）
python3 run.py get_source_vault '{"limit": 30}'

# 今後のイベント
python3 run.py get_event_radar

# Polymarket（閾値指定可）
python3 run.py scan_polymarket '{"min_size": 10000, "min_price": 0.95}'

# 原データ
python3 run.py get_raw_data '{"article_limit": 10}'

# マクロ/コモディティ
python3 run.py get_macro
```

---

## スコアリング

6軸の評価スコアを加重平均し、ペナルティを差し引いてP1〜archiveに分類します。

| 評価軸 | 比重 | 内容 |
|-------|------|------|
| ソース信頼度 | 25% | Crypto Times(85) > 公式メディア(75) > 市場データ(70) > シグナル(50) |
| 市場影響度 | 25% | BTC/ETH/ETF/規制関連は高スコア |
| 新規性 | 15% | コンテンツハッシュで重複検出 |
| 日本関連性 | 15% | 日本の規制・取引所・円建て情報を検出 |
| 時間感度 | 10% | 6時間以内=90、12時間以内=75、24時間以内=60 |
| クロスソース確認 | 10% | 複数メディアで報道されている場合にブースト |

**ペナルティ:** 煽り表現 / エビデンス不足 / 重複記事

**分類:** P1（80点以上）→ P2（60点以上）→ P3（40点以上）→ archive

**Quiet Day:** P1=0件 かつ P2が2件未満の場合、「大きな材料は限定的」と正直に返します。

---

## データソース

| レイヤー | ソース | 用途 |
|---------|--------|------|
| 自社 | [Crypto Times](https://crypto-times.jp/)（RSS / WP REST API） | 日本語暗号資産ニュース |
| 海外メディア | CoinDesk / The Block / CoinTelegraph / DL News | 英語圏ニュース |
| 市場データ | [CoinGecko](https://www.coingecko.com/) | 価格・時価総額 |
| 市場データ（フォールバック） | [CoinMarketCap](https://coinmarketcap.com/)（`CMC_API_KEY`設定時） | CoinGecko障害時の代替 |
| 予測市場 | [Polymarket](https://polymarket.com/)（Gamma API） | 大額ベットのスキャン |
| マクロ | PAXG（金プロキシ）/ 為替API / Fear & Greed Index | コモディティ・マクロ指標 |

---

## オプション設定

コア機能はAPI Key不要で動作します。以下は任意の追加設定です。

| 環境変数 | 用途 |
|---------|------|
| `CMC_API_KEY` | CoinMarketCapフォールバック（[無料登録](https://coinmarketcap.com/api/)で取得可） |

---

## フォールバック

| 優先 | 条件 | 動作 |
|------|------|------|
| 1 | CoinGecko正常 | 最新データを返す |
| 2 | CoinGecko障害 + CMC設定あり | CoinMarketCapから取得（ソース明示） |
| 3 | 両方障害 + キャッシュあり | 直近のキャッシュデータを返す（stale表示） |
| 4 | 全滅 | エラーメッセージを表示 |

---

## 免責事項

本ツールの出力は情報提供のみを目的としており、投資助言ではありません。暗号資産市場はリスクが高く、投資判断はご自身の責任で行ってください。

---

## ライセンス

[MIT](LICENSE)

---

[Crypto Times](https://crypto-times.jp/) 🇯🇵
