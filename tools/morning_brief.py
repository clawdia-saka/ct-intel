"""M1: Morning Brief — top scored news with priority classification."""

from engine.sources import fetch_all_news
from engine.dedup import dedup_documents
from engine.scorer import score_all, is_quiet_day
from tools.common import now_jst_iso

PRIORITY_EMOJI = {"P1": "🔴", "P2": "🟡", "P3": "🔵"}


def get_morning_brief(limit: int = 7) -> str:
    docs = fetch_all_news()
    docs = dedup_documents(docs)
    docs = score_all(docs)

    # Filter to P1/P2, cap at limit
    top = [d for d in docs if d["priority"] in ("P1", "P2")][:limit]

    quiet = is_quiet_day(docs)

    lines = []
    lines.append(f"[CTIE Morning Brief] {now_jst_iso()}")
    lines.append(f"Total sources scanned: {len(docs)}")
    lines.append(f"Top items: {len(top)}")

    if quiet:
        lines.append("")
        lines.append("⚠ QUIET DAY: 今日は新規の大型材料は限定的です。")

    lines.append("")

    for i, d in enumerate(top, 1):
        emoji = PRIORITY_EMOJI.get(d["priority"], "⚪")
        lines.append(f"--- [{i}] {emoji} {d['priority']} (score: {d['score']}) ---")
        lines.append(f"Title: {d['title']}")
        if d.get("raw_text"):
            summary = d["raw_text"][:200]
            if len(d["raw_text"]) > 200:
                summary += "..."
            lines.append(f"Summary: {summary}")
        if d.get("asset_tags"):
            lines.append(f"Assets: {', '.join(d['asset_tags'])}")
        if d.get("topic_tags"):
            lines.append(f"Topics: {', '.join(d['topic_tags'])}")
        lines.append(f"Source: {d['source_name']} ({d['source_type']})")
        lines.append(f"URL: {d.get('url', 'N/A')}")
        lines.append(f"Published: {d.get('published_at', 'N/A')}")
        lines.append("")

    if not top:
        lines.append("No P1/P2 items found.")

    # Append P3 count for context
    p3_count = sum(1 for d in docs if d["priority"] == "P3")
    archive_count = sum(1 for d in docs if d["priority"] == "archive")
    lines.append(f"[Additional: P3={p3_count}, archive={archive_count}]")

    return "\n".join(lines)
