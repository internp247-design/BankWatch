#!/usr/bin/env python
"""
Test: Verify the bug in rules_application_results view
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from analyzer.models import Rule, CustomCategory
import json

print("\n" + "="*100)
print("BUG TEST: Rules and Categories not showing in apply results page")
print("="*100 + "\n")

user = User.objects.filter(is_superuser=False).first()
if not user:
    print("❌ No test user found")
    exit(1)

# Get statistics
all_rules = Rule.objects.filter(user=user, is_active=True)
all_cats = CustomCategory.objects.filter(user=user, is_active=True)

print(f"Test User: {user.username}")
print(f"Active Rules: {all_rules.count()}")
print(f"Active Categories: {all_cats.count()}\n")

# Test the apply results view
client = Client()
client.force_login(user)

print("-" * 100)
print("TEST: Load apply results page WITHOUT any filters")
print("-" * 100)

# Load the page WITHOUT selected rule_ids or category_ids
response = client.get('/analyzer/rules/apply/results/')

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    # Check if rules are in the response
    content = response.content.decode()
    
    # Count occurrences of rule items
    rule_items = content.count('class="rule-item"')
    cat_items = content.count('class="category-item"')
    
    print(f"\nSidebar Rule Items Found: {rule_items}")
    print(f"Sidebar Category Items Found: {cat_items}")
    
    print(f"\nExpected Rule Items: {all_rules.count()}")
    print(f"Expected Category Items: {all_cats.count()}")
    
    if rule_items == 0 and all_rules.count() > 0:
        print(f"\n❌ BUG CONFIRMED: No rules shown in sidebar!")
        print(f"   - {all_rules.count()} active rules exist")
        print(f"   - But 0 are displayed in the sidebar")
        print(f"   - This is because the view filters rules by selected_rule_ids")
        print(f"   - When no filter is selected, it shows empty queryset")
    elif rule_items == all_rules.count():
        print(f"\n✅ Rules are displayed correctly")
    
    if cat_items == 0 and all_cats.count() > 0:
        print(f"\n❌ BUG CONFIRMED: No categories shown in sidebar!")
        print(f"   - {all_cats.count()} active categories exist")
        print(f"   - But 0 are displayed in the sidebar")
    elif cat_items == all_cats.count():
        print(f"\n✅ Categories are displayed correctly")
else:
    print(f"❌ Failed to load page: {response.status_code}")

# Test with a filter selected
print("\n" + "-" * 100)
print("TEST: Load apply results page WITH rule filters")
print("-" * 100)

if all_rules.count() > 0:
    first_rule = all_rules.first()
    response = client.get(f'/analyzer/rules/apply/results/?rule_ids={first_rule.id}')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode()
        rule_items = content.count('class="rule-item"')
        
        print(f"Rule Items Found: {rule_items}")
        print(f"Expected: 1")
        
        if rule_items == 1:
            print(f"\n✅ With filter selected, rule IS shown")
        else:
            print(f"\n❌ Rule not shown even with filter selected")
else:
    print("⚠️  No rules available to test")

# ROOT CAUSE ANALYSIS
print("\n" + "="*100)
print("ROOT CAUSE ANALYSIS")
print("="*100)

print(f"""
ISSUE LOCATION: analyzer/views.py, lines 726-732

BUGGY CODE:
    if selected_category_ids:
        custom_categories = all_custom_categories.filter(id__in=selected_category_ids)
    else:
        custom_categories = CustomCategory.objects.none()  # ← BUG: Returns empty set!
    
    if selected_rule_ids:
        rules = all_rules.filter(id__in=selected_rule_ids)
    else:
        rules = Rule.objects.none()  # ← BUG: Returns empty set!

PROBLEM:
    When user first loads the page (no filters selected):
    - selected_rule_ids = []  (empty)
    - selected_category_ids = []  (empty)
    - Therefore: rules = CustomCategory.objects.none()
    - Therefore: custom_categories = Rule.objects.none()
    - Result: Sidebar shows "No rules available" and "No custom categories"
    - User cannot see ANY rules or categories to select!

SOLUTION:
    Should always show ALL active rules and categories in the sidebar.
    The filter should only apply to the TRANSACTION TABLE, not the sidebar.
    
    Correct code:
    if selected_category_ids:
        categories_to_display = all_custom_categories.filter(id__in=selected_category_ids)
    else:
        categories_to_display = all_custom_categories  # ← Show all!
    
    if selected_rule_ids:
        rules_to_display = all_rules.filter(id__in=selected_rule_ids)
    else:
        rules_to_display = all_rules  # ← Show all!
""")

print("\n" + "="*100)
