#!/usr/bin/env python
"""
Test script to check if rule filtering works via HTTP
"""
import os
import sys
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from analyzer.models import Rule

# Get the test user
user = User.objects.first()
if not user:
    print("ERROR: No users in database!")
    exit(1)

print(f"\n{'='*70}")
print(f"Testing rule application results page")
print(f"{'='*70}\n")

# Get a couple of recently created rules
rules = Rule.objects.filter(user=user, is_active=True).order_by('-id')[:2]
print(f"Found {rules.count()} rules for testing")
for rule in rules:
    print(f"  - ID:{rule.id} | Name:{rule.name}")

if rules.count() < 1:
    print("ERROR: Need at least 1 rule to test!")
    exit(1)

# Create a test client
client = Client()

# Log in as the user
client.login(username=user.username, password='password')  # Assuming default password

# Test 1: Get the page without filters
print(f"\n\nTest 1: Get page without filters")
print("-" * 70)
response = client.get('/analyzer/rules/apply/results/', follow=True)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.content)} bytes")

# Test 2: Get the page with a rule filter
rule_id = rules.first().id
print(f"\n\nTest 2: Get page with rule_ids filter (rule_id={rule_id})")
print("-" * 70)
response = client.get(f'/analyzer/rules/apply/results/?rule_ids={rule_id}', follow=True)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.content)} bytes")

if 'No transactions found' in response.content.decode('utf-8', errors='ignore'):
    print("WARNING: Response contains 'No transactions found'")

print(f"\n{'='*70}")
print("Test complete!")
print(f"{'='*70}\n")
