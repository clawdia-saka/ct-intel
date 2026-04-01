"""ソース取得: RSS, WP REST API, CoinGecko"""
from __future__ import annotations
import hashlib, ipaddress, socket, time, uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from html import unescape
from urllib.parse import urlparse
import re

import feedparser, requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))
TIMEOUT = 12
MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5MB per response
MAX_RETRIES = 2

# === URL Allowlist + SSRF Protection ===
ALLOWED_HOSTS = {
    "crypto-times.jp",
    "www.coindesk.com",
    "www.theblock.co",
    "cointelegraph.com",
    "www.dlnews.com",
    "api.coingecko.com",
    "api.alternative.me",
}

BLOCKED_IP_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # AWS metadata etc.
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _validate_url(url: str) -> bool:
    """Validate URL against allowlist and block private IPs (SSRF protection)."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host or parsed.scheme not in ("http", "https"):
            print(f"⚠ BLOCKED: invalid scheme or host: {url[:80]}")
            return False
        # Check allowlist
        if host not in ALLOWED_HOSTS:
            print(f"⚠ BLOCKED: host not in allowlist: {host}")
            return False
        # DNS resolve and check for private IPs
        for info in socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM):
            addr = info[4][0]
            ip = ipaddress.ip_address(addr)
            for net in BLOCKED_IP_NETS:
                if ip in net:
                    print(f"⚠ SSRF BLOCKED: {host} resolved to private IP {addr}")
                    return False
        return True
    except Exception as e:
        print(f"⚠ BLOCKED: URL validation error for {url[:80]}: {e}")
        return False


def _safe_get(url: str, **kwargs) -> requests.Response | None:
    """requests.get with URL validation, size limit, and retry cap."""
    if not _validate_url(url):
        return None
    kwargs.setdefault("timeout", TIMEOUT)
    kwargs.setdefault("headers", {"User-Agent": "CT-Intel/1.0"})
    kwargs["stream"] = True
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, **kwargs)
            r.raise_for_status()
            # Enforce size limit
            content_len = r.headers.get("Content-Length")
            if content_len and int(content_len) > MAX_RESPONSE_BYTES:
                print(f"⚠ BLOCKED: response too large ({content_len} bytes): {url[:80]}")
                r.close()
                return None
            # Read with size cap
            chunks = []
            total = 0
            for chunk in r.iter_content(chunk_size=8192):
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    print(f"⚠ TRUNCATED: response exceeded {MAX_RESPONSE_BYTES} bytes: {url[:80]}")
                    break
                chunks.append(chunk)
            r._content = b"".join(chunks)
            r.close()
            return r
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            print(f"⚠ Request failed after {MAX_RETRIES} attempts: {url[:80]}: {e}")
            return None
    return None


def _strip_html(html: str) -> str:
    if not html:
        return ""
    return unescape(BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True))


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _parse_dt(dt_str: str | None) -> str | None:
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(dt_str.strip(), fmt).astimezone(JST).isoformat()
        except ValueError:
            continue
    return dt_str


def _detect_assets(text: str) -> list[str]:
    assets = []
    t = text.upper()
    for sym in ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "DOT", "MATIC", "LINK"]:
        if sym in t:
            assets.append(sym)
    for name, sym in [("ビットコイン", "BTC"), ("イーサリアム", "ETH"), ("Bitcoin", "BTC"), ("Ethereum", "ETH"), ("Solana", "SOL")]:
        if name.lower() in text.lower():
            if sym not in assets:
                assets.append(sym)
    return assets


def _detect_topics(text: str) -> list[str]:
    topics = []
    t = text.lower()
    mapping = {
        "regulation": ["規制", "sec ", "fsa", "金融庁", "regulation", "compliance"],
        "etf": ["etf"],
        "defi": ["defi", "dex", "tvl", "流動性"],
        "l2": ["layer2", "l2", "rollup", "zk-", "optimism", "arbitrum", "base"],
        "nft": ["nft"],
        "stablecoin": ["stablecoin", "usdt", "usdc", "ステーブルコイン"],
        "security": ["ハック", "hack", "exploit", "脆弱性", "vulnerability"],
        "macro": ["fomc", "cpi", "fed", "利下げ", "利上げ", "雇用統計", "gdp"],
        "rwa": ["rwa", "real world", "tokeniz"],
        "ai_crypto": ["ai", "人工知能"],
        "gaming": ["gamefi", "gaming", "ゲーム"],
    }
    for topic, keywords in mapping.items():
        if any(k in t for k in keywords):
            topics.append(topic)
    return topics


def fetch_rss(url: str, source_name: str, source_type: str = "official") -> list[dict]:
    """RSSフィードを取得して正規化"""
    docs = []
    if not _validate_url(url):
        return docs
    try:
        # Fetch with size limit via _safe_get, then parse
        r = _safe_get(url)
        if r is None:
            return docs
        feed = feedparser.parse(r.content)
        for entry in feed.entries[:30]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            raw = _strip_html(entry.get("summary", "") or entry.get("description", ""))
            published = entry.get("published", entry.get("updated", ""))
            combined = f"{title} {raw}"
            docs.append({
                "id": str(uuid.uuid4()),
                "source_name": source_name,
                "source_type": source_type,
                "url": link,
                "title": title,
                "published_at": _parse_dt(published),
                "fetched_at": datetime.now(JST).isoformat(),
                "raw_text": raw[:2000],
                "language": "ja" if source_name == "Crypto Times" else "en",
                "content_hash": _hash(link or title),
                "asset_tags": _detect_assets(combined),
                "topic_tags": _detect_topics(combined),
            })
    except Exception as e:
        print(f"⚠ RSS取得失敗 ({source_name}): {e}")
    return docs


def fetch_wp_rest(url: str, source_name: str = "Crypto Times") -> list[dict]:
    """WordPress REST API fallback"""
    docs = []
    try:
        r = _safe_get(url)
        if r is None:
            return docs
        for post in r.json()[:20]:
            title = _strip_html(post.get("title", {}).get("rendered", ""))
            raw = _strip_html(post.get("excerpt", {}).get("rendered", ""))
            link = post.get("link", "")
            combined = f"{title} {raw}"
            docs.append({
                "id": str(uuid.uuid4()),
                "source_name": source_name,
                "source_type": "owned",
                "url": link,
                "title": title,
                "published_at": _parse_dt(post.get("date", "")),
                "fetched_at": datetime.now(JST).isoformat(),
                "raw_text": raw[:2000],
                "language": "ja",
                "content_hash": _hash(link or title),
                "asset_tags": _detect_assets(combined),
                "topic_tags": _detect_topics(combined),
            })
    except Exception as e:
        print(f"⚠ WP REST取得失敗 ({source_name}): {e}")
    return docs


def fetch_coingecko() -> dict:
    """CoinGecko価格+グローバルデータ"""
    data = {"prices": {}, "global": {}}
    try:
        r = _safe_get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,solana,ripple,dogecoin,cardano,avalanche-2,chainlink",
                    "vs_currencies": "usd,jpy", "include_24hr_change": "true", "include_market_cap": "true"},
        )
        if r:
            data["prices"] = r.json()
    except Exception as e:
        print(f"⚠ CoinGecko価格取得失敗: {e}")
    time.sleep(1.5)  # rate limit
    try:
        r = _safe_get("https://api.coingecko.com/api/v3/global")
        if r:
            data["global"] = r.json().get("data", {})
    except Exception as e:
        print(f"⚠ CoinGeckoグローバル取得失敗: {e}")
    # Fear & Greed Index
    time.sleep(1.5)
    try:
        r = _safe_get("https://api.alternative.me/fng/?limit=1")
        if r:
            fng = r.json().get("data", [{}])[0]
            data["fear_greed"] = {
                "value": int(fng.get("value", 0)),
                "label": fng.get("value_classification", "N/A"),
            }
    except Exception as e:
        print(f"⚠ Fear&Greed取得失敗: {e}")

    return data


def fetch_all(config: dict) -> tuple[list[dict], dict]:
    """全ソースから取得"""
    docs = []

    # Layer 1: Owned
    for src in config.get("sources", {}).get("owned", []):
        result = fetch_rss(src["url"], src["name"], "owned")
        if not result and src.get("fallback_url"):
            result = fetch_wp_rest(src["fallback_url"], src["name"])
        docs.extend(result)

    # Layer 2: Official
    for src in config.get("sources", {}).get("official", []):
        docs.extend(fetch_rss(src["url"], src["name"], "official"))

    # Layer 3: Market
    market = fetch_coingecko()

    return docs, market
