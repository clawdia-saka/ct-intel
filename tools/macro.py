"""M7: Macro & Commodities — traditional market data from free APIs."""

from tools.common import safe_request, now_jst_iso
from config.settings import COINGECKO_BASE


def _fetch_coingecko_commodities() -> dict:
    """Fetch gold price via tokenized gold assets on CoinGecko."""
    resp = safe_request(
        f"{COINGECKO_BASE}/simple/price",
        params={
            "ids": "pax-gold,tether-gold",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
    )
    result = {}
    if resp:
        try:
            data = resp.json()
            # Collect all available gold token prices
            gold_prices = []
            tokens = [
                ("pax-gold", "PAXG"),
                ("tether-gold", "XAUT"),
            ]
            for cg_id, symbol in tokens:
                info = data.get(cg_id, {})
                if info.get("usd"):
                    gold_prices.append({
                        "symbol": symbol,
                        "price": info["usd"],
                        "change": info.get("usd_24h_change"),
                    })
            if gold_prices:
                # Use average as gold reference
                avg_price = sum(g["price"] for g in gold_prices) / len(gold_prices)
                avg_change = None
                changes = [g["change"] for g in gold_prices if g["change"] is not None]
                if changes:
                    avg_change = sum(changes) / len(changes)
                sources = "/".join(g["symbol"] for g in gold_prices)
                result["GOLD"] = {
                    "price_usd": round(avg_price, 2),
                    "change_24h": round(avg_change, 2) if avg_change is not None else None,
                    "source_tokens": sources,
                    "detail": gold_prices,
                }
        except Exception:
            pass
    return result


def _fetch_exchange_rates() -> dict:
    """Fetch USD/JPY from a free exchange rate API."""
    result = {}
    # Try exchangerate.host (free, no key required)
    resp = safe_request(
        "https://api.exchangerate.host/latest",
        params={"base": "USD", "symbols": "JPY"},
    )
    if resp:
        try:
            data = resp.json()
            rates = data.get("rates", {})
            if rates.get("JPY"):
                result["USD/JPY"] = {"rate": rates["JPY"]}
        except Exception:
            pass

    # Fallback: open.er-api.com
    if "USD/JPY" not in result:
        resp2 = safe_request("https://open.er-api.com/v6/latest/USD")
        if resp2:
            try:
                data = resp2.json()
                rates = data.get("rates", {})
                if rates.get("JPY"):
                    result["USD/JPY"] = {"rate": rates["JPY"]}
            except Exception:
                pass
    return result


def _fetch_fear_greed() -> dict:
    """Crypto Fear & Greed Index (free API)."""
    resp = safe_request("https://api.alternative.me/fng/?limit=1")
    if resp:
        try:
            data = resp.json()
            entry = data.get("data", [{}])[0]
            return {
                "value": int(entry.get("value", 0)),
                "classification": entry.get("value_classification", ""),
            }
        except Exception:
            pass
    return {}


def get_macro() -> str:
    lines = []
    lines.append(f"[CTIE Macro & Commodities] {now_jst_iso()}")
    lines.append("")
    lines.append("Note: Free API sources only (no API key). Some data may be unavailable.")
    lines.append("")

    commodities = _fetch_coingecko_commodities()
    lines.append("== Commodities ==")
    gold = commodities.get("GOLD")
    if gold:
        p_str = f"${gold['price_usd']:,.2f}"
        c_str = f"{gold['change_24h']:+.2f}%" if gold.get('change_24h') is not None else "N/A"
        lines.append(f"  GOLD: {p_str} (24h: {c_str})  source: {gold.get('source_tokens', 'N/A')}")
        for detail in gold.get("detail", []):
            d_str = f"${detail['price']:,.2f}"
            dc_str = f"{detail['change']:+.2f}%" if detail.get('change') is not None else ""
            lines.append(f"    {detail['symbol']}: {d_str} {dc_str}")
    else:
        lines.append("  GOLD: データ取得不可")
    lines.append("")

    # Exchange rates
    fx = _fetch_exchange_rates()
    lines.append("== Forex ==")
    if fx:
        for pair, info in fx.items():
            rate = info.get("rate")
            lines.append(f"  {pair}: {rate:.2f}" if rate else f"  {pair}: N/A")
    else:
        lines.append("  USD/JPY: データ取得不可")
    lines.append("  DXY: データ取得不可 (no free API without key)")
    lines.append("")

    # US indices - typically need paid APIs
    lines.append("== US Indices ==")
    lines.append("  S&P500: データ取得不可 (requires paid API)")
    lines.append("  NASDAQ: データ取得不可 (requires paid API)")
    lines.append("  US 10Y Treasury: データ取得不可 (requires paid API)")
    lines.append("")

    # Crypto Fear & Greed as bonus
    fng = _fetch_fear_greed()
    if fng:
        lines.append("== Crypto Fear & Greed Index ==")
        lines.append(f"  Value: {fng.get('value', 'N/A')} ({fng.get('classification', '')})")
        lines.append("")

    return "\n".join(lines)
