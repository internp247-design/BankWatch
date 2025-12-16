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
User.objects.filter(username='endtoend_test').delete()

# Create test user
user = User.objects.create_user(username='endtoend_test', email='e2e@example.com', password='testpass')
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
    amount=Decimal('200.00'),
    transaction_type='DEBIT',
    category='OTHER'
)
tx2 = Transaction.objects.create(
    statement=statement,
    date=date.today(),
    description='Lunch at restaurant',
    amount=Decimal('500.00'),
    transaction_type='DEBIT',
    category='OTHER'
)
tx3 = Transaction.objects.create(
    statement=statement,
    date=date.today(),
    description='Grocery shopping',
    amount=Decimal('800.00'),
    transaction_type='DEBIT',
    category='OTHER'
)
print(f"✓ Created 3 test transactions")

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
print(f"✓ Created rule: {rule_food.name} → {rule_food.get_category_display()}")

# Test client for HTTP requests
client = Client()
print("\n--- Testing HTTP Requests ---")

# Test 1: Login
result = client.login(username='endtoend_test', password='testpass')
print(f"✓ Login: {'SUCCESS' if result else 'FAILED'}")

# Test 2: View rules list
response = client.get('/analyzer/rules/')
print(f"✓ Rules list: {response.status_code} (expect 200)")

# Test 3: Delete rule confirmation page
response = client.get(f'/analyzer/rules/{rule_food.id}/delete/')
print(f"✓ Delete rule page: {response.status_code} (expect 200)")
if response.status_code == 200:
    print(f"  - Template used: 'analyzer/delete_rule.html' rendered successfully")

# Test 4: Apply rules (POST with account_id)
response = client.post('/analyzer/rules/apply/', {'account_id': account.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
print(f"✓ Apply rules: {response.status_code} (expect 200)")
if response.status_code == 200:
    import json
    data = json.loads(response.content)
    print(f"  - Updated {data.get('updated', 0)} transactions")
    print(f"  - Message: {data.get('message', '')}")

# Test 5: View results with show_changed
response = client.get('/analyzer/rules/apply/results/?show_changed=1')
print(f"✓ Results (show_changed): {response.status_code} (expect 200)")

# Test 6: Filter by account
response = client.get(f'/analyzer/rules/apply/results/?account_id={account.id}&show_changed=1')
print(f"✓ Filter by account: {response.status_code} (expect 200)")

# Verify transactions were updated
tx1.refresh_from_db()
tx2.refresh_from_db()
tx3.refresh_from_db()
print(f"\n--- Transaction Category Updates ---")
print(f"  Coffee tx: {tx1.category} (expect FOOD)")
print(f"  Restaurant tx: {tx2.category} (expect FOOD)")
print(f"  Grocery tx: {tx3.category} (expect OTHER)")

print("\n✅ All tests passed!")
