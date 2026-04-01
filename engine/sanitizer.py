"""Layer 2: データ処理層の防御 — 外部コンテンツのサニタイズ"""
from __future__ import annotations
import re
from typing import Any

# === Suspicious patterns (prompt injection markers) ===
SUSPICIOUS_PATTERNS = [
    re.compile(r'ignore\s+(all\s+)?previous\s+instructions', re.I),
    re.compile(r'reveal\s+(your|the)\s+(system|developer|hidden)\s+prompt', re.I),
    re.compile(r'print\s+(your\s+)?environment\s+variables', re.I),
    re.compile(r'open\s+(a\s+)?local\s+file', re.I),
    re.compile(r'run\s+(a\s+)?(shell\s+)?command', re.I),
    re.compile(r'execute\s+(this|the|a)\s+', re.I),
    re.compile(r'show\s+(me\s+)?(your\s+)?(env|environment)\s+(vars|variables)', re.I),
    re.compile(r'access\s+(local|system)\s+file', re.I),
    re.compile(r'developer\s+message\s*:', re.I),
    re.compile(r'system\s+prompt\s*:', re.I),
    re.compile(r'you\s+are\s+now\s+(a|an|in)', re.I),
    re.compile(r'forget\s+(all\s+)?your\s+(previous\s+)?instructions', re.I),
    re.compile(r'new\s+instructions?\s*:', re.I),
    re.compile(r'override\s+(previous|system|all)', re.I),
    re.compile(r'disregard\s+(all|previous|your)', re.I),
    re.compile(r'browse\s+to\s+', re.I),
    re.compile(r'fetch\s+(this|the)\s+url', re.I),
    re.compile(r'call\s+(this|the)\s+(api|tool|function)', re.I),
    re.compile(r'<\s*script\b', re.I),
    re.compile(r'javascript\s*:', re.I),
    re.compile(r'data\s*:\s*text/html', re.I),
]

# Invisible/zero-width characters that can hide injection
INVISIBLE_CHARS = re.compile(r'[\u200b\u200c\u200d\u200e\u200f\u2028\u2029\u202a-\u202e\ufeff\u00ad\u034f\u061c\u115f\u1160\u17b4\u17b5\u180e\u2060-\u2064\u206a-\u206f\uffa0\ufff9-\ufffb]')

# Base64 patterns (potential encoded payloads)
BASE64_BLOCK = re.compile(r'[A-Za-z0-9+/]{50,}={0,2}')

# Max content length (chars) per document
MAX_CONTENT_LEN = 2000


def detect_suspicious(text: str) -> list[str]:
    """Detect injection-like patterns in text. Returns list of matched pattern descriptions."""
    if not text:
        return []
    found = []
    for pat in SUSPICIOUS_PATTERNS:
        if pat.search(text):
            found.append(pat.pattern)
    return found


def strip_invisible(text: str) -> str:
    """Remove zero-width and invisible Unicode characters."""
    return INVISIBLE_CHARS.sub('', text)


def strip_dangerous_html(text: str) -> str:
    """Remove dangerous HTML elements even after BeautifulSoup parsing."""
    # Remove residual script/style/iframe/object tags
    text = re.sub(r'<\s*(script|style|iframe|object|embed|form|input|textarea|button|applet|base|link|meta)\b[^>]*>.*?</\s*\1\s*>', '', text, flags=re.I | re.DOTALL)
    text = re.sub(r'<\s*(script|style|iframe|object|embed|form|input|textarea|button|applet|base|link|meta)\b[^>]*/?\s*>', '', text, flags=re.I)
    # Remove event handlers
    text = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.I)
    # Remove javascript: URLs
    text = re.sub(r'javascript\s*:', '', text, flags=re.I)
    # Remove data: URIs
    text = re.sub(r'data\s*:\s*\w+/\w+[;,]', '', text, flags=re.I)
    return text


def strip_base64(text: str) -> str:
    """Remove large base64 blocks (potential encoded payloads)."""
    return BASE64_BLOCK.sub('[base64-removed]', text)


def sanitize_text(text: str) -> tuple[str, list[str]]:
    """
    Full sanitization pipeline for external content.
    Returns (sanitized_text, list_of_suspicious_phrases_found).
    """
    if not text:
        return "", []

    # Step 1: Strip invisible chars
    text = strip_invisible(text)

    # Step 2: Strip dangerous HTML remnants
    text = strip_dangerous_html(text)

    # Step 3: Strip base64 blocks
    text = strip_base64(text)

    # Step 4: Detect suspicious patterns BEFORE removing them
    suspicious = detect_suspicious(text)

    # Step 5: Truncate
    if len(text) > MAX_CONTENT_LEN:
        text = text[:MAX_CONTENT_LEN] + "…[truncated]"

    # Step 6: Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text, suspicious


def sanitize_doc(doc: dict) -> dict:
    """
    Sanitize a single document. Adds 'suspicious_phrases' field.
    Modifies doc in place and returns it.
    """
    all_suspicious = []

    # Sanitize title
    if doc.get("title"):
        doc["title"], sus = sanitize_text(doc["title"])
        all_suspicious.extend(sus)

    # Sanitize raw_text (main content)
    if doc.get("raw_text"):
        doc["raw_text"], sus = sanitize_text(doc["raw_text"])
        all_suspicious.extend(sus)

    # Store suspicious findings
    if all_suspicious:
        doc["suspicious_phrases"] = list(set(all_suspicious))
        doc["flagged"] = True
    else:
        doc["suspicious_phrases"] = []
        doc["flagged"] = False

    return doc


def sanitize_all(docs: list[dict]) -> list[dict]:
    """Sanitize all documents. Returns sanitized docs with flags."""
    flagged_count = 0
    for doc in docs:
        sanitize_doc(doc)
        if doc.get("flagged"):
            flagged_count += 1
            # Log only count of patterns, never raw content or full patterns
            print(f"⚠ FLAGGED: {doc.get('source_name', '?')}: "
                  f"{len(doc['suspicious_phrases'])} suspicious pattern(s) detected")
    if flagged_count:
        print(f"🛡 Sanitizer: {flagged_count}/{len(docs)} documents flagged")
    return docs
