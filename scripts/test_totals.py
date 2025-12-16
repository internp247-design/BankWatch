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

User = get_user_model()

# Clean up test data first
User.objects.filter(username='totals_test').delete()

# Create test user
user = User.objects.create_user(username='totals_test', email='totals@example.com', password='testpass')
print(f"✓ Created test user: {user.username}")

# Create account
account = BankAccount.objects.create(user=user, account_name='Test Account', bank_name='Test Bank')
print(f"✓ Created account: {account.account_name}")

# Create statement
statement = BankStatement.objects.create(account=account, original_filename='test.csv', file_type='CSV')
print(f"✓ Created statement: {statement.id}")

# Create test transactions
tx1 = Transaction.objects.create(
    statement=statement,
    date=date.today(),
    description='Coffee at Starbucks',
    amount=Decimal('250.00'),
    transaction_type='DEBIT',
    category='OTHER'
)
tx2 = Transaction.objects.create(
    statement=statement,
    date=date.today(),
    description='Lunch at restaurant',
    amount=Decimal('600.00'),
    transaction_type='DEBIT',
    category='OTHER'
)
tx3 = Transaction.objects.create(
    statement=statement,
    date=date.today(),
    description='Dinner at cafe',
    amount=Decimal('350.00'),
    transaction_type='DEBIT',
    category='OTHER'
)
tx4 = Transaction.objects.create(
    statement=statement,
    date=date.today(),
    description='Grocery shopping',
    amount=Decimal('800.00'),
    transaction_type='DEBIT',
    category='OTHER'
)
print(f"✓ Created 4 test transactions")

# Create a rule for Food
rule_food = Rule.objects.create(
    user=user,
    name='Restaurant & Cafe Rule',
    category='FOOD',
    is_active=True,
    rule_type='OR'
)
RuleCondition.objects.create(
    rule=rule_food,
    condition_type='KEYWORD',
    keyword='restaurant',
    keyword_match_type='CONTAINS'
)
RuleCondition.objects.create(
    rule=rule_food,
    condition_type='KEYWORD',
    keyword='starbucks',
    keyword_match_type='CONTAINS'
)
RuleCondition.objects.create(
    rule=rule_food,
    condition_type='KEYWORD',
    keyword='cafe',
    keyword_match_type='CONTAINS'
)
print(f"✓ Created rule: {rule_food.name} → {rule_food.get_category_display()}")

# Test client for HTTP requests
client = Client()
print("\n--- Testing Totals Display ---")

# Test 1: Login
result = client.login(username='totals_test', password='testpass')
print(f"✓ Login: {'SUCCESS' if result else 'FAILED'}")

# Test 2: Apply rules (POST with account_id)
response = client.post('/analyzer/rules/apply/', {'account_id': account.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
print(f"✓ Apply rules: {response.status_code} (expect 200)")
if response.status_code == 200:
    import json
    data = json.loads(response.content)
    print(f"  - Updated {data.get('updated', 0)} transactions")
    print(f"  - Expected: 3 transactions (coffee, restaurant, cafe)")

# Test 3: View results with show_changed to get totals
response = client.get('/analyzer/rules/apply/results/?show_changed=1')
html_content = response.content.decode('utf-8')
print(f"\n✓ Results page (show_changed): {response.status_code}")

# Check for totals in HTML
if 'Summary: Total Amount by Rule' in html_content:
    print("  ✓ Totals summary card found in HTML")
else:
    print("  ✗ Totals summary card NOT found in HTML")

if 'Restaurant & Cafe Rule' in html_content:
    print("  ✓ Rule name found in HTML")
else:
    print("  ✗ Rule name NOT found in HTML")

# Check for rule total amount (should be 250 + 600 + 350 = 1200)
if '1200.00' in html_content:
    print("  ✓ Total amount 1200.00 found in HTML")
else:
    print("  ✗ Total amount NOT found in HTML")
    # Try to find what amounts are there
    import re
    amounts = re.findall(r'₹[\d,]+\.\d{2}', html_content)
    print(f"  Found amounts in page: {amounts}")

# Check transaction count (should be 3)
if '3 transactions' in html_content or '3 transaction' in html_content:
    print("  ✓ Transaction count (3) found in HTML")
else:
    print("  ✗ Transaction count NOT found in HTML")

# Verify transactions were updated
tx1.refresh_from_db()
tx2.refresh_from_db()
tx3.refresh_from_db()
tx4.refresh_from_db()
print(f"\n--- Transaction Category Updates ---")
print(f"  Coffee tx: {tx1.category} (expect FOOD)")
print(f"  Restaurant tx: {tx2.category} (expect FOOD)")
print(f"  Cafe tx: {tx3.category} (expect FOOD)")
print(f"  Grocery tx: {tx4.category} (expect OTHER)")

print("\n✅ All tests completed!")
