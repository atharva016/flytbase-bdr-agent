import json, sys
sys.stdout.reconfigure(encoding='utf-8')
f = open('pipeline_results.json', 'r', encoding='utf-8')
d = json.load(f)
m = d['pipeline_metadata']
print('=== PIPELINE RESULTS ===')
print('Duration:', m['duration_seconds'], 's')
print('Accounts:', m['total_accounts'])
print('Contacts:', m['total_contacts'])
print('Research:', m['total_research_briefs'])
print('Emails:', m['total_emails'])
print()
print('--- ACCOUNTS ---')
for a in d['accounts'].get('accounts', []):
    print(f"  {a['company_name']} ({a['country']}) - Score: {a.get('icp_match_score', '?')}")
print()
print('--- CONTACTS (first 10) ---')
for c in d['contacts'].get('contacts', [])[:10]:
    print(f"  {c['name']} @ {c['company']} - {c['title']}")
print()
print('--- EMAILS ---')
for e in d['emails'].get('emails', []):
    print(f"  To: {e['contact_name']} @ {e['company']}")
    print(f"  Subject: {e['subject']}")
    print()
