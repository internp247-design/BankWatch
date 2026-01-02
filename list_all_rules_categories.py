#!/usr/bin/env python
"""
List all created rules and categories for the user
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Rule, CustomCategory

user = User.objects.first()
if not user:
    print("ERROR: No users found!")
    sys.exit(1)

print(f"\n{'='*80}")
print(f"RULES & CATEGORIES SUMMARY FOR USER: {user.username}")
print(f"{'='*80}\n")

# Get all rules (both active and inactive)
all_rules = Rule.objects.filter(user=user).order_by('name')
active_rules = all_rules.filter(is_active=True)
inactive_rules = all_rules.filter(is_active=False)

print(f"\n[RULES SUMMARY]")
print(f"-" * 80)
print(f"Total Rules Created: {all_rules.count()}")
print(f"  - Active Rules: {active_rules.count()}")
print(f"  - Inactive Rules: {inactive_rules.count()}")

print(f"\n[ACTIVE RULES] ({active_rules.count()})")
print(f"-" * 80)
for idx, rule in enumerate(active_rules, 1):
    conditions_count = rule.conditions.count()
    print(f"{idx}. {rule.name}")
    print(f"   Category: {rule.get_category_display()}")
    print(f"   Type: {rule.rule_type}")
    print(f"   Conditions: {conditions_count}")
    print()

if inactive_rules.count() > 0:
    print(f"\n[INACTIVE RULES] ({inactive_rules.count()})")
    print(f"-" * 80)
    for idx, rule in enumerate(inactive_rules, 1):
        conditions_count = rule.conditions.count()
        print(f"{idx}. {rule.name}")
        print(f"   Category: {rule.get_category_display()}")
        print(f"   Type: {rule.rule_type}")
        print(f"   Conditions: {conditions_count}")
        print()

# Get all custom categories
all_categories = CustomCategory.objects.filter(user=user).order_by('name')
active_categories = all_categories.filter(is_active=True)
inactive_categories = all_categories.filter(is_active=False)

print(f"\n[CUSTOM CATEGORIES SUMMARY]")
print(f"-" * 80)
print(f"Total Categories Created: {all_categories.count()}")
print(f"  - Active Categories: {active_categories.count()}")
print(f"  - Inactive Categories: {inactive_categories.count()}")

if active_categories.count() > 0:
    print(f"\n[ACTIVE CATEGORIES] ({active_categories.count()})")
    print(f"-" * 80)
    for idx, category in enumerate(active_categories, 1):
        rules_count = category.custom_category_rules.filter(is_active=True).count()
        print(f"{idx}. {category.name} {category.icon}")
        print(f"   Description: {category.description or 'N/A'}")
        print(f"   Color: {category.color}")
        print(f"   Active Rules: {rules_count}")
        print()

if inactive_categories.count() > 0:
    print(f"\n[INACTIVE CATEGORIES] ({inactive_categories.count()})")
    print(f"-" * 80)
    for idx, category in enumerate(inactive_categories, 1):
        rules_count = category.custom_category_rules.filter(is_active=True).count()
        print(f"{idx}. {category.name} {category.icon}")
        print(f"   Description: {category.description or 'N/A'}")
        print(f"   Color: {category.color}")
        print(f"   Active Rules: {rules_count}")
        print()

print(f"\n{'='*80}")
print(f"END OF REPORT")
print(f"{'='*80}\n")
