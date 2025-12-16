#!/usr/bin/env python
"""Debug script to test custom category filtering"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import CustomCategory, CustomCategoryRule, CustomCategoryRuleCondition, Transaction
from django.contrib.auth.models import User
from analyzer.rules_engine import CustomCategoryRulesEngine

# Get the first user
user = User.objects.first()
if not user:
    print("No users found!")
    exit(1)

print(f"\n=== Testing Custom Category Filtering for user: {user.username} ===\n")

# Get all custom categories
categories = CustomCategory.objects.filter(user=user)
print(f"Total custom categories: {categories.count()}")

for category in categories:
    print(f"\n--- Category: {category.name} (ID: {category.id}) ---")
    
    # Get rules for this category
    rules = CustomCategoryRule.objects.filter(custom_category=category)
    print(f"  Total rules: {rules.count()}")
    
    active_rules = rules.filter(is_active=True)
    print(f"  Active rules: {active_rules.count()}")
    
    for rule in active_rules:
        conditions = CustomCategoryRuleCondition.objects.filter(rule=rule)
        print(f"\n    Rule: {rule.name} (ID: {rule.id}, Type: {rule.rule_type})")
        print(f"      Conditions: {conditions.count()}")
        
        for cond in conditions:
            print(f"        - Type: {cond.condition_type}")
            if cond.condition_type == 'KEYWORD':
                print(f"          Keyword: '{cond.keyword}' ({cond.keyword_match_type})")
            elif cond.condition_type == 'AMOUNT':
                print(f"          Amount: {cond.amount_operator} {cond.amount_value}")
                if cond.amount_value2:
                    print(f"          To: {cond.amount_value2}")
            elif cond.condition_type == 'DATE':
                print(f"          Date: {cond.date_start} to {cond.date_end}")
        
        # Test matching against transactions
        test_transactions = Transaction.objects.filter(
            statement__account__user=user
        )[:5]
        
        print(f"\n      Testing against {test_transactions.count()} sample transactions:")
        for tx in test_transactions:
            tx_data = {
                'description': tx.description,
                'amount': float(tx.amount),
                'date': tx.date
            }
            
            matches = CustomCategoryRulesEngine._matches_rule_static(tx_data, rule)
            status = "✓ MATCH" if matches else "✗ NO MATCH"
            print(f"        {status}: {tx.description[:50]}... (${tx.amount})")

print("\n=== End of debug output ===\n")
