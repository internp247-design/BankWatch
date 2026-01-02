#!/usr/bin/env python
"""
TRACE MATCHING: Step through condition matching to find the bug
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Rule, Transaction, BankStatement
from analyzer.rules_engine import RulesEngine

print("\n" + "="*100)
print("TRACING: Why transactions don't match ANY rules")
print("="*100 + "\n")

user = User.objects.filter(is_superuser=False).first()
if not user:
    print("❌ No test user")
    exit(1)

# Get a simple rule
rule = Rule.objects.filter(user=user, is_active=True, conditions__isnull=False).first()
if not rule:
    print("❌ No rules with conditions")
    exit(1)

print(f"Testing Rule: {rule.name} (ID {rule.id})")
print(f"Rule Type: {rule.rule_type}")
print(f"Conditions: {rule.conditions.count()}\n")

for i, cond in enumerate(rule.conditions.all(), 1):
    print(f"Condition {i}: {cond.condition_type}")
    if cond.condition_type == 'KEYWORD':
        print(f"  Keyword: '{cond.keyword}'")
        print(f"  Match Type: {cond.keyword_match_type}")

# Get a transaction
tx = Transaction.objects.filter(statement__account__user=user).first()
if not tx:
    print("\n❌ No transactions")
    exit(1)

print(f"\nTesting Transaction ID {tx.id}:")
print(f"  Date: {tx.date}")
print(f"  Description: {tx.description[:80]}")
print(f"  Amount: {tx.amount}")

tx_data = {
    'date': tx.date,
    'description': tx.description,
    'amount': float(tx.amount),
    'transaction_type': tx.transaction_type
}

# Now step through matching
engine = RulesEngine(user)

print(f"\n" + "="*100)
print("STEP-BY-STEP MATCHING")
print("="*100)

print(f"\n1. Does rule have conditions?")
conditions = rule.conditions.all()
print(f"   Conditions.exists() = {conditions.exists()}")

if not conditions.exists():
    print(f"   ❌ No conditions, rule will return False immediately")
else:
    print(f"   ✅ Has {conditions.count()} conditions")
    
    print(f"\n2. Rule type = {rule.rule_type}")
    
    if rule.rule_type == 'AND':
        print(f"   Using AND logic: ALL conditions must match\n")
        all_match = True
        for i, cond in enumerate(conditions, 1):
            match = engine._matches_condition(tx_data, cond)
            print(f"   Condition {i} ({cond.condition_type}): {match}")
            if not match:
                all_match = False
                print(f"      Description used: '{tx_data['description'][:80]}'")
                if cond.condition_type == 'KEYWORD':
                    print(f"      Looking for keyword: '{cond.keyword}'")
                    print(f"      Match type: {cond.keyword_match_type}")
                    print(f"      Lowercase description: '{tx_data['description'].lower()[:80]}'")
                    print(f"      Lowercase keyword: '{cond.keyword.lower()}'")
                    
                    desc = tx_data['description'].lower()
                    kw = cond.keyword.lower()
                    if cond.keyword_match_type == 'CONTAINS':
                        print(f"      '{kw}' in description? {kw in desc}")
        
        print(f"\n   Overall AND result: {all_match}")
        
    else:  # OR
        print(f"   Using OR logic: ANY condition matches\n")
        any_match = False
        for i, cond in enumerate(conditions, 1):
            match = engine._matches_condition(tx_data, cond)
            print(f"   Condition {i} ({cond.condition_type}): {match}")
            if match:
                any_match = True
        
        print(f"\n   Overall OR result: {any_match}")

# Test the actual rule matching
print(f"\n" + "="*100)
print("FINAL TEST")
print("="*100)

result = engine._matches_rule(tx_data, rule)
print(f"\nRule '{rule.name}' matches transaction {tx.id}? {result}")

if not result:
    print("\n❌ Rule does NOT match!")
    print("\nPossible causes:")
    print("  1. Description doesn't contain keyword")
    print("  2. Amount is outside range")
    print("  3. Date is outside range")
    print("  4. AND logic but not all conditions match")
    print("  5. Conditions not properly saved to database")

# Try to find a transaction that DOES match this rule
print(f"\n" + "="*100)
print("SEARCHING FOR MATCHING TRANSACTION")
print("="*100)

user_transactions = Transaction.objects.filter(
    statement__account__user=user
)[:20]

found_match = False
for i, test_tx in enumerate(user_transactions):
    test_data = {
        'date': test_tx.date,
        'description': test_tx.description,
        'amount': float(test_tx.amount),
        'transaction_type': test_tx.transaction_type
    }
    
    if engine._matches_rule(test_data, rule):
        print(f"\n✅ Found matching transaction!")
        print(f"   TX ID {test_tx.id}: {test_tx.description[:80]}")
        print(f"   Amount: {test_tx.amount}")
        found_match = True
        break

if not found_match:
    print(f"\n❌ No matching transactions found in first 20 transactions")
    print(f"   This suggests the rule conditions may be too restrictive")
    print(f"   Or no transactions have the required keywords/amounts")
