"""
Aggregate spam_report_categorized.csv by owner to produce a user-level risk report.

Outputs spam_users_report.csv with one row per user, showing:
- How many resources they have per category
- A risk level (HIGH / MEDIUM / LOW)
- Their profile URL and email

Usage:
    python3 scripts/spam_users_report.py [spam_report_categorized.csv] [spam_users_report.csv]

Risk levels:
  HIGH   - has any EXTERNAL_SPAM resource, or majority of resources are spam
  MEDIUM - multiple flagged resources across TEST_DEV / GEOGRAPHIC_PLACEHOLDER / OFF_TOPIC
  LOW    - one or two minor flagged resources (student work, platform infra)
"""

import csv
import sys
from collections import defaultdict

INPUT_FILE  = sys.argv[1] if len(sys.argv) > 1 else "spam_report_categorized.csv"
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else "spam_users_report.csv"

CATEGORIES = [
    "EXTERNAL_SPAM",
    "TEST_DEV",
    "STUDENT_WORK",
    "PLATFORM_INFRA",
    "GEOGRAPHIC_PLACEHOLDER",
    "OFF_TOPIC",
    "OTHER",
]


def risk_level(counts: dict) -> str:
    ext   = counts.get("EXTERNAL_SPAM", 0)
    total = sum(counts.values())
    test  = counts.get("TEST_DEV", 0)
    geo   = counts.get("GEOGRAPHIC_PLACEHOLDER", 0)
    off   = counts.get("OFF_TOPIC", 0)
    other = counts.get("OTHER", 0)

    if ext > 0:
        return "HIGH"
    if total >= 5 or (test + geo + off + other) >= 3:
        return "MEDIUM"
    return "LOW"


# ── Read report ───────────────────────────────────────────────────────────────

users = defaultdict(lambda: {
    "owner_ids": set(),
    "owner_emails": set(),
    "owner_profile_urls": set(),
    "counts": defaultdict(int),
    "resource_titles": [],
})

with open(INPUT_FILE, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        usernames = row.get("owner_usernames", "").split("|")
        ids       = row.get("owner_ids", "").split("|")
        emails    = row.get("owner_emails", "").split("|")
        urls      = row.get("owner_profile_urls", "").split("|")
        category  = row.get("category", "OTHER") or "OTHER"
        title     = row.get("title", "")

        for i, username in enumerate(usernames):
            username = username.strip()
            if not username:
                continue
            u = users[username]
            u["owner_ids"].add(ids[i].strip() if i < len(ids) else "")
            u["owner_emails"].add(emails[i].strip() if i < len(emails) else "")
            u["owner_profile_urls"].add(urls[i].strip() if i < len(urls) else "")
            u["counts"][category] += 1
            if title:
                u["resource_titles"].append(f"[{category}] {title}")

# ── Write report ──────────────────────────────────────────────────────────────

fieldnames = [
    "username", "risk_level", "total_flagged",
    *CATEGORIES,
    "owner_ids", "owner_emails", "owner_profile_urls",
    "flagged_resource_titles",
]

rows = []
for username, data in users.items():
    total = sum(data["counts"].values())
    rows.append({
        "username":               username,
        "risk_level":             risk_level(data["counts"]),
        "total_flagged":          total,
        **{cat: data["counts"].get(cat, 0) for cat in CATEGORIES},
        "owner_ids":              "|".join(sorted(data["owner_ids"])),
        "owner_emails":           "|".join(sorted(data["owner_emails"])),
        "owner_profile_urls":     "|".join(sorted(data["owner_profile_urls"])),
        "flagged_resource_titles": " | ".join(data["resource_titles"][:10]),
    })

# Sort: HIGH first, then by total_flagged descending
rows.sort(key=lambda r: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}[r["risk_level"]], -r["total_flagged"]))

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# ── Summary ───────────────────────────────────────────────────────────────────

high   = sum(1 for r in rows if r["risk_level"] == "HIGH")
medium = sum(1 for r in rows if r["risk_level"] == "MEDIUM")
low    = sum(1 for r in rows if r["risk_level"] == "LOW")

print(f"Written {len(rows)} users to {OUTPUT_FILE}\n")
print(f"  HIGH risk:   {high}")
print(f"  MEDIUM risk: {medium}")
print(f"  LOW risk:    {low}")
print()
print("Top HIGH risk users:")
for r in [r for r in rows if r["risk_level"] == "HIGH"][:15]:
    print(f"  {r['username']:<30} {r['total_flagged']} flagged  {r['owner_emails']}")
