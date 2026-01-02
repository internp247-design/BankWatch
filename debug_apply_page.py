#!/usr/bin/env python
"""
DEEP DEBUG: Check actual apply results page behavior
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from analyzer.models import Rule, Transaction, BankStatement, BankAccount
import json

print("\n" + "="*100)
print("TESTING: Apply rules page with real HTTP requests")
print("="*100 + "\n")

user = User.objects.filter(is_superuser=False).first()
if not user:
    print("❌ No test user found")
    exit(1)

# Get user's rules
rules = Rule.objects.filter(user=user, is_active=True).order_by('-created_at')
print(f"User: {user.username}")
print(f"Active Rules: {rules.count()}\n")

if rules.count() < 2:
    print("❌ Need at least 2 rules to test")
    exit(1)

# Get one old rule and one new rule
all_rules_ordered = list(rules)
old_rule = all_rules_ordered[-1]  # Last (oldest)
new_rule = all_rules_ordered[0]   # First (newest)

print(f"Old Rule ID {old_rule.id}: {old_rule.name}")
print(f"  Conditions: {old_rule.conditions.count()}")
print(f"  Created: {old_rule.created_at}")

print(f"\nNew Rule ID {new_rule.id}: {new_rule.name}")
print(f"  Conditions: {new_rule.conditions.count()}")
print(f"  Created: {new_rule.created_at}\n")

# Create a client and login
client = Client()
client.force_login(user)

# Test 1: Old rule
print("="*100)
print(f"TEST 1: Apply OLD RULE (ID {old_rule.id})")
print("="*100)

response = client.get(f'/analyzer/rules/apply/results/?rule_ids={old_rule.id}')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode()
    
    # Check if results found
    if 'No transactions found' in content:
        print("Result: ❌ No transactions found")
    else:
        # Count result rows
        result_count = content.count('<tr>')
        print(f"Result: ✅ Found {result_count} transaction rows")
        
        # Check if rule is shown in sidebar
        if f'data-rule-id="{old_rule.id}"' in content:
            print(f"Sidebar: ✅ Rule appears in sidebar")
        else:
            print(f"Sidebar: ❌ Rule NOT in sidebar")
else:
    print(f"Error: {response.status_code}")

# Test 2: New rule
print("\n" + "="*100)
print(f"TEST 2: Apply NEW RULE (ID {new_rule.id})")
print("="*100)

response = client.get(f'/analyzer/rules/apply/results/?rule_ids={new_rule.id}')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode()
    
    # Check if results found
    if 'No transactions found' in content:
        print("Result: ❌ No transactions found")
    else:
        # Count result rows
        result_count = content.count('<tr>')
        print(f"Result: ✅ Found {result_count} transaction rows")
        
        # Check if rule is shown in sidebar
        if f'data-rule-id="{new_rule.id}"' in content:
            print(f"Sidebar: ✅ Rule appears in sidebar")
        else:
            print(f"Sidebar: ❌ Rule NOT in sidebar")
else:
    print(f"Error: {response.status_code}")

# Test 3: Check if transactions even exist
print("\n" + "="*100)
print("TEST 3: Check Database")
print("="*100)

accounts = BankAccount.objects.filter(user=user)
statements = BankStatement.objects.filter(account__in=accounts)
transactions = Transaction.objects.filter(statement__in=statements)

print(f"\nAccounts: {accounts.count()}")
print(f"Statements: {statements.count()}")
print(f"Transactions: {transactions.count()}\n")

if transactions.count() > 0:
    print("Sample Transactions:")
    for tx in transactions[:3]:
        print(f"  {tx.date}: {tx.description[:50]}")
else:
    print("❌ NO TRANSACTIONS IN DATABASE!")

# Test 4: Check view logic
print("\n" + "="*100)
print("TEST 4: Debug - Check what the view receives")
print("="*100)

# Get first account with transactions
if statements.exists():
    account_id = statements.first().account.id
    
    # Test with account filter
    response = client.get(f'/analyzer/rules/apply/results/?account_id={account_id}&rule_ids={old_rule.id}')
    print(f"\nWith account filter (ID {account_id}):")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode()
        if 'No transactions found' in content:
            print("Result: ❌ No transactions found")
        else:
            print(f"Result: ✅ Found transactions")
else:
    print("No statements/accounts to test with")

print("\n" + "="*100)
