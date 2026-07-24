#!/usr/bin/env python3
"""
Prepare deletion/deactivation input lists for EXTERNAL_SPAM cleanup.

This script is intentionally non-destructive.
It only reads a spam report CSV and writes two list files:
  1) resource short_ids to delete
  2) associated owner usernames

Filter criteria:
  category == EXTERNAL_SPAM

Usage:
  python3 scripts/external_spam_cleanup_plan.py \
      --input spam_report_private.csv \
      --resource-output external_spam_resource_ids.txt \
      --user-output external_spam_usernames.txt

Optional:
  --require-spam-verdict   Also require verdict == SPAM.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def normalize(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().upper()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare EXTERNAL_SPAM resource and user lists from a spam report CSV"
    )
    parser.add_argument(
        "--input",
        default="spam_report_private.csv",
        help="Path to input CSV (default: spam_report_private.csv)",
    )
    parser.add_argument(
        "--resource-output",
        default="external_spam_resource_ids.txt",
        help="Output file for resource short_ids",
    )
    parser.add_argument(
        "--user-output",
        default="external_spam_usernames.txt",
        help="Output file for owner usernames",
    )
    parser.add_argument(
        "--require-spam-verdict",
        action="store_true",
        help="Require verdict=SPAM in addition to category=EXTERNAL_SPAM",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    resource_output_path = Path(args.resource_output)
    user_output_path = Path(args.user_output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        return 1

    resource_ids: list[str] = []
    usernames: set[str] = set()

    rows = 0
    matched = 0

    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_columns = {"short_id", "category", "owner_usernames"}
        missing = sorted(required_columns - set(reader.fieldnames or []))
        if missing:
            print("ERROR: missing required columns:", ", ".join(missing))
            return 1

        for row in reader:
            rows += 1
            category = normalize(row.get("category"))
            if category != "EXTERNAL_SPAM":
                continue

            if args.require_spam_verdict:
                verdict = normalize(row.get("verdict"))
                if verdict != "SPAM":
                    continue

            short_id = (row.get("short_id") or "").strip()
            if short_id:
                resource_ids.append(short_id)

            owner_usernames = row.get("owner_usernames") or ""
            for username in owner_usernames.split("|"):
                username = username.strip()
                if username:
                    usernames.add(username)

            matched += 1

    resource_output_path.write_text(
        "\n".join(resource_ids) + ("\n" if resource_ids else ""), encoding="utf-8"
    )
    user_output_path.write_text(
        "\n".join(sorted(usernames)) + ("\n" if usernames else ""), encoding="utf-8"
    )

    print("Prepared EXTERNAL_SPAM cleanup inputs")
    print(f"  Input rows scanned:        {rows}")
    print(f"  Matching rows:             {matched}")
    print(f"  Resource ids written:      {len(resource_ids)} -> {resource_output_path}")
    print(f"  Unique users written:      {len(usernames)} -> {user_output_path}")

    print("\nSuggested next commands (review before running):")
    print("  # Delete resources in batches")
    print(
        "  xargs -a "
        f"{resource_output_path} -n 50 "
        "docker exec hydroshare python manage.py delete_resource"
    )
    print("\n  # Optional: review users list before any deactivation")
    print(f"  sed -n '1,50p' {user_output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
