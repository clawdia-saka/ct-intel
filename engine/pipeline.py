"""メインパイプライン: ingest → dedup → score → store → output"""
from __future__ import annotations
import hashlib, os, sqlite3, json, uuid
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml

from .sources import fetch_all
from .sanitizer import sanitize_all
from .scorer import score_all, is_quiet_day
from .formatter import format_brief, format_market, format_sources, format_events, format_full

JST = timezone(timedelta(hours=9))
SKILL_DIR = Path(__file__).resolve().parent.parent
DB_PATH = SKILL_DIR / "data" / "store.db"
CONFIG_PATH = SKILL_DIR / "config.yaml"
DEDUP_THRESHOLD = 0.80


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def _init_db(conn: sqlite3.Connection):
    conn.execute("""CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY, source_name TEXT, source_type TEXT, url TEXT UNIQUE,
        title TEXT, published_at TEXT, fetched_at TEXT, raw_text TEXT,
        content_hash TEXT, importance_score REAL, priority TEXT,
        asset_tags TEXT, topic_tags TEXT, language TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY, artifact_type TEXT, content TEXT,
        generated_at TEXT, source_ids TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS market_snapshots (
        id TEXT PRIMARY KEY, data TEXT, captured_at TEXT
    )""")
    conn.commit()


def _get_existing_hashes(conn: sqlite3.Connection) -> set[str]:
    try:
        rows = conn.execute("SELECT content_hash FROM documents WHERE fetched_at > datetime('now', '-24 hours')").fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()


def _dedup(docs: list[dict]) -> list[dict]:
    """URL重複 + タイトル類似度で重複排除"""
    seen_urls: set[str] = set()
    seen_titles: list[str] = []
    result = []
    for doc in docs:
        url = doc.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        title = doc.get("title", "")
        is_dup = False
        for st in seen_titles:
            if SequenceMatcher(None, title.lower(), st.lower()).ratio() > DEDUP_THRESHOLD:
                is_dup = True
                break
        if is_dup:
            continue
        seen_titles.append(title)
        result.append(doc)
    return result


def _store_docs(conn: sqlite3.Connection, docs: list[dict]):
    for doc in docs:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO documents (id, source_name, source_type, url, title, published_at, fetched_at, raw_text, content_hash, importance_score, priority, asset_tags, topic_tags, language) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (doc["id"], doc.get("source_name"), doc.get("source_type"), doc.get("url"),
                 doc.get("title"), doc.get("published_at"), doc.get("fetched_at"),
                 doc.get("raw_text"), doc.get("content_hash"),
                 doc.get("importance_score"), doc.get("priority"),
                 json.dumps(doc.get("asset_tags", [])), json.dumps(doc.get("topic_tags", [])),
                 doc.get("language"))
            )
        except sqlite3.IntegrityError:
            pass
    conn.commit()


def _store_market(conn: sqlite3.Connection, market: dict):
    conn.execute(
        "INSERT INTO market_snapshots (id, data, captured_at) VALUES (?,?,?)",
        (str(uuid.uuid4()), json.dumps(market), datetime.now(JST).isoformat())
    )
    conn.commit()


def _store_artifact(conn: sqlite3.Connection, atype: str, content: str, source_ids: list[str]):
    conn.execute(
        "INSERT INTO artifacts (id, artifact_type, content, generated_at, source_ids) VALUES (?,?,?,?,?)",
        (str(uuid.uuid4()), atype, content, datetime.now(JST).isoformat(), json.dumps(source_ids))
    )
    conn.commit()


def run_pipeline(command: str = "brief", refresh: bool = True) -> str:
    config = _load_config()
    conn = sqlite3.connect(str(DB_PATH))
    _init_db(conn)

    if refresh:
        docs, market = fetch_all(config)
        docs = _dedup(docs)
        docs = sanitize_all(docs)  # Layer 2: sanitize before scoring
        existing_hashes = _get_existing_hashes(conn)
        weights = config.get("scoring", {}).get("weights")
        docs = score_all(docs, existing_hashes, weights)
        _store_docs(conn, docs)
        if market.get("prices"):
            _store_market(conn, market)
    else:
        rows = conn.execute(
            "SELECT id, source_name, source_type, url, title, published_at, fetched_at, raw_text, content_hash, importance_score, priority, asset_tags, topic_tags, language FROM documents ORDER BY importance_score DESC LIMIT 50"
        ).fetchall()
        docs = []
        for r in rows:
            docs.append({
                "id": r[0], "source_name": r[1], "source_type": r[2], "url": r[3],
                "title": r[4], "published_at": r[5], "fetched_at": r[6], "raw_text": r[7],
                "content_hash": r[8], "importance_score": r[9], "priority": r[10],
                "asset_tags": json.loads(r[11] or "[]"), "topic_tags": json.loads(r[12] or "[]"),
                "language": r[13],
            })
        market_row = conn.execute("SELECT data FROM market_snapshots ORDER BY captured_at DESC LIMIT 1").fetchone()
        market = json.loads(market_row[0]) if market_row else {}

    if command == "brief":
        quiet = is_quiet_day(docs, config)
        output = format_brief(docs, quiet)
        _store_artifact(conn, "morning_brief", output, [d["id"] for d in docs[:7]])
    elif command == "market":
        top_docs = [d for d in docs if d.get("priority") in ("P1", "P2")][:3]
        output = format_market(market, top_docs)
        _store_artifact(conn, "market_overview", output, [d["id"] for d in top_docs])
    elif command == "sources":
        output = format_sources(docs[:20])
    elif command == "events":
        output = format_events(docs)
    elif command == "full":
        quiet = is_quiet_day(docs, config)
        output = format_full(docs, market, quiet)
        _store_artifact(conn, "full_report", output, [d["id"] for d in docs[:10]])
    elif command == "refresh":
        output = f"✅ データ更新完了: {len(docs)}件取得、スコアリング済み"
    else:
        output = f"不明なコマンド: {command}\n利用可能: brief, market, sources, refresh"

    conn.close()
    return output
