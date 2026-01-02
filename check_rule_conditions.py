#!/usr/bin/env python
"""
Check the rules and their conditions to see why they're not matching
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Rule, RuleCondition, Transaction

def check_rules_and_conditions():
    """Check what conditions exist for each rule"""
    
    print("=" * 100)
    print("CHECKING ALL ACTIVE RULES AND THEIR CONDITIONS")
    print("=" * 100)
    
    # Get admin user
    user = User.objects.filter(is_superuser=False).first()
    if not user:
        print("No test user found")
        return
    
    print(f"\nUser: {user.username}\n")
    
    # Get all active rules
    rules = Rule.objects.filter(user=user, is_active=True).order_by('name')
    
    print(f"Total Active Rules: {rules.count()}\n")
    
    for rule in rules:
        print(f"Rule: {rule.name}")
        print(f"  Category: {rule.category}")
        print(f"  Type: {rule.rule_type}")
        print(f"  Active: {rule.is_active}")
        
        conditions = rule.conditions.all()
        print(f"  Conditions: {conditions.count()}")
        
        if conditions.count() == 0:
            print(f"    ⚠️  NO CONDITIONS - This rule won't match anything!")
        
        for cond in conditions:
            print(f"    - Type: {cond.condition_type}")
            if cond.condition_type == 'KEYWORD':
                print(f"      Keyword: {cond.keyword}")
                print(f"      Match Type: {cond.keyword_match_type}")
            elif cond.condition_type == 'AMOUNT':
                print(f"      Min: {cond.amount_min}, Max: {cond.amount_max}")
            elif cond.condition_type == 'DATE':
                print(f"      Start: {cond.date_start}, End: {cond.date_end}")
            elif cond.condition_type == 'SOURCE':
                print(f"      Source: {cond.source}")
        print()

if __name__ == '__main__':
    try:
        check_rules_and_conditions()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
