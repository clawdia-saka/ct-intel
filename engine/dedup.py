"""Document deduplication — URL, content hash, title similarity."""

from difflib import SequenceMatcher

TITLE_SIM_THRESHOLD = 0.80


def dedup_documents(docs: list[dict]) -> list[dict]:
    """Remove duplicates. Keep first occurrence (highest-priority source first)."""
    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()
    kept_titles: list[str] = []
    result: list[dict] = []

    for doc in docs:
        url = doc.get("url", "")
        chash = doc.get("content_hash", "")
        title = doc.get("title", "")

        # URL exact match
        if url and url in seen_urls:
            continue

        # Content hash match
        if chash and chash in seen_hashes:
            continue

        # Title similarity
        is_dup = False
        for kept in kept_titles:
            if SequenceMatcher(None, title.lower(), kept.lower()).ratio() > TITLE_SIM_THRESHOLD:
                is_dup = True
                break
        if is_dup:
            continue

        if url:
            seen_urls.add(url)
        if chash:
            seen_hashes.add(chash)
        kept_titles.append(title)
        result.append(doc)

    return result
