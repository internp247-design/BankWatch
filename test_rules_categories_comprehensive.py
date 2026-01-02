#!/usr/bin/env python
"""
Comprehensive test of custom rules and categories application
"""
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Rule, RuleCondition, CustomCategory, CustomCategoryRule, Transaction
from analyzer.rules_engine import RulesEngine, CustomCategoryRulesEngine
from decimal import Decimal

user = User.objects.first()
if not user:
    print("ERROR: No users found!")
    sys.exit(1)

print(f"\n{'='*80}")
print(f"COMPREHENSIVE TEST: Custom Rules & Categories Application")
print(f"{'='*80}\n")

# Test 1: Check if rules exist and are being loaded
print("TEST 1: Rules Loading")
print("-" * 80)
all_rules = Rule.objects.filter(user=user, is_active=True)
print(f"Total active rules: {all_rules.count()}")

engine = RulesEngine(user)
print(f"RulesEngine loaded rules: {engine.rules.count()}")

if engine.rules.count() != all_rules.count():
    print(f"WARNING: Mismatch between DB rules ({all_rules.count()}) and engine rules ({engine.rules.count()})")
else:
    print("[OK] Rule counts match")

# Test 2: Check if any custom categories exist
print(f"\n\nTEST 2: Custom Categories")
print("-" * 80)
all_categories = CustomCategory.objects.filter(user=user, is_active=True)
print(f"Total active categories: {all_categories.count()}")

category_engine = CustomCategoryRulesEngine(user)
print(f"CustomCategoryRulesEngine loaded: {category_engine.rules.count()} category rules")

# Test 3: Test transaction matching with each rule
print(f"\n\nTEST 3: Rule Matching on Sample Transactions")
print("-" * 80)

transactions = Transaction.objects.filter(statement__account__user=user).order_by('-id')[:10]
print(f"Testing {transactions.count()} transactions\n")

total_matches = 0
for tx in transactions:
    tx_data = {
        'date': tx.date,
        'description': tx.description,
        'amount': float(tx.amount),
        'transaction_type': tx.transaction_type
    }
    
    matched_rule = engine.find_matching_rule(tx_data)
    matched_category = category_engine.apply_rules_to_transaction(tx_data)
    
    if matched_rule or matched_category:
        total_matches += 1
        match_info = []
        if matched_rule:
            match_info.append(f"Rule: {matched_rule.name}")
        if matched_category:
            match_info.append(f"Category: {matched_category.name}")
        
        print(f"  TX {tx.id}: {' | '.join(match_info)}")
        print(f"    Desc: {tx.description[:60]}")

print(f"\nTotal matches: {total_matches}/{transactions.count()}")

# Test 4: Test the apply_rules logic
print(f"\n\nTEST 4: Simulate Apply Rules Logic")
print("-" * 80)

all_transactions = Transaction.objects.filter(statement__account__user=user)
print(f"Processing {all_transactions.count()} transactions...")

matched_count = 0
updated_count = 0
already_categorized = 0

for tx in all_transactions.iterator():
    tx_data = {
        'date': tx.date,
        'description': tx.description,
        'amount': float(tx.amount),
        'transaction_type': tx.transaction_type
    }
    
    matched_rule = engine.find_matching_rule(tx_data)
    
    if matched_rule:
        matched_count += 1
        target_category = matched_rule.category
        
        if target_category != tx.category:
            updated_count += 1
        else:
            already_categorized += 1

print(f"  Matched by rules: {matched_count}")
print(f"  Updated category: {updated_count}")
print(f"  Already had correct category: {already_categorized}")
print(f"  No match: {all_transactions.count() - matched_count}")

# Test 5: Check for inactive rules/categories
print(f"\n\nTEST 5: Inactive Rules & Categories")
print("-" * 80)

inactive_rules = Rule.objects.filter(user=user, is_active=False)
inactive_cats = CustomCategory.objects.filter(user=user, is_active=False)

print(f"Inactive rules: {inactive_rules.count()}")
print(f"Inactive categories: {inactive_cats.count()}")

if inactive_rules.count() > 0:
    print("\nInactive rules:")
    for rule in inactive_rules[:5]:
        print(f"  - {rule.name} (ID: {rule.id})")

# Test 6: Check category rule conditions
print(f"\n\nTEST 6: Category Rule Conditions")
print("-" * 80)

for category in all_categories[:3]:
    category_rules = CustomCategoryRule.objects.filter(category=category)
    print(f"\n{category.name}: {category_rules.count()} rules")
    
    for cat_rule in category_rules[:2]:
        conditions = CustomCategoryRuleCondition.objects.filter(rule=cat_rule)
        print(f"  Rule: {cat_rule.name}")
        for cond in conditions:
            print(f"    - {cond.condition_type}: {cond.keyword or cond.source_channel or ''}")

print(f"\n\n{'='*80}")
print("Test Complete!")
print(f"{'='*80}\n")
