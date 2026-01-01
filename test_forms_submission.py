#!/usr/bin/env python
"""
Test script to verify that form submissions work correctly
for both Rule creation and Category creation
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
from analyzer.models import Rule, CustomCategory, RuleCondition

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

def test_rule_creation_with_conditions():
    """Test creating a rule with conditions via AJAX"""
    print("\n" + "="*60)
    print("TEST 1: Rule Creation with Conditions")
    print("="*60)
    
    import time
    user = get_or_create_test_user()
    client.login(username='testuser', password='testpass123')
    
    # Prepare form data with unique name
    unique_name = f"Test Rule {int(time.time())}"
    conditions = [
        {
            'type': 'keyword',
            'match_type': 'contains',
            'keyword': 'salary'
        },
        {
            'type': 'amount',
            'operator': 'greater_than',
            'value': 10000
        }
    ]
    
    data = {
        'name': unique_name,
        'category': 'Income',  # Assuming this category exists
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    }
    
    url = reverse('create_rule_ajax')
    print(f"\nPOSTing to: {url}")
    print(f"Data: {data}")
    
    response = client.post(url, data=data)
    result = response.json()
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Data: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        print("✅ Rule creation successful!")
        
        # Verify rule was created
        rule = Rule.objects.get(id=result['rule_id'])
        print(f"  - Rule ID: {rule.id}")
        print(f"  - Rule Name: {rule.name}")
        print(f"  - Conditions Count: {rule.conditions.count()}")
        
        # Verify conditions were created
        for i, condition in enumerate(rule.conditions.all(), 1):
            print(f"    Condition {i}: {condition.condition_type} - {condition.keyword or condition.amount_value or condition.date_start}")
        
        return True
    else:
        print(f"❌ Rule creation failed: {result.get('message')}")
        return False

def test_category_creation_with_conditions():
    """Test creating a category with conditions via AJAX"""
    print("\n" + "="*60)
    print("TEST 2: Category Creation with Conditions")
    print("="*60)
    
    import time
    user = get_or_create_test_user()
    client.login(username='testuser', password='testpass123')
    
    # Prepare form data with unique name
    unique_name = f"Test Category {int(time.time())}"
    conditions = [
        {
            'type': 'amount',
            'operator': 'between',
            'value': 5000,
            'value2': 20000
        }
    ]
    
    data = {
        'name': unique_name,
        'description': 'A test category',
        'icon': '📊',
        'color': '#ff0000',
        'conditions': json.dumps(conditions)
    }
    
    url = reverse('create_category_ajax')
    print(f"\nPOSTing to: {url}")
    print(f"Data: {data}")
    
    response = client.post(url, data=data)
    result = response.json()
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Data: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        print("✅ Category creation successful!")
        
        # Verify category was created
        category = CustomCategory.objects.get(id=result['category_id'])
        print(f"  - Category ID: {category.id}")
        print(f"  - Category Name: {category.name}")
        print(f"  - Category Icon: {category.icon}")
        print(f"  - Category Color: {category.color}")
        
        return True
    else:
        print(f"❌ Category creation failed: {result.get('message')}")
        return False

def test_rule_without_conditions():
    """Test that rule creation fails without conditions"""
    print("\n" + "="*60)
    print("TEST 3: Rule Creation WITHOUT Conditions (Should Fail)")
    print("="*60)
    
    user = get_or_create_test_user()
    client.login(username='testuser', password='testpass123')
    
    data = {
        'name': 'Test Rule Without Conditions',
        'category': 'Income',
        'rule_type': 'AND',
        'conditions': json.dumps([])  # Empty conditions
    }
    
    url = reverse('create_rule_ajax')
    print(f"\nPOSTing to: {url}")
    print(f"Data: {data}")
    
    response = client.post(url, data=data)
    result = response.json()
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Data: {json.dumps(result, indent=2)}")
    
    if not result.get('success'):
        print("✅ Correctly rejected rule without conditions!")
        return True
    else:
        print("❌ Rule without conditions should have been rejected!")
        return False

def test_category_without_name():
    """Test that category creation fails without name"""
    print("\n" + "="*60)
    print("TEST 4: Category Creation WITHOUT Name (Should Fail)")
    print("="*60)
    
    user = get_or_create_test_user()
    client.login(username='testuser', password='testpass123')
    
    data = {
        'name': '',  # Empty name
        'description': 'A test category',
        'icon': '📊',
        'color': '#ff0000'
    }
    
    url = reverse('create_category_ajax')
    print(f"\nPOSTing to: {url}")
    print(f"Data: {data}")
    
    response = client.post(url, data=data)
    result = response.json()
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Data: {json.dumps(result, indent=2)}")
    
    if not result.get('success'):
        print("✅ Correctly rejected category without name!")
        return True
    else:
        print("❌ Category without name should have been rejected!")
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("BankWatch Form Submission Tests")
    print("="*60)
    
    results = []
    
    try:
        # Run tests
        results.append(("Rule with conditions", test_rule_creation_with_conditions()))
        results.append(("Category with conditions", test_category_creation_with_conditions()))
        results.append(("Rule without conditions validation", test_rule_without_conditions()))
        results.append(("Category without name validation", test_category_without_name()))
        
    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    sys.exit(0 if passed == total else 1)
