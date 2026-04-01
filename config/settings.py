"""CTIE Configuration — Sources, Scoring, Constants."""

import os

# ── Timeouts & Headers ─────────────────────────────────────────────
TIMEOUT = 12
USER_AGENT = "CTIE/1.0"

# ── Crypto Times (Layer 1: Owned) ──────────────────────────────────
CT_RSS = "https://crypto-times.jp/feed/"
CT_WP_API = "https://crypto-times.jp/wp-json/wp/v2/posts?per_page=20"

# ── Official Sources (Layer 2) ─────────────────────────────────────
RSS_SOURCES = [
    {"name": "Crypto Times", "url": CT_RSS, "type": "owned", "lang": "ja"},
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "type": "official", "lang": "en"},
    {"name": "The Block", "url": "https://www.theblock.co/rss.xml", "type": "official", "lang": "en"},
    {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss", "type": "official", "lang": "en"},
    {"name": "DL News", "url": "https://www.dlnews.com/arc/outboundfeeds/rss/", "type": "official", "lang": "en"},
]

# ── Market Sources (Layer 3) ───────────────────────────────────────
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# ── CoinMarketCap (optional fallback, requires free API key) ────────
CMC_API_BASE = "https://pro-api.coinmarketcap.com"
CMC_API_KEY = os.environ.get("CMC_API_KEY", "")  # User sets this

# ── Polymarket ─────────────────────────────────────────────────────
POLYMARKET_API = "https://gamma-api.polymarket.com"

# ── Scoring Weights ────────────────────────────────────────────────
SOURCE_WEIGHTS = {
    "source_reliability": 0.25,
    "market_impact": 0.25,
    "novelty": 0.15,
    "japan_relevance": 0.15,
    "time_sensitivity": 0.10,
    "cross_source": 0.10,
}

SOURCE_BASE_SCORES = {
    "owned": 85,      # CT記事は優先表示
    "official": 75,
    "market": 70,
    "signal": 50,
}

# ── Priority Thresholds ────────────────────────────────────────────
P1_THRESHOLD = 80
P2_THRESHOLD = 60
P3_THRESHOLD = 40

# ── Hype Detection ─────────────────────────────────────────────────
HYPE_WORDS = [
    "爆上げ", "moon", "100x", "確実", "絶対", "間違いない",
    "guaranteed", "to the moon",
]

# ── Asset Detection ─────────────────────────────────────────────────
MAJOR_ASSETS = {
    "BTC": ["btc", "bitcoin", "ビットコイン", "比特币"],
    "ETH": ["eth", "ethereum", "イーサリアム", "以太坊"],
    "SOL": ["sol", "solana", "ソラナ"],
    "BNB": ["bnb", "binance"],
    "XRP": ["xrp", "ripple", "リップル"],
    "DOGE": ["doge", "dogecoin"],
    "ADA": ["ada", "cardano"],
    "AVAX": ["avax", "avalanche"],
    "DOT": ["dot", "polkadot"],
    "MATIC": ["matic", "polygon"],
    "LINK": ["link", "chainlink"],
}

# ── Topic Detection ─────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    "regulation": ["規制", "sec ", "fsa", "金融庁", "regulation", "compliance", "监管"],
    "etf": ["etf"],
    "defi": ["defi", "dex", "tvl", "流動性"],
    "l2": ["layer2", "l2", "rollup", "zk-", "optimism", "arbitrum", "base"],
    "nft": ["nft"],
    "stablecoin": ["stablecoin", "usdt", "usdc", "ステーブルコイン", "稳定币"],
    "security": ["ハック", "hack", "exploit", "脆弱性", "vulnerability"],
    "macro": ["fomc", "cpi", "fed", "利下げ", "利上げ", "雇用統計", "gdp"],
    "rwa": ["rwa", "real world", "tokeniz"],
    "ai_crypto": ["ai", "人工知能"],
    "gaming": ["gamefi", "gaming", "ゲーム"],
}

# ── Event Radar ─────────────────────────────────────────────────────
EVENT_KEYWORDS = [
    "cpi", "fomc", "unlock", "mainnet", "upgrade", "listing", "上場",
    "governance", "vote", "airdrop", "halving", "半減期",
    "launch", "testnet", "hardfork", "migration",
]

EVENT_TYPES = {
    "macro": ["cpi", "fomc", "fed", "gdp", "雇用統計", "employment", "pce", "ppi"],
    "unlock": ["unlock", "vesting", "token release"],
    "protocol": ["mainnet", "upgrade", "hardfork", "testnet", "migration", "launch"],
    "listing": ["listing", "上場", "delist"],
    "governance": ["governance", "vote", "proposal", "ガバナンス"],
}

TIME_HORIZON_PATTERNS = {
    "tonight": ["今夜", "tonight", "today", "本日", "今日"],
    "tomorrow": ["明日", "tomorrow"],
    "this_week": ["今週", "this week"],
    "this_month": ["今月", "this month"],
}
