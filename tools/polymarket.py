"""M5: Polymarket — large high-conviction bets from prediction markets."""

from tools.common import safe_request, now_jst_iso
from config.settings import POLYMARKET_API


def scan_polymarket(min_size: int = 10000, min_price: float = 0.95, limit: int = 10) -> str:
    # Fetch active events
    resp = safe_request(
        f"{POLYMARKET_API}/events",
        params={"active": "true", "closed": "false", "limit": "50"},
    )
    if resp is None:
        return (
            f"[CTIE Polymarket] {now_jst_iso()}\n\n"
            "⚠ Polymarket API is currently unavailable. Try again later."
        )

    try:
        events = resp.json()
    except Exception:
        return (
            f"[CTIE Polymarket] {now_jst_iso()}\n\n"
            "⚠ Failed to parse Polymarket response."
        )

    if not events:
        return (
            f"[CTIE Polymarket] {now_jst_iso()}\n\n"
            "No active events found."
        )

    big_bets = []

    for event in events:
        title = event.get("title", "Unknown Event")
        markets = event.get("markets", [])

        for market in markets:
            # Look for high-volume, high-conviction outcomes
            volume = 0
            try:
                volume = float(market.get("volume", 0) or 0)
            except (ValueError, TypeError):
                pass

            # Check outcome prices for high conviction
            outcomes = market.get("outcomePrices", [])
            if isinstance(outcomes, str):
                try:
                    import json
                    outcomes = json.loads(outcomes)
                except Exception:
                    outcomes = []

            max_price = 0.0
            for price in outcomes:
                try:
                    p = float(price)
                    max_price = max(max_price, p)
                except (ValueError, TypeError):
                    pass

            if volume >= min_size and max_price >= min_price:
                big_bets.append({
                    "event_title": title,
                    "market_question": market.get("question", title),
                    "volume": volume,
                    "max_price": max_price,
                    "liquidity": market.get("liquidity", "N/A"),
                })

    # Sort by volume descending
    big_bets.sort(key=lambda x: x["volume"], reverse=True)
    big_bets = big_bets[:limit]

    lines = []
    lines.append(f"[CTIE Polymarket] {now_jst_iso()}")
    lines.append(f"High-conviction bets (volume>=${min_size}, price>={min_price}): {len(big_bets)}")
    lines.append("")

    for i, bet in enumerate(big_bets, 1):
        vol_str = f"${bet['volume']:,.0f}"
        lines.append(f"[{i}] {bet['market_question']}")
        lines.append(f"    Event: {bet['event_title']}")
        lines.append(f"    Volume: {vol_str} | Max Price: {bet['max_price']:.2f}")
        liq = bet.get("liquidity")
        if liq and liq != "N/A":
            try:
                lines.append(f"    Liquidity: ${float(liq):,.0f}")
            except (ValueError, TypeError):
                pass
        lines.append("")

    if not big_bets:
        lines.append("No large high-conviction bets found matching criteria.")

    return "\n".join(lines)
