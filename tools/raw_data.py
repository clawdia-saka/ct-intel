"""M6: Raw Data — unprocessed articles for downstream use."""

from engine.sources import fetch_rss, fetch_wp_rest
from config.settings import CT_RSS, RSS_SOURCES
from tools.common import now_jst_iso


def get_raw_data(article_limit: int = 5, flash_limit: int = 5) -> str:
    lines = []
    lines.append(f"[CTIE Raw Data] {now_jst_iso()}")
    lines.append("")

    # CT articles (owned)
    lines.append("== CryptoTimes Articles ==")
    ct_docs = fetch_rss(CT_RSS, "CryptoTimes", "owned")
    if not ct_docs:
        ct_docs = fetch_wp_rest()
    ct_docs = ct_docs[:article_limit]

    for i, d in enumerate(ct_docs, 1):
        lines.append(f"--- CT [{i}] ---")
        lines.append(f"Title: {d['title']}")
        lines.append(f"URL: {d.get('url', 'N/A')}")
        lines.append(f"Published: {d.get('published_at', 'N/A')}")
        lines.append(f"Text: {d.get('raw_text', '')}")
        lines.append("")

    if not ct_docs:
        lines.append("(No CT articles available)")
        lines.append("")

    # International sources
    lines.append("== International Flash ==")
    intl_docs = []
    for src in RSS_SOURCES:
        if src["type"] == "owned":
            continue
        intl_docs.extend(fetch_rss(src["url"], src["name"], src["type"]))
    intl_docs = intl_docs[:flash_limit]

    for i, d in enumerate(intl_docs, 1):
        lines.append(f"--- INTL [{i}] ---")
        lines.append(f"Source: {d['source_name']}")
        lines.append(f"Title: {d['title']}")
        lines.append(f"URL: {d.get('url', 'N/A')}")
        lines.append(f"Published: {d.get('published_at', 'N/A')}")
        lines.append(f"Text: {d.get('raw_text', '')}")
        lines.append("")

    if not intl_docs:
        lines.append("(No international articles available)")

    return "\n".join(lines)
