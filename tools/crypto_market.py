"""M2: Crypto Market — prices, global stats, and key materials."""

from engine.sources import fetch_crypto_prices, fetch_global_market, fetch_all_news
from engine.dedup import dedup_documents
from engine.scorer import score_all
from tools.common import now_jst_iso


def get_crypto_market(assets: str = "BTC,ETH,SOL,XRP") -> str:
    asset_list = [a.strip().upper() for a in assets.split(",")]

    prices = fetch_crypto_prices(asset_list)
    global_data = fetch_global_market()

    lines = []
    lines.append(f"[CTIE Crypto Market] {now_jst_iso()}")
    if prices.get("_source") == "coinmarketcap":
        lines.append("(source: CoinMarketCap — CoinGecko unavailable)")
    elif prices.get("_stale"):
        lines.append(f"⚠ Price data is stale (API unavailable, using data from {prices['_cache_age_sec']}s ago)")
    elif prices.get("_cached"):
        lines.append(f"(cached data, {prices['_cache_age_sec']}s ago)")
    if global_data.get("_stale"):
        lines.append(f"⚠ Global data is stale (API unavailable, using data from {global_data['_cache_age_sec']}s ago)")
    elif global_data.get("_cached"):
        lines.append(f"(global: cached data, {global_data['_cache_age_sec']}s ago)")
    lines.append("")

    # Prices
    if "error" in prices:
        lines.append(f"⚠ Price data: {prices['error']}")
    else:
        lines.append("== Asset Prices ==")
        for sym, info in prices.get("prices", {}).items():
            usd = info.get("usd")
            jpy = info.get("jpy")
            change = info.get("usd_24h_change")
            mcap = info.get("usd_market_cap")
            usd_str = f"${usd:,.2f}" if usd else "N/A"
            jpy_str = f"¥{jpy:,.0f}" if jpy else "N/A"
            chg_str = f"{change:+.2f}%" if change is not None else "N/A"
            mcap_str = f"${mcap/1e9:,.1f}B" if mcap else "N/A"
            lines.append(f"  {sym}: {usd_str} / {jpy_str}  (24h: {chg_str})  MCap: {mcap_str}")
        lines.append("")

    # Global
    if "error" in global_data:
        lines.append(f"⚠ Global data: {global_data['error']}")
    else:
        total_mcap = global_data.get("total_market_cap_usd")
        btc_dom = global_data.get("btc_dominance")
        mcap_chg = global_data.get("market_cap_change_24h")
        lines.append("== Global Market ==")
        if total_mcap:
            lines.append(f"  Total Market Cap: ${total_mcap/1e12:,.2f}T")
        if btc_dom is not None:
            lines.append(f"  BTC Dominance: {btc_dom:.1f}%")
        if mcap_chg is not None:
            lines.append(f"  24h Change: {mcap_chg:+.2f}%")
        lines.append("")

    # Key materials from M1
    lines.append("== Key Materials (from news) ==")
    try:
        docs = fetch_all_news()
        docs = dedup_documents(docs)
        docs = score_all(docs)
        top = [d for d in docs if d["priority"] in ("P1", "P2")][:3]
        if top:
            for d in top:
                lines.append(f"  [{d['priority']}] {d['title']}")
                lines.append(f"    Source: {d['source_name']} | URL: {d.get('url', 'N/A')}")
        else:
            lines.append("  No major materials.")
    except Exception:
        lines.append("  (News fetch unavailable)")

    return "\n".join(lines)
