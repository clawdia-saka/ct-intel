"""M4: Event Radar — upcoming events extracted from news articles."""

import re

from engine.sources import fetch_all_news
from config.settings import EVENT_KEYWORDS, EVENT_TYPES, TIME_HORIZON_PATTERNS
from tools.common import now_jst_iso


def _classify_event(text: str) -> str:
    """Determine event type from text."""
    lower = text.lower()
    for etype, keywords in EVENT_TYPES.items():
        for kw in keywords:
            if kw.lower() in lower:
                return etype
    return "other"


def _detect_horizon(text: str) -> str:
    """Detect time horizon from text."""
    lower = text.lower()
    for horizon, patterns in TIME_HORIZON_PATTERNS.items():
        for p in patterns:
            if p.lower() in lower:
                return horizon
    return "不明"


def _confidence(source_type: str) -> str:
    """Assign confidence rank by source type."""
    if source_type in ("official",):
        return "A"
    elif source_type in ("market",):
        return "B"
    elif source_type in ("owned",):
        return "B"
    else:
        return "C"


def get_event_radar() -> str:
    docs = fetch_all_news()
    events = []

    for doc in docs:
        text = f"{doc.get('title', '')} {doc.get('raw_text', '')}"
        lower = text.lower()

        # Check for event keywords
        matched_kw = [kw for kw in EVENT_KEYWORDS if kw.lower() in lower]
        if not matched_kw:
            continue

        conf = _confidence(doc.get("source_type", "signal"))
        # Skip D-level (unverified)
        if conf == "D":
            continue

        etype = _classify_event(text)
        horizon = _detect_horizon(text)

        events.append({
            "title": doc["title"],
            "event_type": etype,
            "time_horizon": horizon,
            "confidence": conf,
            "keywords": matched_kw,
            "source_name": doc["source_name"],
            "source_type": doc["source_type"],
            "url": doc.get("url", ""),
            "published_at": doc.get("published_at", ""),
        })

    lines = []
    lines.append(f"[CTIE Event Radar] {now_jst_iso()}")
    lines.append(f"Events detected: {len(events)}")
    lines.append("")

    # Group by event type
    for etype in ("macro", "unlock", "protocol", "listing", "governance", "other"):
        group = [e for e in events if e["event_type"] == etype]
        if not group:
            continue
        lines.append(f"== {etype.upper()} ==")
        for e in group:
            lines.append(f"  [{e['confidence']}] {e['title']}")
            lines.append(f"      Horizon: {e['time_horizon']} | Keywords: {', '.join(e['keywords'])}")
            lines.append(f"      Source: {e['source_name']} | URL: {e.get('url', 'N/A')}")
            lines.append("")

    if not events:
        lines.append("No event-related articles detected.")

    return "\n".join(lines)
