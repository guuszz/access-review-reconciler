from __future__ import annotations

import argparse
import json
import sys

from access_review.reconcile import reconcile_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare local people and account CSV fixtures")
    parser.add_argument("people_csv")
    parser.add_argument("accounts_csv")
    parser.add_argument("--exceptions", help="optional CSV with email,reason for documented account exceptions")
    args = parser.parse_args()
    try:
        report = reconcile_files(args.people_csv, args.accounts_csv, args.exceptions)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["review_required"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
