"""M3: Source Vault — full source attribution list."""

from engine.sources import fetch_all_news
from tools.common import now_jst_iso


def get_source_vault(limit: int = 20) -> str:
    docs = fetch_all_news()
    docs = docs[:limit]

    lines = []
    lines.append(f"[CTIE Source Vault] {now_jst_iso()}")
    lines.append(f"Showing latest {len(docs)} sources")
    lines.append("")

    for i, d in enumerate(docs, 1):
        lines.append(f"[{i}] {d['source_name']} ({d['source_type']})")
        lines.append(f"    Title: {d['title']}")
        lines.append(f"    URL: {d.get('url', 'N/A')}")
        lines.append(f"    Published: {d.get('published_at', 'N/A')}")
        lines.append(f"    Language: {d.get('language', 'N/A')}")
        lines.append("")

    if not docs:
        lines.append("No sources available.")

    return "\n".join(lines)
