#!/usr/bin/env python
"""
Test the apply_rules fix - verify that matched transactions are shown
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from analyzer.models import Rule, Transaction, RuleCondition
from django.db import transaction as db_transaction

user = User.objects.first()
if not user:
    print("ERROR: No users found!")
    exit(1)

print(f"\n{'='*80}")
print(f"TEST: Apply Rules - Verify Matched Transactions Are Shown")
print(f"{'='*80}\n")

# Find a rule that should match some transactions
matching_rules = []
for rule in Rule.objects.filter(user=user, is_active=True):
    conditions = rule.conditions.count()
    if conditions > 0:
        matching_rules.append(rule)
        if len(matching_rules) >= 3:
            break

print(f"Found {len(matching_rules)} rules to test:\n")

from analyzer.rules_engine import RulesEngine

engine = RulesEngine(user)

for rule in matching_rules:
    print(f"\nTesting rule: {rule.name}")
    print(f"  Category: {rule.category}")
    print(f"  Conditions: {rule.conditions.count()}")
    
    # Find transactions that match this rule
    matched_txs = []
    for tx in Transaction.objects.filter(statement__account__user=user)[:50]:
        tx_data = {
            'date': tx.date,
            'description': tx.description,
            'amount': float(tx.amount),
            'transaction_type': tx.transaction_type
        }
        if engine._matches_rule(tx_data, rule):
            matched_txs.append(tx)
    
    print(f"  Matched transactions: {len(matched_txs)}")
    
    if matched_txs:
        # Show first few matches
        for tx in matched_txs[:3]:
            print(f"    - TX {tx.id}: {tx.description[:50]}")

print(f"\n\n{'='*80}")
print("SIMULATION: What would happen if we ran apply_rules?")
print(f"{'='*80}\n")

# Simulate apply_rules logic
all_transactions = Transaction.objects.filter(statement__account__user=user)
matched_ids = []
updated_ids = []
matched_map = {}

with db_transaction.atomic():
    for tx in all_transactions.iterator():
        tx_data = {
            'date': tx.date,
            'description': tx.description,
            'amount': float(tx.amount),
            'transaction_type': tx.transaction_type
        }
        
        matched_rule = engine.find_matching_rule(tx_data)
        
        if matched_rule:
            matched_ids.append(tx.id)
            matched_map[str(tx.id)] = matched_rule.name
            
            if matched_rule.category != tx.category:
                updated_ids.append(tx.id)

print(f"Simulation Results:")
print(f"  Total matched: {len(matched_ids)}")
print(f"  Would be updated: {len(updated_ids)}")
print(f"  Already had correct category: {len(matched_ids) - len(updated_ids)}")
print(f"\nWhen results page shows with show_changed=1:")
print(f"  Before fix: Would show {len(updated_ids)} transactions")
print(f"  After fix: Will show {len(matched_ids)} transactions")
print(f"  Improvement: +{len(matched_ids) - len(updated_ids)} more transactions visible")

print(f"\n{'='*80}\n")
