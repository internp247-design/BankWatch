#!/usr/bin/env python
"""
Debug script to check rules and categories application logic
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import (
    Rule, RuleCondition, CustomCategory, CustomCategoryRule, 
    CustomCategoryRuleCondition, Transaction, BankAccount, BankStatement
)
from analyzer.rules_engine import RulesEngine, CustomCategoryRulesEngine
from datetime import datetime, date

def debug_rules_application():
    """Debug rules application"""
    
    print("=" * 70)
    print("DEBUGGING RULES & CATEGORIES APPLICATION")
    print("=" * 70)
    
    # Get a test user
    user = User.objects.filter(is_superuser=False).first()
    if not user:
        print("No test user found")
        return
    
    print(f"\nTest User: {user.username}")
    
    # Check rules
    print("\n" + "=" * 70)
    print("CHECKING RULES")
    print("=" * 70)
    
    rules = Rule.objects.filter(user=user)
    print(f"\nTotal Rules for user: {rules.count()}")
    
    for rule in rules[:3]:  # Show first 3 rules
        print(f"\n  Rule: {rule.name} (ID: {rule.id})")
        print(f"    Category: {rule.category}")
        print(f"    Type: {rule.rule_type}")
        print(f"    Active: {rule.is_active}")
        
        conditions = rule.conditions.all()
        print(f"    Conditions: {conditions.count()}")
        for cond in conditions:
            print(f"      - {cond.condition_type}: {cond.keyword or cond.amount_value or cond.date_from} ({cond.keyword_match_type or cond.amount_operator or 'N/A'})")
    
    # Check custom categories
    print("\n" + "=" * 70)
    print("CHECKING CUSTOM CATEGORIES")
    print("=" * 70)
    
    categories = CustomCategory.objects.filter(user=user)
    print(f"\nTotal Custom Categories for user: {categories.count()}")
    
    for cat in categories[:3]:  # Show first 3
        print(f"\n  Category: {cat.name} (ID: {cat.id})")
        print(f"    Color: {cat.color}")
        print(f"    Icon: {cat.icon}")
        
        rules = CustomCategoryRule.objects.filter(custom_category=cat)
        print(f"    Rules: {rules.count()}")
        for rule in rules[:2]:
            print(f"      Rule: {rule.name} (ID: {rule.id})")
            print(f"        Type: {rule.rule_type}")
            print(f"        Active: {rule.is_active}")
            
            conditions = rule.conditions.all()
            print(f"        Conditions: {conditions.count()}")
            for cond in conditions[:1]:
                print(f"          - {cond.condition_type}")
    
    # Test a transaction against rules
    print("\n" + "=" * 70)
    print("TESTING RULE APPLICATION")
    print("=" * 70)
    
    # Get a sample transaction
    tx = Transaction.objects.filter(statement__account__user=user).first()
    if tx:
        print(f"\nTest Transaction:")
        print(f"  Description: {tx.description}")
        print(f"  Amount: ₹{tx.amount}")
        print(f"  Date: {tx.date}")
        print(f"  Type: {tx.transaction_type}")
        
        # Apply rules
        engine = RulesEngine(user)
        tx_data = {
            'date': tx.date,
            'description': tx.description,
            'amount': float(tx.amount),
            'transaction_type': tx.transaction_type
        }
        
        matched_rule = engine.find_matching_rule(tx_data)
        print(f"\n  Matched Rule: {matched_rule.name if matched_rule else 'None'}")
        
        if matched_rule:
            print(f"    Category: {matched_rule.category}")
            
            # Show which conditions matched
            print(f"    Matching conditions:")
            for cond in matched_rule.conditions.all():
                matches = engine._matches_condition(tx_data, cond)
                print(f"      - {cond.condition_type}: {matches}")
    
    # Test custom category rules
    print("\n" + "=" * 70)
    print("TESTING CUSTOM CATEGORY RULE APPLICATION")
    print("=" * 70)
    
    if tx:
        cat_engine = CustomCategoryRulesEngine(user)
        matched_cat_rule = cat_engine.find_matching_rule(tx_data)
        print(f"\nTransaction: {tx.description}")
        print(f"  Matched Category Rule: {matched_cat_rule.name if matched_cat_rule else 'None'}")
        if matched_cat_rule:
            print(f"    Category: {matched_cat_rule.custom_category.name}")
    
    # Check if any transactions have been categorized
    print("\n" + "=" * 70)
    print("TRANSACTION CATEGORIZATION STATUS")
    print("=" * 70)
    
    all_txs = Transaction.objects.filter(statement__account__user=user)
    print(f"\nTotal Transactions: {all_txs.count()}")
    
    categorized = all_txs.exclude(category__isnull=True).count()
    print(f"Categorized: {categorized}")
    print(f"Uncategorized: {all_txs.count() - categorized}")
    
    # Show category distribution
    print(f"\nCategory Distribution:")
    from django.db.models import Count
    distribution = all_txs.values('category__name').annotate(count=Count('id')).order_by('-count')
    for item in distribution[:10]:
        print(f"  {item['category__name']}: {item['count']}")

if __name__ == '__main__':
    try:
        debug_rules_application()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
