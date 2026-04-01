"""重要度スコアリング: ルールベース、LLM不使用"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any

JST = timezone(timedelta(hours=9))

SOURCE_BASE = {"owned": 95, "official": 85, "market": 80, "signal": 50}
HIGH_IMPACT = {"regulation", "etf", "security", "macro"}
HIGH_ASSETS = {"BTC", "ETH"}
MID_IMPACT = {"defi", "l2", "stablecoin", "rwa", "ai_crypto"}
MID_ASSETS = {"SOL", "BNB", "XRP"}
HYPE_WORDS = ["爆上げ", "moon", "100x", "絶対", "確実", "間違いない", "guaranteed", "to the moon"]


def source_reliability(doc: dict) -> float:
    score = SOURCE_BASE.get(doc.get("source_type", "signal"), 50)
    return min(max(score, 0), 100)


def market_impact(doc: dict) -> float:
    topics = set(doc.get("topic_tags", []))
    assets = set(doc.get("asset_tags", []))
    if topics & HIGH_IMPACT or assets & HIGH_ASSETS:
        score = 85
    elif topics & MID_IMPACT or assets & MID_ASSETS:
        score = 65
    else:
        score = 35
    if len(assets) >= 2:
        score += 10
    return min(max(score, 0), 100)


def novelty(doc: dict, existing_hashes: set[str]) -> float:
    h = doc.get("content_hash", "")
    if h in existing_hashes:
        return 20
    return 80


def japan_relevance(doc: dict) -> float:
    text = (doc.get("title", "") + " " + doc.get("raw_text", "")).lower()
    ja_keywords = ["日本", "japan", "金融庁", "fsa", "jfsa", "円", "yen", "jpy", "bitflyer",
                    "coincheck", "sbi", "楽天", "メルカリ", "bitbank", "gmo"]
    if any(k in text for k in ja_keywords):
        return 90
    if doc.get("language") == "ja":
        return 75
    major_global = {"regulation", "etf", "macro", "security"}
    if set(doc.get("topic_tags", [])) & major_global:
        return 65
    return 25


def time_sensitivity(doc: dict) -> float:
    pub = doc.get("published_at")
    if not pub:
        return 40
    try:
        if isinstance(pub, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
                try:
                    pub_dt = datetime.fromisoformat(pub)
                    break
                except ValueError:
                    continue
            else:
                return 40
        else:
            pub_dt = pub
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=JST)
        age_hours = (datetime.now(JST) - pub_dt).total_seconds() / 3600
        if age_hours <= 6:
            return 90
        if age_hours <= 24:
            return 70
        if age_hours <= 72:
            return 50
        return 25
    except Exception:
        return 40


def cross_source(doc: dict, all_docs: list[dict]) -> float:
    title_lower = doc.get("title", "").lower()[:50]
    if not title_lower:
        return 25
    matches = 0
    for d in all_docs:
        if d["id"] != doc["id"] and title_lower[:20] in d.get("title", "").lower():
            matches += 1
    if matches >= 2:
        return 90
    if matches == 1:
        return 70
    if doc.get("source_type") == "official":
        return 75
    if doc.get("source_type") == "owned":
        return 60
    return 25


def penalties(doc: dict) -> float:
    penalty = 0
    text = (doc.get("title", "") + " " + doc.get("raw_text", "")).lower()
    if any(w.lower() in text for w in HYPE_WORDS):
        penalty += 15
    if not doc.get("published_at"):
        penalty += 10
    return penalty


def compute_score(doc: dict, all_docs: list[dict], existing_hashes: set[str], weights: dict | None = None) -> float:
    w = weights or {
        "source_reliability": 0.25,
        "market_impact": 0.25,
        "novelty": 0.15,
        "japan_relevance": 0.15,
        "time_sensitivity": 0.10,
        "cross_source_confirmation": 0.10,
    }
    score = (
        w["source_reliability"] * source_reliability(doc) +
        w["market_impact"] * market_impact(doc) +
        w["novelty"] * novelty(doc, existing_hashes) +
        w["japan_relevance"] * japan_relevance(doc) +
        w["time_sensitivity"] * time_sensitivity(doc) +
        w["cross_source_confirmation"] * cross_source(doc, all_docs)
    ) - penalties(doc)
    return max(0.0, min(score, 100.0))


def classify(score: float) -> str:
    if score >= 80:
        return "P1"
    if score >= 60:
        return "P2"
    if score >= 40:
        return "P3"
    return "archive"


def is_quiet_day(docs: list[dict], config: dict | None = None) -> bool:
    cfg = (config or {}).get("scoring", {}).get("quiet_day", {})
    p1_min = cfg.get("p1_min", 1)
    p2_min = cfg.get("p2_min", 2)
    p1 = sum(1 for d in docs if d.get("priority") == "P1")
    p2 = sum(1 for d in docs if d.get("priority") == "P2")
    return p1 < p1_min and p2 < p2_min


def score_all(docs: list[dict], existing_hashes: set[str] | None = None, weights: dict | None = None) -> list[dict]:
    hashes = existing_hashes or set()
    for doc in docs:
        doc["importance_score"] = compute_score(doc, docs, hashes, weights)
        doc["priority"] = classify(doc["importance_score"])
    docs.sort(key=lambda d: d["importance_score"], reverse=True)
    return docs
