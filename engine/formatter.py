"""出力整形: 日本語フォーマッター"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

PRIORITY_EMOJI = {"P1": "🔴", "P2": "🟡", "P3": "🟢"}


def _now_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")


def _fmt_price(v: float | None) -> str:
    if v is None:
        return "N/A"
    if v >= 1000:
        return f"${v:,.0f}"
    return f"${v:.2f}"


def _fmt_change(v: float | None) -> str:
    if v is None:
        return ""
    arrow = "▲" if v >= 0 else "▼"
    return f"{arrow}{v:+.2f}%"


def _fmt_mcap(v: float | None) -> str:
    if v is None:
        return "N/A"
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.1f}B"
    return f"${v/1e6:.0f}M"


def format_brief(docs: list[dict], quiet: bool = False) -> str:
    today = datetime.now(JST).strftime("%Y-%m-%d")
    lines = [f"📌 今日の重要論点 | {today}", "━" * 30, ""]

    if quiet:
        lines.append("今日は大きな新規材料は限定的です。以下の論点のみ押さえておけば十分です。")
        lines.append("")

    shown = [d for d in docs if d.get("priority") in ("P1", "P2")][:7]
    if not shown:
        shown = docs[:3]

    for i, doc in enumerate(shown, 1):
        emoji = PRIORITY_EMOJI.get(doc.get("priority", "P3"), "🟢")
        lines.append(f"{emoji} {doc['title']}")
        if doc.get("raw_text"):
            lines.append(f"  事実: {doc['raw_text'][:120]}")
        topics = doc.get("topic_tags", [])
        assets = doc.get("asset_tags", [])
        tags = assets + topics
        if tags:
            lines.append(f"  関連: {' / '.join(tags[:5])}")
        lines.append(f"  📎 {doc.get('url', 'N/A')}")
        lines.append("")

    lines.append("---")
    lines.append("💡 市況まとめも出せます → `ctie.py market`")
    lines.append("💡 出典一覧も出せます → `ctie.py sources`")
    return "\n".join(lines)


COIN_MAP = [
    ("bitcoin", "BTC"), ("ethereum", "ETH"), ("solana", "SOL"),
    ("ripple", "XRP"), ("dogecoin", "DOGE"), ("cardano", "ADA"),
    ("avalanche-2", "AVAX"), ("chainlink", "LINK"),
]


def format_market(market_data: dict, top_docs: list[dict] | None = None) -> str:
    now = _now_jst()
    lines = [f"📊 マーケット概況 | {now}", "━" * 30, ""]

    prices = market_data.get("prices", {})
    lines.append("💰 暗号資産市況")
    lines.append("")
    lines.append("| Asset | USD | JPY | 24h |")
    lines.append("| ----- | ------- | ----------- | ------ |")
    for coin_id, symbol in COIN_MAP:
        d = prices.get(coin_id, {})
        if not d:
            continue
        p = _fmt_price(d.get("usd"))
        jpy = d.get("jpy")
        jpy_str = f"¥{jpy:,.0f}" if jpy else "N/A"
        c24 = d.get("usd_24h_change")
        c_str = f"{c24:+.2f}%" if c24 is not None else "N/A"
        lines.append(f"| {symbol} | {p} | {jpy_str} | {c_str} |")
    lines.append("")

    g = market_data.get("global", {})
    if g:
        total_mc = g.get("total_market_cap", {}).get("usd")
        btc_dom = g.get("market_cap_percentage", {}).get("btc")
        mc_change = g.get("market_cap_change_percentage_24h_usd")
        parts = []
        if total_mc:
            parts.append(f"総時価総額: {_fmt_mcap(total_mc)}")
        if btc_dom:
            parts.append(f"BTC占有率: {btc_dom:.1f}%")
        if mc_change is not None:
            parts.append(f"24h: {mc_change:+.2f}%")
        if parts:
            lines.append(" | ".join(parts))
            lines.append("")

    # Fear & Greed
    fg = market_data.get("fear_greed", {})
    if fg:
        val = fg.get("value", 0)
        label = fg.get("label", "")
        emoji = "😱" if val <= 25 else "😟" if val <= 45 else "😐" if val <= 55 else "😄" if val <= 75 else "🤑"
        lines.append(f"{emoji} Fear & Greed Index: {val}（{label}）")
        lines.append("")

    if top_docs:
        lines.append("📋 主要材料")
        for doc in top_docs[:3]:
            lines.append(f"  • {doc['title'][:60]}")
            lines.append(f"    📎 {doc.get('url', '')}")
        lines.append("")

    lines.append("---")
    lines.append("💡 重要論点の詳細 → `ctie.py brief`")
    return "\n".join(lines)


def format_sources(docs: list[dict]) -> str:
    lines = ["📎 出典一覧", "━" * 30, ""]

    type_labels = {"owned": "自社", "official": "公式", "market": "市場", "signal": "シグナル"}

    for i, doc in enumerate(docs[:20], 1):
        t = type_labels.get(doc.get("source_type", ""), doc.get("source_type", ""))
        pub = doc.get("published_at", "N/A")
        if isinstance(pub, str) and len(pub) > 16:
            pub = pub[:16]
        lines.append(f"{i}. {doc['title'][:70]}")
        lines.append(f"   種別: {t} ({doc.get('source_name', '')}) | {pub}")
        lines.append(f"   🔗 {doc.get('url', 'N/A')}")
        lines.append("")

    if not docs:
        lines.append("（該当するソースがありません）")

    return "\n".join(lines)


# === Event keywords for auto-classification ===
EVENT_LAUNCH = ["launch", "ローンチ", "開始", "starts", "rolls out", "debuts", "introduces", "goes live", "pilots"]
EVENT_END = ["shut down", "終了", "ends", "discontinue", "sunset", "closes", "deprecat"]
EVENT_HACK = ["hack", "exploit", "breach", "attack", "ハック"]


def _classify_event(doc: dict) -> str | None:
    """Classify doc as event type or None."""
    text = (doc.get("title", "") + " " + doc.get("raw_text", "")).lower()
    if any(k in text for k in EVENT_HACK):
        return "🚨"
    if any(k in text for k in EVENT_LAUNCH):
        return "🚀"
    if any(k in text for k in EVENT_END):
        return "📉"
    return None


def format_events(docs: list[dict]) -> str:
    """Format event radar section."""
    lines = ["📅 イベントレーダー", "━" * 30, ""]
    events = []
    for doc in docs:
        emoji = _classify_event(doc)
        if emoji:
            events.append((emoji, doc))
    if not events:
        lines.append("（本日の注目イベントはありません）")
    else:
        for emoji, doc in events[:8]:
            lines.append(f"{emoji} {doc['title'][:70]}")
            if doc.get('url'):
                lines.append(f"🔗 {doc['url']}")
            lines.append("")
    return "\n".join(lines)


def format_full(docs: list[dict], market_data: dict, quiet: bool = False) -> str:
    """Full report: market + brief + events + sources."""
    now = _now_jst()
    sections = []
    sections.append(f"📊 CTIE 一括レポート — {now}")
    sections.append("")

    # Market
    top_docs = [d for d in docs if d.get('priority') in ('P1', 'P2')][:3]
    sections.append(format_market(market_data, top_docs))
    sections.append("")

    # Brief
    sections.append(format_brief(docs, quiet))
    sections.append("")

    # Events
    sections.append(format_events(docs))
    sections.append("")

    # Source count
    sections.append(f"💡 個別深掘り：`ctie.py sources` で出典{len(docs)}件を確認可能")

    return "\n".join(sections)
