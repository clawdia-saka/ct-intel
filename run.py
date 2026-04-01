#!/usr/bin/env python3
"""CTIE — Crypto Times Intelligence Engine

CLI tool router. Each tool fetches data, scores, and returns structured text.
No LLM calls. Formatting is done by the agent via SKILL.md.

Usage:
    python run.py <tool_name> [json_args]

Examples:
    python run.py get_morning_brief
    python run.py get_crypto_market '{"assets": "BTC,ETH,SOL"}'
    python run.py scan_polymarket '{"min_size": 5000}'
"""

import sys
import os
import json
import argparse
import importlib

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TOOLS = {
    "get_morning_brief": ("tools.morning_brief", "get_morning_brief"),
    "get_crypto_market": ("tools.crypto_market", "get_crypto_market"),
    "get_source_vault": ("tools.source_vault", "get_source_vault"),
    "get_event_radar": ("tools.event_radar", "get_event_radar"),
    "scan_polymarket": ("tools.polymarket", "scan_polymarket"),
    "get_raw_data": ("tools.raw_data", "get_raw_data"),
    "get_macro": ("tools.macro", "get_macro"),
}


def main():
    parser = argparse.ArgumentParser(
        description="CTIE — Crypto Times Intelligence Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join([
            "Available tools:",
            "  get_morning_brief   M1: Today's key topics with priority scoring",
            "  get_crypto_market   M2: Crypto prices + global market + key materials",
            "  get_source_vault    M3: Source attribution list",
            "  get_event_radar     M4: Upcoming events (macro/unlock/protocol/listing)",
            "  scan_polymarket     M5: Polymarket high-conviction bets",
            "  get_raw_data        M6: Raw article data (CT + international)",
            "  get_macro           M7: Macro & commodities (free APIs)",
        ]),
    )
    parser.add_argument("tool_name", nargs="?", help="Tool to execute")
    parser.add_argument("json_args", nargs="?", default="{}", help="JSON arguments (optional)")

    args = parser.parse_args()

    if not args.tool_name:
        parser.print_help()
        sys.exit(0)

    if args.tool_name not in TOOLS:
        print(f"Error: Unknown tool '{args.tool_name}'")
        print(f"Available: {', '.join(TOOLS.keys())}")
        sys.exit(1)

    module_path, func_name = TOOLS[args.tool_name]

    try:
        kwargs = json.loads(args.json_args)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON arguments: {e}")
        sys.exit(1)

    mod = importlib.import_module(module_path)
    func = getattr(mod, func_name)

    result = func(**kwargs)
    print(result)


if __name__ == "__main__":
    main()
