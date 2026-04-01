# CTIE Architecture

## 推奨構成（OpenClaw非依存）

### Core Engine
- Python / FastAPI / Postgres / Redis (Queue) / Pydantic schema / Scheduler / Prompt versioning

### Ingestion
- RSS / API connector / scraper（最低限）/ webhook / CSV/manual upload

### Intelligence Layer
- entity resolution / dedupe / topic clustering / scoring / alert rules / source ranking

### Generation Layer
- morning brief / market summary / event preview / draft generator

### Delivery Layer
- Chat interface / Slack・Discord / Email / CMS draft export / Notion export / X draft output

---

## システム構成図

```
+----------------------+
| Crypto Times CMS/RSS |
+----------+-----------+
           |
+----------v-----------+
|   Owned Connectors   |
+-----------------------+

+---------------------+  +---------------------+  +---------------------+
| Official Connectors |  | Market Connectors   |  | Optional Signals    |
| (Regulator, PR etc) |  | (Price, ETF, OI)    |  | (X, Polymarket etc) |
+----------+----------+  +----------+----------+  +----------+----------+
            \                       |                       /
             \                      |                      /
              +---------------------v---------------------+
              |     Ingestion / Normalization              |
              +---------------------+---------------------+
                                    |
                        +-----------v-----------+
                        |  PostgreSQL / Store   |
                        |  docs, events, signals|
                        +-----------+-----------+
                                    |
                        +-----------v-----------+
                        | Intelligence Pipeline |
                        |  dedupe / entities /  |
                        |  scoring / clustering |
                        +-----------+-----------+
                                    |
                        +-----------v-----------+
                        | LLM Generation Layer  |
                        |  brief / market /     |
                        |  event / draft        |
                        +-----------+-----------+
                                    |
              +---------------------+---------------------+
              |                     |                     |
    +---------v---------+ +--------v----------+ +--------v---------+
    | Chat / Skill UI   | | Internal Dashboard| | Email / Slack /  |
    | OpenClaw wrapper  | | review / source   | | Notion / Export   |
    +-------------------+ +-------------------+ +------------------+
```

---

## ディレクトリ構成

```
crypto-times-intelligence/
├── README.md
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Makefile
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── prompt-policy.md
│   ├── scoring-policy.md
│   └── runbooks/
├── app/
│   ├── main.py              # FastAPI entry
│   ├── cli.py
│   ├── config/
│   ├── core/
│   ├── db/
│   │   ├── models/          # SQLAlchemy models
│   │   └── repositories/
│   ├── schemas/              # Pydantic
│   ├── connectors/
│   │   ├── owned/
│   │   ├── official/
│   │   ├── market/
│   │   └── signal/
│   ├── pipelines/
│   │   ├── ingest_orchestrator.py
│   │   ├── dedupe.py
│   │   ├── entity_linking.py
│   │   ├── importance_scorer.py
│   │   └── quality_checks.py
│   ├── services/
│   │   ├── morning_brief_service.py
│   │   ├── market_overview_service.py
│   │   ├── source_vault_service.py
│   │   └── feedback_service.py
│   ├── prompts/ja/
│   ├── llm/
│   ├── delivery/
│   ├── api/routes/
│   ├── schedulers/
│   └── tests/
├── scripts/
└── skill_wrapper/
    ├── SKILL.md
    ├── run.py
    └── tools/
```

---

## データモデル（v1テーブル）

| テーブル | 用途 |
|----------|------|
| sources | ソース定義（name, type, reliability_score） |
| documents | 記事・発表（url, title, raw_text, importance_score, priority） |
| assets | アセット/銘柄（symbol, sector） |
| market_snapshots | 定量時系列（price, change_24h, volume, market_cap） |
| signals | 検知された変化（signal_type, priority, score, evidence） |
| artifacts | 生成物（morning_brief, market_overview, source_vault） |
| feedback | 人間評価（rating, label, note） |

### v1.5以降で追加
- events（未来イベント）
- entities（企業・プロジェクト・人物）
- claims（主張抽出）
- watchlists（監視対象）

---

## 設計思想
- **Skillは玄関、本体は家。** 玄関だけ立派にしても意味がない
- **LLMは判定者ではなく編集者**
- **記事中心設計をやめる。論点が母集団**
- **将来、ChatGPT/Slack/ダッシュボード/メール配信すべてに流用可能**
