import os
import sys
import django

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from analyzer.models import Transaction, BankAccount
import json

User = get_user_model()

# Login with existing test user
client = Client()
client.login(username='totals_test', password='testpass')

# Get results page with show_changed
response = client.get('/analyzer/rules/apply/results/?show_changed=1')
html = response.content.decode('utf-8')

print("=== PAGE CONTENT CHECK ===")
print(f"Status Code: {response.status_code}")
print(f"Page contains 'Rule Application Results': {'Rule Application Results' in html}")
print(f"Page contains 'Summary': {'Summary' in html}")
print(f"Page contains 'Total Amount': {'Total Amount' in html}")
print(f"Page contains 'No transactions': {'No transactions' in html}")

# Check what's in context
print("\n=== CHECKING CONTEXT ===")
account = BankAccount.objects.get(account_name='Test Account')
# Simulate what the view does
from analyzer.views import RulesEngine
engine = RulesEngine(User.objects.get(username='totals_test'))

# Check session data
print(f"Session keys: {list(client.session.keys())}")
if 'last_rules_applied_ids' in client.session:
    print(f"Last applied IDs in session: {client.session.get('last_rules_applied_ids')}")
    print(f"Last applied prev in session: {client.session.get('last_rules_applied_prev')}")
    print(f"Last applied rule in session: {client.session.get('last_rules_applied_rule')}")

# Get transactions
txs = Transaction.objects.filter(statement__account=account, category='FOOD')
print(f"\nTransactions with FOOD category: {txs.count()}")
for tx in txs:
    print(f"  - {tx.description}: ₹{tx.amount}")

# Check for table content
print("\n=== TABLE CONTENT CHECK ===")
if '<tbody>' in html:
    tbody_idx = html.find('<tbody>')
    tbody_end = html.find('</tbody>', tbody_idx)
    tbody_content = html[tbody_idx:tbody_end+8]
    # Check if it has transaction rows
    if '<tr>' in tbody_content:
        print("✓ Table has rows")
        # Count row occurrences (excluding header rows)
        row_count = tbody_content.count('<tr>')
        print(f"  Row count in tbody: {row_count}")
        # Show a snippet
        lines = tbody_content.split('\n')[:15]
        for line in lines:
            if line.strip():
                print(f"  {line[:100]}")
    else:
        print("✗ Table has no rows")
        print(f"Tbody content length: {len(tbody_content)}")
        print(f"First 300 chars: {tbody_content[:300]}")
else:
    print("✗ No tbody found in HTML")
