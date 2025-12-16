import os
import sys
import django

# Ensure project root is on sys.path so Django settings package is importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth import get_user_model
from analyzer.models import BankAccount, BankStatement, Transaction, Rule, RuleCondition
from analyzer.rules_engine import RulesEngine
from decimal import Decimal
from datetime import date

User = get_user_model()
# Create/get test user
user, created = User.objects.get_or_create(username='rules_test_user', defaults={'email':'rules_test@example.com'})
if created:
    user.set_password('testpass')
    user.save()

acct, _ = BankAccount.objects.get_or_create(user=user, account_name='Test Account')
stmt, _ = BankStatement.objects.get_or_create(account=acct, defaults={'original_filename':'sim.csv','file_type':'CSV'})

# Create two transactions
Transaction.objects.create(statement=stmt, date=date.today(), description='Dinner at restaurant - Pizza', amount=Decimal('500.00'), transaction_type='DEBIT', category='OTHER')
Transaction.objects.create(statement=stmt, date=date.today(), description='Grocery store purchase', amount=Decimal('1200.00'), transaction_type='DEBIT', category='OTHER')

# Create a rule with a keyword condition
rule, _ = Rule.objects.get_or_create(user=user, name='Restaurant Rule', defaults={'category':'FOOD','is_active':True,'rule_type':'OR'})
# Ensure a matching condition exists
rc, _ = RuleCondition.objects.get_or_create(rule=rule, condition_type='KEYWORD', defaults={'keyword':'restaurant','keyword_match_type':'CONTAINS'})
# If condition existed but missing fields, update them
rc.keyword = 'restaurant'
rc.keyword_match_type = 'CONTAINS'
rc.save()

# Apply rules via engine
engine = RulesEngine(user)
updated = []
for tx in Transaction.objects.filter(statement__account=acct):
    tx_data = {'date': tx.date, 'description': tx.description, 'amount': float(tx.amount), 'transaction_type': tx.transaction_type}
    matched_rule = engine.find_matching_rule(tx_data)
    if matched_rule and matched_rule.category != tx.category:
        prev = tx.category
        tx.category = matched_rule.category
        tx.save()
        updated.append({'id': tx.id, 'description': tx.description, 'previous': prev, 'current': tx.category, 'matched_rule': matched_rule.name, 'amount': float(tx.amount)})

print('Updated transactions:')
for u in updated:
    print(u)

# Compute totals per rule
totals = {}
counts = {}
for u in updated:
    name = u.get('matched_rule') or 'Unmatched'
    amt = u.get('amount', 0.0)
    totals[name] = totals.get(name, 0.0) + amt
    counts[name] = counts.get(name, 0) + 1

print('\nTotals by rule:')
for name in totals:
    print(f"{name}: {totals[name]:.2f} ({counts[name]})")

# Prepare results list similar to view
results = []
for tx in Transaction.objects.filter(id__in=[u['id'] for u in updated]).select_related('statement','statement__account'):
    results.append({
        'id': tx.id,
        'date': tx.date,
        'description': tx.description,
        'amount': tx.amount,
        'current_category': tx.category,
        'matched_rule_name': next((x['matched_rule'] for x in updated if x['id'] == tx.id), None),
        'previous_category': next((x['previous'] for x in updated if x['id'] == tx.id), None),
        'account_name': tx.statement.account.account_name,
    })

print('\nResults rows:')
for r in results:
    print(r)
