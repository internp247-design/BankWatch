#!/usr/bin/env python
"""
Activate all inactive rules for better user experience
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Rule

user = User.objects.first()
if not user:
    print("ERROR: No users found!")
    exit(1)

print(f"\n{'='*70}")
print(f"Activating inactive rules for user: {user.username}")
print(f"{'='*70}\n")

inactive_rules = Rule.objects.filter(user=user, is_active=False)
print(f"Found {inactive_rules.count()} inactive rules:\n")

for rule in inactive_rules:
    conditions_count = rule.conditions.count()
    print(f"  - {rule.name} (ID: {rule.id}) - {conditions_count} conditions")
    rule.is_active = True
    rule.save()

print(f"\n✓ Activated {inactive_rules.count()} rules")

# Verify
active_rules = Rule.objects.filter(user=user, is_active=True).count()
print(f"\nTotal active rules now: {active_rules}")

print(f"\n{'='*70}\n")
