#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Transaction, Rule
from analyzer.rules_engine import RulesEngine

user = User.objects.filter(is_superuser=False).first()
rule = Rule.objects.get(id=1, user=user)

# Get first CREDIT transaction
tx = Transaction.objects.filter(
    statement__account__user=user,
    transaction_type='CREDIT'
).first()

print(f"Rule: {rule.name}")
print(f"Keyword: '{rule.conditions.first().keyword}'")
print(f"Match Type: {rule.conditions.first().keyword_match_type}")

print(f"\nTransaction ID {tx.id}:")
print(f"Description: {tx.description}")
print(f"Type: {tx.transaction_type}")

# Manual check
desc = tx.description.lower()
keyword = 'cr'
print(f"\nManual check:")
print(f"  Description (lower): '{desc}'")
print(f"  Keyword: '{keyword}'")
print(f"  Is '{keyword}' in description? {keyword in desc}")

# Engine check
tx_data = {
    'date': tx.date,
    'description': tx.description,
    'amount': float(tx.amount),
    'transaction_type': tx.transaction_type
}

engine = RulesEngine(user)
matches = engine._matches_rule(tx_data, rule)
print(f"\nEngine says matches? {matches}")

# Check condition directly
cond = rule.conditions.first()
cond_matches = engine._matches_condition(tx_data, cond)
print(f"Condition matches? {cond_matches}")

# Check keyword method
kw_matches = engine._matches_keyword_condition(tx_data, cond)
print(f"Keyword condition matches? {kw_matches}")
