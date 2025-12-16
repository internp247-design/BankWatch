#!/usr/bin/env python
"""Check all custom categories in database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import CustomCategory, CustomCategoryRule, CustomCategoryRuleCondition
from django.contrib.auth.models import User

print("\n=== All Custom Categories in Database ===\n")

total_cats = CustomCategory.objects.count()
print(f"Total custom categories: {total_cats}")

if total_cats == 0:
    print("No custom categories found!")
    
    # Check if there are any rules
    total_rules = CustomCategoryRule.objects.count()
    print(f"Total custom category rules: {total_rules}")
    
    # List all users and their categories
    print("\n--- By User ---")
    for user in User.objects.all():
        cats = CustomCategory.objects.filter(user=user)
        print(f"User '{user.username}': {cats.count()} categories")
else:
    for cat in CustomCategory.objects.all():
        print(f"\nCategory: {cat.name}")
        print(f"  User: {cat.user.username}")
        print(f"  Active: {cat.is_active}")
        
        rules = cat.rules.all()
        print(f"  Rules: {rules.count()}")
        
        for rule in rules:
            conditions = rule.conditions.all()
            print(f"    Rule: {rule.name} (Active: {rule.is_active}, Conditions: {conditions.count()})")
            for cond in conditions:
                print(f"      - {cond.condition_type}")

print("\n=== End ===\n")
