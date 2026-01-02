#!/usr/bin/env python
"""
Test script to verify rule creation functionality
Tests the create_rule_ajax endpoint with various condition types
"""

import os
import django
import json
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.test import Client, TestCase
from django.contrib.auth.models import User
from analyzer.models import Rule, RuleCondition

def test_rule_creation():
    """Test basic rule creation with different condition types"""
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'password': 'testpass123'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Clean up previous test rules
    Rule.objects.filter(user=user).delete()
    
    client = Client()
    client.login(username='testuser', password='testpass123')
    
    print("=" * 60)
    print("TESTING RULE CREATION WITH VARIOUS CONDITIONS")
    print("=" * 60)
    
    # Test 1: Rule with keyword condition
    print("\n1. Testing Rule with Keyword Condition...")
    conditions = [
        {
            'type': 'keyword',
            'match': 'contains',
            'value': 'Amazon'
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Amazon Shopping',
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data}")
    
    if data.get('success'):
        print("   ✓ PASSED: Keyword condition rule created successfully")
        rule1_id = data['rule_id']
    else:
        print(f"   ✗ FAILED: {data.get('message')}")
        return False
    
    # Test 2: Rule with amount condition
    print("\n2. Testing Rule with Amount Condition...")
    conditions = [
        {
            'type': 'amount',
            'operator': 'greater_than',
            'value': 1000
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'High Value Transfers',
        'category': 'TRANSPORT',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data}")
    
    if data.get('success'):
        print("   ✓ PASSED: Amount condition rule created successfully")
        rule2_id = data['rule_id']
    else:
        print(f"   ✗ FAILED: {data.get('message')}")
        return False
    
    # Test 3: Rule with BETWEEN amount condition
    print("\n3. Testing Rule with BETWEEN Amount Condition...")
    conditions = [
        {
            'type': 'amount',
            'operator': 'between',
            'value': 500,
            'value2': 2000
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Medium Purchases',
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data}")
    
    if data.get('success'):
        print("   ✓ PASSED: BETWEEN amount condition rule created successfully")
        rule3_id = data['rule_id']
    else:
        print(f"   ✗ FAILED: {data.get('message')}")
        return False
    
    # Test 4: Rule with date condition
    print("\n4. Testing Rule with Date Condition...")
    conditions = [
        {
            'type': 'date',
            'from': '2024-01-01',
            'to': '2024-12-31'
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Year 2024 Transactions',
        'category': 'TRAVEL',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data}")
    
    if data.get('success'):
        print("   ✓ PASSED: Date condition rule created successfully")
        rule4_id = data['rule_id']
    else:
        print(f"   ✗ FAILED: {data.get('message')}")
        return False
    
    # Test 5: Rule with source condition
    print("\n5. Testing Rule with Source Condition...")
    conditions = [
        {
            'type': 'source',
            'source': 'UPI'
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'UPI Transfers',
        'category': 'TRANSPORT',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data}")
    
    if data.get('success'):
        print("   ✓ PASSED: Source condition rule created successfully")
        rule5_id = data['rule_id']
    else:
        print(f"   ✗ FAILED: {data.get('message')}")
        return False
    
    # Test 6: Rule with multiple conditions (OR logic)
    print("\n6. Testing Rule with Multiple Conditions (OR Logic)...")
    conditions = [
        {
            'type': 'keyword',
            'match': 'contains',
            'value': 'Paytm'
        },
        {
            'type': 'keyword',
            'match': 'contains',
            'value': 'PhonePe'
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Wallet Payments',
        'category': 'OTHER',
        'rule_type': 'OR',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data}")
    
    if data.get('success'):
        print("   ✓ PASSED: Multiple conditions rule created successfully")
        rule6_id = data['rule_id']
    else:
        print(f"   ✗ FAILED: {data.get('message')}")
        return False
    
    # Test 7: Validation - Missing rule name
    print("\n7. Testing Validation - Missing Rule Name...")
    conditions = [
        {
            'type': 'keyword',
            'match': 'contains',
            'value': 'Test'
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': '',  # Empty name
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data}")
    
    if not data.get('success') and 'name' in data.get('message', '').lower():
        print("   ✓ PASSED: Validation error caught correctly")
    else:
        print("   ✗ FAILED: Should have caught missing name validation")
        return False
    
    # Test 8: Validation - Missing conditions
    print("\n8. Testing Validation - Missing Conditions...")
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Test Rule',
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps([])  # Empty conditions
    })
    
    data = json.loads(response.content)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data}")
    
    if not data.get('success') and 'condition' in data.get('message', '').lower():
        print("   ✓ PASSED: Validation error caught correctly")
    else:
        print("   ✗ FAILED: Should have caught missing conditions validation")
        return False
    
    # Test 9: Validation - Invalid between amounts
    print("\n9. Testing Validation - Invalid BETWEEN Amount Range...")
    conditions = [
        {
            'type': 'amount',
            'operator': 'between',
            'value': 2000,  # Greater than value2
            'value2': 500   # Less than value
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Invalid Range',
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data}")
    
    if not data.get('success') and 'less than' in data.get('message', '').lower():
        print("   ✓ PASSED: Invalid range validation caught correctly")
    else:
        print("   ✗ FAILED: Should have caught invalid range validation")
        return False
    
    # Verify rules in database
    print("\n" + "=" * 60)
    print("VERIFYING RULES IN DATABASE")
    print("=" * 60)
    
    rules = Rule.objects.filter(user=user)
    print(f"\nTotal rules created: {rules.count()}")
    
    for rule in rules:
        print(f"\n  Rule: {rule.name} → {rule.get_category_display()}")
        print(f"  Type: {rule.rule_type} (AND/OR logic)")
        print(f"  Conditions: {rule.conditions.count()}")
        
        for condition in rule.conditions.all():
            cond_type = condition.condition_type
            if cond_type == 'KEYWORD':
                print(f"    - KEYWORD: '{condition.keyword}' ({condition.keyword_match_type})")
            elif cond_type == 'AMOUNT':
                if condition.amount_value2:
                    print(f"    - AMOUNT: Between ₹{condition.amount_value} and ₹{condition.amount_value2}")
                else:
                    print(f"    - AMOUNT: {condition.amount_operator} ₹{condition.amount_value}")
            elif cond_type == 'DATE':
                print(f"    - DATE: {condition.date_start} to {condition.date_end}")
            elif cond_type == 'SOURCE':
                print(f"    - SOURCE: {condition.source_channel}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY ✓")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        test_rule_creation()
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
