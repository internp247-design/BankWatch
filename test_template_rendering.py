#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client

user = User.objects.filter(is_superuser=False).first()
client = Client()
client.force_login(user)

# Test 1: Initial page load (NO filters)
print("\n" + "="*100)
print("TEST: Initial page load (NO filters)")
print("="*100)

response = client.get('/analyzer/rules/apply/results/')
print(f"Status: {response.status_code}")

content = response.content.decode()
if 'id="resultsTable"' in content:
    print("[PASS] Results table found in HTML")
    # Count table rows
    rows = content.count('<tr data-transaction-id=')
    print(f"   Rows in table: {rows}")
else:
    print("[FAIL] Results table NOT found in HTML")

if '<h4>No Transactions Found</h4>' in content:
    print("[FAIL] Page shows 'No Transactions Found' message")
else:
    print("[PASS] Page does NOT show 'No Transactions Found'")

# Test 2: Page load with filter
print("\n" + "="*100)
print("TEST: Page load WITH filter (?rule_ids=1)")
print("="*100)

response = client.get('/analyzer/rules/apply/results/?rule_ids=1')
print(f"Status: {response.status_code}")

content = response.content.decode()
if 'id="resultsTable"' in content:
    print("[PASS] Results table found in HTML")
    # Count table rows
    rows = content.count('<tr data-transaction-id=')
    print(f"   Rows in table: {rows}")
else:
    print("[FAIL] Results table NOT found in HTML")

if '<h4>No Transactions Found</h4>' in content:
    print("[FAIL] Page shows 'No Transactions Found' message")
else:
    print("[PASS] Page does NOT show 'No Transactions Found'")
