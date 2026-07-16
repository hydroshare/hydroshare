import csv
from collections import Counter

pub  = list(csv.DictReader(open('spam_report_categorized.csv')))
priv = list(csv.DictReader(open('spam_report_private.csv')))

print('=== COMPLETE SCAN SUMMARY ===')
pub_genuine = sum(1 for r in pub if r['category'] not in ('FALSE_POSITIVE','OTHER'))
print(f'Public scan flagged:  {len(pub)}  (genuine: {pub_genuine})')
print(f'Private scan flagged: {len(priv)}')
print()

all_rows = pub + priv
cats = Counter(r.get('category','') for r in all_rows)
genuine = sum(n for cat,n in cats.items() if cat not in ('FALSE_POSITIVE','OTHER',''))
print('Combined category breakdown:')
for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
    tag = '  <- excluded' if cat in ('FALSE_POSITIVE','OTHER') else ''
    print(f'  {cat:<30} {n}{tag}')
print(f'\nTotal flagged: {len(all_rows)}')
print(f'Genuine concerns: {genuine}')

# Private external spam accounts
ext_priv = [r for r in priv if r.get('category') == 'EXTERNAL_SPAM']
user_list = [r['owner_usernames'].split('|')[0] for r in ext_priv]
email_map = {r['owner_usernames'].split('|')[0]: r['owner_emails'].split('|')[0] for r in ext_priv}
users = Counter(user_list)
unique_accounts = len(users)
print(f'\nPRIVATE external spam: {len(ext_priv)} resources across {unique_accounts} accounts (top 20):')
for u, n in sorted(users.items(), key=lambda x: -x[1])[:20]:
    print(f'  {u:<30} {n} resources  {email_map.get(u,"")}')
