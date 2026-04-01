"""Shared utilities for CTIE tools."""

import hashlib
import re
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

from config.settings import TIMEOUT, USER_AGENT, MAJOR_ASSETS, TOPIC_KEYWORDS

JST = timezone(timedelta(hours=9))


def strip_html(html: str) -> str:
    """Remove HTML tags and return plain text."""
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


def content_hash(text: str) -> str:
    """SHA-256 first 16 hex chars of text."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def parse_datetime(dt_str: str) -> str:
    """Best-effort parse to ISO format with JST."""
    if not dt_str:
        return ""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(dt_str)
        return dt.astimezone(JST).isoformat()
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(dt_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(JST).isoformat()
        except ValueError:
            continue
    return dt_str


def detect_assets(text: str) -> list[str]:
    """Detect mentioned crypto assets in text."""
    if not text:
        return []
    upper = text.upper()
    found = []
    for asset in MAJOR_ASSETS:
        if re.search(r'\b' + asset + r'\b', upper):
            found.append(asset)
    # Also detect full names
    name_map = {
        "ビットコイン": "BTC", "BITCOIN": "BTC",
        "イーサリアム": "ETH", "ETHEREUM": "ETH",
        "ソラナ": "SOL", "SOLANA": "SOL",
        "リップル": "XRP", "RIPPLE": "XRP",
    }
    lower = text.lower()
    for name, sym in name_map.items():
        if name.lower() in lower and sym not in found:
            found.append(sym)
    return found


def detect_topics(text: str) -> list[str]:
    """Detect topic categories from text."""
    if not text:
        return []
    lower = text.lower()
    found = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in lower:
                found.append(topic)
                break
    return found


def safe_request(url: str, params: dict | None = None, headers: dict | None = None) -> requests.Response | None:
    """GET with timeout and error handling. Returns None on failure."""
    hdr = {"User-Agent": USER_AGENT}
    if headers:
        hdr.update(headers)
    try:
        resp = requests.get(url, params=params, headers=hdr, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp
    except Exception:
        return None


def now_jst() -> datetime:
    return datetime.now(JST)


def now_jst_iso() -> str:
    return now_jst().isoformat()
