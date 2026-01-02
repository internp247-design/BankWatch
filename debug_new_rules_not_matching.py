#!/usr/bin/env python
"""
DEBUG: Why Newly Created Rules Don't Match Any Transactions

This script investigates:
1. Are newly created rules saved correctly?
2. Do they have valid conditions?
3. Why don't they match transactions?
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Rule, RuleCondition, CustomCategory, CustomCategoryRule, CustomCategoryRuleCondition, Transaction, BankStatement
from analyzer.rules_engine import RulesEngine, CustomCategoryRulesEngine
import json
from decimal import Decimal

print("\n" + "="*100)
print("DEBUGGING: Why newly created rules don't match transactions")
print("="*100 + "\n")

# Get test user
user = User.objects.filter(is_superuser=False).first()
if not user:
    print("❌ No test user found")
    exit(1)

print(f"Test User: {user.username}\n")

# Get some test data
all_rules = Rule.objects.filter(user=user, is_active=True)
old_rules = all_rules.order_by('created_at')[:3]  # Get first 3 (old rules)
new_rules = all_rules.order_by('-created_at')[:3]  # Get last 3 (new rules)

print(f"Total Active Rules: {all_rules.count()}")
print(f"Old Rules (first created): {old_rules.count()}")
print(f"New Rules (recently created): {new_rules.count()}\n")

# Get some transactions
statements = BankStatement.objects.filter(account__user=user)
transactions = Transaction.objects.filter(statement__in=statements)[:10]

if not transactions.exists():
    print("❌ No transactions found for testing")
    exit(1)

print(f"Sample Transactions for Testing: {transactions.count()}\n")

# Print all transactions
print("-" * 100)
print("SAMPLE TRANSACTIONS")
print("-" * 100)
for tx in transactions[:5]:
    print(f"  {tx.id}: {tx.date} | {tx.description} | {tx.amount} | {tx.transaction_type}")
print()

# Test 1: Check if rules are saved correctly
print("="*100)
print("TEST 1: Rule Structure - Are rules saved with valid conditions?")
print("="*100)

print("\nOLD RULES (Previously created - these work):")
print("-" * 100)
for rule in old_rules[:2]:
    conditions = rule.conditions.all()
    print(f"\n✅ Rule ID {rule.id}: {rule.name}")
    print(f"   Category: {rule.get_category_display()}")
    print(f"   Rule Type: {rule.rule_type}")
    print(f"   Conditions Count: {conditions.count()}")
    
    if conditions.count() == 0:
        print(f"   ⚠️  WARNING: No conditions defined!")
    else:
        for i, cond in enumerate(conditions, 1):
            print(f"   Condition {i}: {cond.condition_type}")
            if cond.condition_type == 'KEYWORD':
                print(f"      Keyword: '{cond.keyword}'")
                print(f"      Match Type: {cond.keyword_match_type}")
            elif cond.condition_type == 'AMOUNT':
                print(f"      Operator: {cond.amount_operator}")
                print(f"      Value: {cond.amount_value}")
                if cond.amount_operator == 'BETWEEN':
                    print(f"      Value 2: {cond.amount_value2}")
            elif cond.condition_type == 'DATE':
                print(f"      Date Range: {cond.date_start} to {cond.date_end}")
            elif cond.condition_type == 'SOURCE':
                print(f"      Source: {cond.source_channel}")

print("\n" + "-" * 100)
print("NEW RULES (Recently created - these don't work):")
print("-" * 100)
for rule in new_rules[:2]:
    conditions = rule.conditions.all()
    print(f"\n❌ Rule ID {rule.id}: {rule.name}")
    print(f"   Category: {rule.get_category_display()}")
    print(f"   Rule Type: {rule.rule_type}")
    print(f"   Conditions Count: {conditions.count()}")
    
    if conditions.count() == 0:
        print(f"   ⚠️  CRITICAL: No conditions defined!")
    else:
        for i, cond in enumerate(conditions, 1):
            print(f"   Condition {i}: {cond.condition_type}")
            if cond.condition_type == 'KEYWORD':
                print(f"      Keyword: '{cond.keyword}'")
                print(f"      Match Type: {cond.keyword_match_type}")
                if not cond.keyword:
                    print(f"      ⚠️  WARNING: Keyword is EMPTY!")
            elif cond.condition_type == 'AMOUNT':
                print(f"      Operator: {cond.amount_operator}")
                print(f"      Value: {cond.amount_value}")
                if cond.amount_operator == 'BETWEEN':
                    print(f"      Value 2: {cond.amount_value2}")
            elif cond.condition_type == 'DATE':
                print(f"      Date Range: {cond.date_start} to {cond.date_end}")
            elif cond.condition_type == 'SOURCE':
                print(f"      Source: {cond.source_channel}")

# Test 2: Apply rules to sample transactions
print("\n" + "="*100)
print("TEST 2: Rule Matching - Do rules match transactions?")
print("="*100)

engine = RulesEngine(user)

print("\nTesting OLD RULES:")
print("-" * 100)
for rule in old_rules[:2]:
    print(f"\nRule: {rule.name}")
    match_count = 0
    for tx in transactions[:5]:
        tx_data = {
            'description': tx.description,
            'amount': float(tx.amount),
            'date': tx.date,
            'transaction_type': tx.transaction_type
        }
        if engine._matches_rule(tx_data, rule):
            print(f"  ✅ Matches transaction {tx.id}: {tx.description}")
            match_count += 1
        else:
            print(f"  ❌ Does NOT match: {tx.description}")
    print(f"  Summary: {match_count}/{transactions.count()} transactions matched")

print("\n" + "-" * 100)
print("Testing NEW RULES:")
print("-" * 100)
for rule in new_rules[:2]:
    print(f"\nRule: {rule.name}")
    match_count = 0
    for tx in transactions[:5]:
        tx_data = {
            'description': tx.description,
            'amount': float(tx.amount),
            'date': tx.date,
            'transaction_type': tx.transaction_type
        }
        if engine._matches_rule(tx_data, rule):
            print(f"  ✅ Matches transaction {tx.id}: {tx.description}")
            match_count += 1
        else:
            print(f"  ❌ Does NOT match: {tx.description}")
    print(f"  Summary: {match_count}/{transactions.count()} transactions matched")

# Test 3: Check custom categories
print("\n" + "="*100)
print("TEST 3: Custom Categories - Are they saved correctly?")
print("="*100)

all_categories = CustomCategory.objects.filter(user=user, is_active=True)
print(f"\nTotal Active Custom Categories: {all_categories.count()}\n")

for category in all_categories[:3]:
    print(f"\nCategory: {category.name}")
    rules_for_cat = CustomCategoryRule.objects.filter(custom_category=category, is_active=True)
    print(f"  Rules: {rules_for_cat.count()}")
    
    for rule in rules_for_cat[:2]:
        conditions = rule.conditions.all()
        print(f"    Rule: {rule.name}")
        print(f"      Conditions: {conditions.count()}")
        for cond in conditions:
            if cond.condition_type == 'KEYWORD' and cond.keyword:
                print(f"        Keyword: {cond.keyword}")

# Test 4: Direct condition matching
print("\n" + "="*100)
print("TEST 4: Condition-Level Debugging")
print("="*100)

if new_rules.count() > 0:
    test_rule = new_rules.first()
    print(f"\nTesting Rule: {test_rule.name}")
    print(f"Conditions: {test_rule.conditions.count()}")
    
    if test_rule.conditions.count() == 0:
        print("⚠️  CRITICAL: Rule has no conditions!")
    else:
        test_cond = test_rule.conditions.first()
        print(f"\nFirst Condition Details:")
        print(f"  Type: {test_cond.condition_type}")
        print(f"  ID: {test_cond.id}")
        print(f"  Rule FK: {test_cond.rule_id}")
        
        if test_cond.condition_type == 'KEYWORD':
            print(f"  Keyword: '{test_cond.keyword}'")
            print(f"  Match Type: {test_cond.keyword_match_type}")
            print(f"  Length: {len(test_cond.keyword) if test_cond.keyword else 0}")
            
            if not test_cond.keyword:
                print("\n🔴 CRITICAL BUG FOUND:")
                print("   Keyword condition has EMPTY keyword!")
                print("   This will never match any transaction!")

print("\n" + "="*100)
print("CONCLUSION")
print("="*100)
print("""
If new rules don't match transactions but old rules do, check:

1. ✅ Are conditions being saved to database?
   - Check: RuleCondition.objects.filter(rule=new_rule).count()

2. ❌ Do conditions have valid data?
   - Keyword: Not empty
   - Amount: Valid operators and values
   - Date: Valid date ranges
   - Source: Valid source channels

3. ❌ Is the matching logic correct?
   - Check: engine._matches_rule(tx_data, rule)
   - Check each condition individually

4. ❌ Is there a data format mismatch?
   - Frontend sends one format
   - Backend expects another
   - Conditions stored in wrong format

5. ❌ Is there a timing/race condition?
   - Rule created but not immediately queryable
   - Transaction applied before rule fully saved
""")
