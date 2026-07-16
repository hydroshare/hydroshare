"""
Merge public and private spam reports into a single combined user risk report.
Excludes known false positives (jeff, lizabrazil from private EXTERNAL_SPAM).

Usage:
    python3 scripts/spam_users_combined_report.py
"""

import csv
from collections import defaultdict

PUBLIC_CSV    = "spam_report_categorized.csv"
PRIVATE_CSV   = "spam_report_private.csv"
OUTPUT_CSV    = "spam_users_combined_report.csv"
SECURITY_CSV  = "spam_security_report.csv"   # EXTERNAL_SPAM only

# Known legitimate users/entities to exclude entirely from the report
KNOWN_ENTITIES = {
    # CUAHSI staff
    "drew", "sblack", "mseul", "dcowan", "danames", "abogan", "lplatt",
    "igarousi", "sblack-admin", "etran", "jpollak", "eclark@cuahsi.org",
    "clenhardt", "ndebuhr", "alvacouch", "mahesh437", "lizabrazil",
    "mahes", "mahesh437", "pkDemo", "selenium-user1", "selenium-user4",
    "datamgr-harvey", "kimberleewong",
    # Core HydroShare developers/researchers
    "dtarb", "pkdash", "TonyCastronova", "ChristinaBandaragoda", "aymnassar",
    "choi", "GanTian", "tanumalik", "ClaraCogswell", "sherry", "bartnijssen",
    "dtijerina", "ehhabib", "aaraney", "devin.r.cowan@dartmouth.edu",
    "klippold", "apatel54", "abnerbog", "kenneth.lippold", "ciroh-data",
    "seanbc@hawaii.edu", "jirikadlec2", "jsadler", "jsadler2", "max.kaye",
    "aphelionz", "belizelane", "soumyapurohit", "scootna", "fbaig",
    # CZO / critical zone observatory
    "czo", "czo_boulder", "czo_national",
    # Other known legitimate users
    "CTEMPs", "aufdenkampe", "iUTAHData", "mattwheelwright", "courtneyflint",
    "maidment@utexas.edu", "jdbales", "morsy", "njones@byu.edu",
    "fernando.r.salas", "x", "published", "Jmasterman", "sandesh",
    "shaowen", "Mauriel", "devincowan@pm.me", "hzhang01.cuahsi.org",
    "hzhang", "mahesh437",
}

# Known false positives to exclude from EXTERNAL_SPAM classification only
FALSE_POS_USERS = {"jeff", "lizabrazil", "sherry"}

CATEGORIES = [
    "EXTERNAL_SPAM",
    "TEST_DEV",
    "STUDENT_WORK",
    "PLATFORM_INFRA",
    "GEOGRAPHIC_PLACEHOLDER",
    "OFF_TOPIC",
    "FALSE_POSITIVE",
    "OTHER",
]


def risk_level(counts: dict) -> str:
    ext   = counts.get("EXTERNAL_SPAM", 0)
    total = sum(v for k, v in counts.items() if k not in ("FALSE_POSITIVE", "OTHER"))

    if ext > 0:
        return "HIGH"
    if total >= 5 or sum(counts.get(c, 0) for c in ("TEST_DEV","GEOGRAPHIC_PLACEHOLDER","OFF_TOPIC","OTHER")) >= 3:
        return "MEDIUM"
    return "LOW"


def load_report(path, source_label, users):
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row.get("category", "OTHER") or "OTHER"
            usernames = row.get("owner_usernames", "").split("|")
            ids       = row.get("owner_ids", "").split("|")
            emails    = row.get("owner_emails", "").split("|")
            urls      = row.get("owner_profile_urls", "").split("|")
            title     = row.get("title", "")

            for i, username in enumerate(usernames):
                username = username.strip()
                if not username:
                    continue
                # Skip known legitimate entities entirely
                if username in KNOWN_ENTITIES:
                    continue

                # Demote known false positives from EXTERNAL_SPAM
                effective_category = category
                if category == "EXTERNAL_SPAM" and username in FALSE_POS_USERS:
                    effective_category = "FALSE_POSITIVE"

                u = users[username]
                u["owner_ids"].add(ids[i].strip() if i < len(ids) else "")
                u["owner_emails"].add(emails[i].strip() if i < len(emails) else "")
                u["owner_profile_urls"].add(urls[i].strip() if i < len(urls) else "")
                u["counts"][effective_category] = u["counts"].get(effective_category, 0) + 1
                u["sources"].add(source_label)
                if title and len(u["sample_titles"]) < 5:
                    u["sample_titles"].append(f"[{effective_category}] {title[:60]}")


# ── Load both reports ─────────────────────────────────────────────────────────

users = defaultdict(lambda: {
    "owner_ids": set(),
    "owner_emails": set(),
    "owner_profile_urls": set(),
    "counts": {},
    "sources": set(),
    "sample_titles": [],
})

load_report(PUBLIC_CSV,  "public",  users)
load_report(PRIVATE_CSV, "private", users)

# ── Write combined report ─────────────────────────────────────────────────────

fieldnames = [
    "username", "risk_level", "source", "total_genuine_flagged",
    *CATEGORIES,
    "owner_ids", "owner_emails", "owner_profile_urls",
    "sample_flagged_titles",
]

rows = []
for username, data in users.items():
    total = sum(v for k, v in data["counts"].items() if k not in ("FALSE_POSITIVE","OTHER"))
    rows.append({
        "username":             username,
        "risk_level":           risk_level(data["counts"]),
        "source":               "|".join(sorted(data["sources"])),
        "total_genuine_flagged": total,
        **{cat: data["counts"].get(cat, 0) for cat in CATEGORIES},
        "owner_ids":            "|".join(sorted(data["owner_ids"])),
        "owner_emails":         "|".join(sorted(data["owner_emails"])),
        "owner_profile_urls":   "|".join(sorted(data["owner_profile_urls"])),
        "sample_flagged_titles": " | ".join(data["sample_titles"][:5]),
    })

rows.sort(key=lambda r: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}[r["risk_level"]], -r["total_genuine_flagged"]))

# Full combined report (all flagged users)
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# Security-focused report: only accounts with confirmed EXTERNAL_SPAM resources
security_rows = [r for r in rows if r["EXTERNAL_SPAM"] > 0]
with open(SECURITY_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(security_rows)

# ── Summary ───────────────────────────────────────────────────────────────────

high   = [r for r in rows if r["risk_level"] == "HIGH"]
medium = [r for r in rows if r["risk_level"] == "MEDIUM"]
low    = [r for r in rows if r["risk_level"] == "LOW"]

print(f"Written {len(rows)} users to {OUTPUT_CSV}")
print(f"Written {len(security_rows)} malicious accounts to {SECURITY_CSV}\n")
print(f"--- SECURITY REPORT (EXTERNAL_SPAM only) ---")
print(f"  Malicious accounts: {len(security_rows)}")
print(f"  Total EXTERNAL_SPAM resources: {sum(r['EXTERNAL_SPAM'] for r in security_rows)}")
print()
print(f"--- FULL REPORT (all flagged) ---")
print(f"  HIGH risk:   {len(high)}")
print(f"  MEDIUM risk: {len(medium)}")
print(f"  LOW risk:    {len(low)}")
print()
print(f"Top malicious accounts by EXTERNAL_SPAM count:")
for r in sorted(security_rows, key=lambda r: -r["EXTERNAL_SPAM"])[:20]:
    print(f"  {r['username']:<35} {r['EXTERNAL_SPAM']:>3} spam resources  {r['owner_emails'][:50]}")
