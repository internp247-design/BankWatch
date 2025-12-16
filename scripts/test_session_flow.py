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
from analyzer.models import BankAccount, BankStatement, Transaction, Rule, RuleCondition
from decimal import Decimal
from datetime import date
import json

User = get_user_model()

# Clean up
User.objects.filter(username='session_test').delete()

# Create test user
user = User.objects.create_user(username='session_test', email='session@example.com', password='testpass')
print(f"✓ Created test user")

# Create account
account = BankAccount.objects.create(user=user, account_name='Session Account')
print(f"✓ Created account")

# Create statement and transactions
statement = BankStatement.objects.create(account=account, original_filename='test.csv', file_type='CSV')
tx1 = Transaction.objects.create(statement=statement, date=date.today(), description='Dinner at restaurant', amount=Decimal('500.00'), transaction_type='DEBIT', category='OTHER')
tx2 = Transaction.objects.create(statement=statement, date=date.today(), description='Coffee at cafe', amount=Decimal('200.00'), transaction_type='DEBIT', category='OTHER')
print(f"✓ Created 2 transactions")

# Create rule
rule = Rule.objects.create(user=user, name='Food Rule', category='FOOD', is_active=True, rule_type='OR')
RuleCondition.objects.create(rule=rule, condition_type='KEYWORD', keyword='restaurant', keyword_match_type='CONTAINS')
RuleCondition.objects.create(rule=rule, condition_type='KEYWORD', keyword='cafe', keyword_match_type='CONTAINS')
print(f"✓ Created rule")

# Use Django test client to maintain session
client = Client()
client.login(username='session_test', password='testpass')
print(f"✓ Logged in\n")

# Step 1: Apply rules and get redirect URL
print("=== STEP 1: Apply Rules ===")
apply_response = client.post('/analyzer/rules/apply/', {'account_id': account.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
print(f"Apply response: {apply_response.status_code}")
if apply_response.status_code == 200:
    data = json.loads(apply_response.content)
    print(f"Updated: {data.get('updated')} transactions")
    redirect_url = data.get('redirect_url')
    print(f"Redirect URL: {redirect_url}")
else:
    print(f"Apply failed: {apply_response.content}")
    redirect_url = '/analyzer/rules/apply/results/?show_changed=1'

# Step 2: Follow redirect in SAME client (preserves session)
print(f"\n=== STEP 2: View Results (same client/session) ===")
results_response = client.get(redirect_url if redirect_url else '/analyzer/rules/apply/results/?show_changed=1')
print(f"Results response: {results_response.status_code}")
html = results_response.content.decode('utf-8')

# Check for totals
print(f"\n=== CHECKING RESULTS PAGE ===")
print(f"Contains 'Summary': {'Summary' in html}")
print(f"Contains 'Food Rule': {'Food Rule' in html}")
print(f"Contains '700.00': {'700.00' in html}")  # 500 + 200
print(f"Contains '2 transaction': {'2 transaction' in html}")
print(f"Contains 'No transactions': {'No transactions' in html}")

# Extract what we can find
if 'Summary' in html:
    print("\n✓ TOTALS SECTION FOUND!")
    import re
    # Find all currency amounts
    amounts = re.findall(r'₹[\d,]+\.\d{2}', html)
    print(f"  Amounts in page: {amounts}")
    # Find rule names
    rule_names = re.findall(r'<p class="mb-1 text-muted small">([^<]+)</p>', html)
    print(f"  Rule names: {rule_names}")
    # Find transaction counts
    tx_counts = re.findall(r'(\d+) transaction', html)
    print(f"  Transaction counts: {tx_counts}")
else:
    print("\n✗ Totals section NOT found")
    if 'No transactions were changed' in html:
        print("  Reason: Showing 'No transactions were changed' message")
    elif 'No transactions found' in html:
        print("  Reason: Showing 'No transactions found' message")
    else:
        print("  Table structure:")
        # Find tbody
        if '<tbody>' in html:
            tbody_start = html.find('<tbody>')
            tbody_end = html.find('</tbody>')
            tbody = html[tbody_start:tbody_end+8]
            print(f"  Tbody has {tbody.count('<tr>')} rows")

print("\n✅ Test complete")
