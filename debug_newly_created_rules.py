#!/usr/bin/env python
"""
Debug script to check if newly created rules are present and working correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Rule, RuleCondition, Transaction, CustomCategory, BankAccount, BankStatement
from analyzer.rules_engine import RulesEngine
from datetime import date

# Get the test user
user = User.objects.first()
if not user:
    print("ERROR: No users in database!")
    exit(1)

print(f"\n{'='*60}")
print(f"DEBUG: Checking newly created rules for user: {user.username}")
print(f"{'='*60}\n")

# 1. Check if there are any rules at all
all_rules = Rule.objects.filter(user=user, is_active=True)
print(f"Total active rules for {user.username}: {all_rules.count()}")

if all_rules.count() == 0:
    print("  No rules found!")
else:
    print("\nAll rules:")
    for rule in all_rules.order_by('-created_at'):
        created_at = rule.created_at if hasattr(rule, 'created_at') else 'Unknown'
        print(f"  - ID:{rule.id} | Name:{rule.name} | Category:{rule.category} | Created:{created_at}")
        
        # Check conditions
        conditions = rule.conditions.all()
        print(f"    Conditions: {conditions.count()}")
        for cond in conditions:
            print(f"      - {cond.condition_type}: keyword={cond.keyword}, amount_op={cond.amount_operator}, source={cond.source_channel}")

# 2. Test RulesEngine
print(f"\n\n{'='*60}")
print("Testing RulesEngine...")
print(f"{'='*60}\n")

engine = RulesEngine(user)
print(f"RulesEngine initialized with {engine.rules.count()} rules")

# 3. Get a sample transaction
transactions = Transaction.objects.filter(statement__account__user=user).order_by('id')
if transactions.exists():
    tx = transactions.first()
    print(f"\nTesting with sample transaction:")
    print(f"  ID: {tx.id}")
    print(f"  Description: {tx.description}")
    print(f"  Amount: {tx.amount}")
    print(f"  Date: {tx.date}")
    print(f"  Type: {tx.transaction_type}")
    print(f"  Current Category: {tx.category}")
    
    transaction_data = {
        'date': tx.date,
        'description': tx.description,
        'amount': float(tx.amount),
        'transaction_type': tx.transaction_type
    }
    
    matched_rule = engine.find_matching_rule(transaction_data)
    if matched_rule:
        print(f"\n  Matched Rule: {matched_rule.name} -> {matched_rule.category}")
    else:
        print(f"\n  No matching rule found")
else:
    print("\nNo transactions found!")

# 4. Check for newest rule
print(f"\n\n{'='*60}")
print("Checking for newest rule...")
print(f"{'='*60}\n")

newest_rule = all_rules.order_by('-id').first()
if newest_rule:
    print(f"Newest rule (ID:{newest_rule.id}): {newest_rule.name}")
    print(f"  Category: {newest_rule.category}")
    print(f"  Is Active: {newest_rule.is_active}")
    print(f"  Conditions: {newest_rule.conditions.count()}")
    for cond in newest_rule.conditions.all():
        print(f"    - {cond.condition_type}: keyword={cond.keyword}, amount_op={cond.amount_operator}, source={cond.source_channel}")
    
    # Try to match this rule against transactions
    print(f"\n  Testing newest rule against transactions...")
    matched_count = 0
    engine = RulesEngine(user)
    
    for tx in transactions.iterator():
        transaction_data = {
            'date': tx.date,
            'description': tx.description,
            'amount': float(tx.amount),
            'transaction_type': tx.transaction_type
        }
        
        if engine._matches_rule(transaction_data, newest_rule):
            matched_count += 1
            if matched_count <= 5:  # Show first 5
                print(f"    [MATCH] Matched: {tx.description} ({tx.amount})")
    
    if matched_count > 5:
        print(f"    ... and {matched_count - 5} more transactions")
    print(f"\n  Total matched: {matched_count} transactions")

print(f"\n{'='*60}")
print("Debug complete!")
print(f"{'='*60}\n")
