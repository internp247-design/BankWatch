#!/usr/bin/env python
"""
Test script to verify rule editing functionality
"""
import os
import sys
import django
import json

# Setup Django FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

# Now import Django-dependent modules
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from analyzer.models import Rule, RuleCondition

# Test client
client = Client()

def get_or_create_test_user():
    """Get or create a test user"""
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    return user

def test_rule_edit():
    """Test editing an existing rule"""
    print("\n" + "="*60)
    print("TEST: Rule Editing")
    print("="*60)
    
    import time
    user = get_or_create_test_user()
    client.login(username='testuser', password='testpass123')
    
    # First create a rule
    print("\n1. Creating initial rule...")
    conditions = [
        {
            'type': 'keyword',
            'match_type': 'contains',
            'keyword': 'salary'
        }
    ]
    
    create_data = {
        'name': f'Test Edit Rule {int(time.time())}',
        'category': 'Income',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    }
    
    url = reverse('create_rule_ajax')
    response = client.post(url, data=create_data)
    result = response.json()
    
    if not result.get('success'):
        print(f"❌ Failed to create initial rule: {result.get('message')}")
        return False
    
    rule_id = result['rule_id']
    print(f"✅ Created rule with ID: {rule_id}")
    
    # Now edit the rule
    print("\n2. Editing the rule...")
    new_conditions = [
        {
            'type': 'amount',
            'operator': 'greater_than',
            'value': 50000
        },
        {
            'type': 'keyword',
            'match_type': 'contains',
            'keyword': 'bonus'
        }
    ]
    
    edit_data = {
        'name': f'Updated Rule {int(time.time())}',
        'category': 'INVESTMENT',
        'rule_type': 'OR',
        'conditions': json.dumps(new_conditions)
    }
    
    url = reverse('edit_rule_ajax', kwargs={'rule_id': rule_id})
    print(f"PATCHing to: {url}")
    response = client.post(url, data=edit_data)
    result = response.json()
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Data: {json.dumps(result, indent=2)}")
    
    if not result.get('success'):
        print(f"❌ Failed to edit rule: {result.get('message')}")
        return False
    
    print("✅ Rule edited successfully!")
    
    # Verify changes in database
    print("\n3. Verifying changes...")
    rule = Rule.objects.get(id=rule_id)
    print(f"  - Rule Name: {rule.name}")
    print(f"  - Category: {rule.category}")
    print(f"  - Rule Type: {rule.rule_type}")
    print(f"  - Conditions Count: {rule.conditions.count()}")
    
    # Verify conditions were updated
    if rule.conditions.count() != 2:
        print(f"❌ Expected 2 conditions, got {rule.conditions.count()}")
        return False
    
    amount_cond = rule.conditions.filter(condition_type='AMOUNT').first()
    keyword_cond = rule.conditions.filter(condition_type='KEYWORD').first()
    
    if not amount_cond or not keyword_cond:
        print("❌ Missing expected condition types")
        return False
    
    print(f"  - Condition 1: AMOUNT - {amount_cond.amount_value}")
    print(f"  - Condition 2: KEYWORD - {keyword_cond.keyword}")
    
    return True

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Rule Editing Feature Test")
    print("="*60)
    
    try:
        result = test_rule_edit()
        
        print("\n" + "="*60)
        print("TEST RESULT")
        print("="*60)
        if result:
            print("✅ PASS: Rule editing works correctly!")
        else:
            print("❌ FAIL: Rule editing has issues")
        
    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0)
