#!/usr/bin/env python3
"""CT-Intel: Crypto Times Intelligence Engine"""
import argparse, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="CT-Intel: 暗号資産市場の重要論点を抽出・整理")
    parser.add_argument("command", nargs="?", default="brief",
                        choices=["brief", "market", "sources", "events", "full", "refresh"],
                        help="brief=重要論点, market=市況, sources=出典, events=イベント, full=一括, refresh=データ更新")
    parser.add_argument("--no-refresh", action="store_true", help="キャッシュから出力（データ再取得しない）")
    args = parser.parse_args()

    refresh = args.command == "refresh" or not args.no_refresh
    try:
        result = run_pipeline(command=args.command, refresh=refresh)
        print(result)
    except Exception as e:
        print(f"❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
