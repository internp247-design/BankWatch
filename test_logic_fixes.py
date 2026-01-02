#!/usr/bin/env python
"""
Test script to verify all rule and category edit/create logic fixes
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from analyzer.models import Rule, RuleCondition, CustomCategory

def test_all_logic_fixes():
    """Comprehensive test of all fixed logic"""
    
    # Create test user
    user = User.objects.create_user(username='logictest', password='testpass123')
    
    client = Client()
    client.login(username='logictest', password='testpass123')
    
    print("=" * 70)
    print("TESTING ALL LOGIC FIXES - CREATE & EDIT OPERATIONS")
    print("=" * 70)
    
    # ============================================================
    # TEST 1: Create Rule with Keyword
    # ============================================================
    print("\n✓ TEST 1: Create Rule with Keyword Condition")
    print("-" * 70)
    
    conditions = [
        {
            'type': 'keyword',
            'value': 'Amazon',
            'match': 'contains'
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Amazon Test',
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    rule_id = data['rule_id']
    print(f"  Status: {response.status_code}")
    print(f"  Rule Created: {data['rule_name']} (ID: {rule_id})")
    print(f"  Success: {data['success']}")
    assert data['success'], "Rule creation failed"
    print("  ✅ PASSED\n")
    
    # ============================================================
    # TEST 2: Get Rule (Check Format Standardization)
    # ============================================================
    print("✓ TEST 2: Get Rule - Verify Standardized Format")
    print("-" * 70)
    
    response = client.get(f'/analyzer/api/rule/{rule_id}/get/')
    data = json.loads(response.content)
    
    print(f"  Status: {response.status_code}")
    print(f"  Rule Name: {data['rule_name']}")
    print(f"  Category: {data['category']}")
    print(f"  Conditions Count: {len(data['conditions'])}")
    
    # Check standardized format
    condition = data['conditions'][0]
    print(f"  Condition Type: {condition['type']}")
    print(f"  Condition Value: {condition.get('value')} (standard field)")
    print(f"  Condition Match: {condition.get('match')} (standard field)")
    
    assert condition['type'] == 'keyword', "Wrong type"
    assert 'value' in condition, "Missing standard field 'value'"
    assert 'match' in condition, "Missing standard field 'match'"
    assert condition['value'] == 'Amazon', "Wrong value"
    print("  ✅ FORMAT STANDARDIZED - PASSED\n")
    
    # ============================================================
    # TEST 3: Edit Rule - Update Condition
    # ============================================================
    print("✓ TEST 3: Edit Rule - Update Keyword Condition")
    print("-" * 70)
    
    updated_conditions = [
        {
            'type': 'keyword',
            'value': 'ModifiedAmazon',  # Changed
            'match': 'starts_with'       # Changed
        }
    ]
    
    response = client.post(f'/analyzer/api/rule/{rule_id}/update/', {
        'name': 'Amazon Test Updated',
        'category': 'SHOPPING',
        'rule_type': 'OR',
        'conditions': json.dumps(updated_conditions)
    })
    
    data = json.loads(response.content)
    print(f"  Status: {response.status_code}")
    print(f"  Success: {data['success']}")
    print(f"  Message: {data['message']}")
    assert data['success'], f"Update failed: {data['message']}"
    print("  ✅ PASSED\n")
    
    # ============================================================
    # TEST 4: Verify Edit Applied
    # ============================================================
    print("✓ TEST 4: Verify Edit Applied to Database")
    print("-" * 70)
    
    response = client.get(f'/analyzer/api/rule/{rule_id}/get/')
    data = json.loads(response.content)
    
    condition = data['conditions'][0]
    print(f"  Rule Name After Edit: {data['rule_name']}")
    print(f"  Rule Type After Edit: {data['rule_type']}")
    print(f"  Condition Value After Edit: {condition['value']}")
    print(f"  Condition Match After Edit: {condition['match']}")
    
    assert data['rule_name'] == 'Amazon Test Updated', "Name not updated"
    assert data['rule_type'] == 'OR', "Rule type not updated"
    assert condition['value'] == 'ModifiedAmazon', "Condition value not updated"
    assert condition['match'] == 'starts_with', "Match type not updated"
    print("  ✅ DATABASE CHANGES VERIFIED - PASSED\n")
    
    # ============================================================
    # TEST 5: Create Rule with Amount Condition
    # ============================================================
    print("✓ TEST 5: Create Rule with Amount Condition")
    print("-" * 70)
    
    conditions = [
        {
            'type': 'amount',
            'operator': 'between',
            'value': 500,
            'value2': 2000
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Amount Range Test',
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    amount_rule_id = data['rule_id']
    print(f"  Status: {response.status_code}")
    print(f"  Rule Created: {data['rule_name']} (ID: {amount_rule_id})")
    assert data['success'], "Rule creation failed"
    print("  ✅ PASSED\n")
    
    # ============================================================
    # TEST 6: Get Amount Rule - Format Check
    # ============================================================
    print("✓ TEST 6: Get Amount Rule - Verify Amount Format")
    print("-" * 70)
    
    response = client.get(f'/analyzer/api/rule/{amount_rule_id}/get/')
    data = json.loads(response.content)
    
    condition = data['conditions'][0]
    print(f"  Condition Type: {condition['type']}")
    print(f"  Operator: {condition.get('operator')}")
    print(f"  Value: {condition.get('value')}")
    print(f"  Value2: {condition.get('value2')}")
    
    assert condition['type'] == 'amount', "Wrong type"
    assert condition['operator'] == 'between', "Wrong operator"
    assert condition['value'] == 500, "Wrong value"
    assert condition['value2'] == 2000, "Wrong value2"
    print("  ✅ AMOUNT FORMAT VERIFIED - PASSED\n")
    
    # ============================================================
    # TEST 7: Edit Amount Rule
    # ============================================================
    print("✓ TEST 7: Edit Amount Rule - Change BETWEEN Range")
    print("-" * 70)
    
    updated_conditions = [
        {
            'type': 'amount',
            'operator': 'greater_than',
            'value': 5000
        }
    ]
    
    response = client.post(f'/analyzer/api/rule/{amount_rule_id}/update/', {
        'name': 'Amount Test Updated',
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps(updated_conditions)
    })
    
    data = json.loads(response.content)
    print(f"  Status: {response.status_code}")
    print(f"  Success: {data['success']}")
    assert data['success'], f"Update failed: {data['message']}"
    print("  ✅ PASSED\n")
    
    # ============================================================
    # TEST 8: Validation Error - Invalid BETWEEN
    # ============================================================
    print("✓ TEST 8: Validation - Invalid BETWEEN Range")
    print("-" * 70)
    
    invalid_conditions = [
        {
            'type': 'amount',
            'operator': 'between',
            'value': 2000,  # Greater than value2!
            'value2': 500   # Less than value!
        }
    ]
    
    response = client.post(f'/analyzer/api/rule/{amount_rule_id}/update/', {
        'name': 'Invalid Range',
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps(invalid_conditions)
    })
    
    data = json.loads(response.content)
    print(f"  Status: {response.status_code}")
    print(f"  Success: {data['success']}")
    print(f"  Error Message: {data['message']}")
    
    assert not data['success'], "Should have failed"
    assert response.status_code == 400, "Should return 400 status"
    assert 'less than' in data['message'].lower(), "Wrong error message"
    print("  ✅ VALIDATION WORKING - PASSED\n")
    
    # ============================================================
    # TEST 9: Create & Edit Category
    # ============================================================
    print("✓ TEST 9: Create & Edit Category")
    print("-" * 70)
    
    # Create category
    response = client.post('/analyzer/api/category/create/', {
        'name': 'Entertainment Subscriptions',
        'description': 'Netflix, Prime, etc',
        'icon': '🎬',
        'color': '#FF5733'
    })
    
    data = json.loads(response.content)
    category_id = data['category_id']
    print(f"  Category Created: {data['category_name']} (ID: {category_id})")
    assert data['success'], "Category creation failed"
    
    # Edit category
    response = client.post(f'/analyzer/api/category/{category_id}/edit/', {
        'name': 'Entertainment Updated',
        'description': 'All entertainment subscriptions',
        'icon': '📺',
        'color': '#00FF00'
    })
    
    data = json.loads(response.content)
    print(f"  Category Updated: {data['category_name']}")
    print(f"  New Icon: {data['category_icon']}")
    print(f"  New Color: {data['category_color']}")
    assert data['success'], "Category update failed"
    print("  ✅ PASSED\n")
    
    # ============================================================
    # TEST 10: Multiple Conditions Edit
    # ============================================================
    print("✓ TEST 10: Edit Rule with Multiple Conditions")
    print("-" * 70)
    
    multi_conditions = [
        {
            'type': 'keyword',
            'value': 'Entertainment',
            'match': 'contains'
        },
        {
            'type': 'amount',
            'operator': 'greater_than',
            'value': 100
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Multi Condition Rule',
        'category': 'ENTERTAINMENT',
        'rule_type': 'AND',
        'conditions': json.dumps(multi_conditions)
    })
    
    data = json.loads(response.content)
    multi_rule_id = data['rule_id']
    print(f"  Rule Created: {data['rule_name']} (ID: {multi_rule_id})")
    assert data['success'], "Rule creation failed"
    
    # Verify both conditions loaded
    response = client.get(f'/analyzer/api/rule/{multi_rule_id}/get/')
    data = json.loads(response.content)
    print(f"  Conditions Retrieved: {len(data['conditions'])}")
    assert len(data['conditions']) == 2, "Should have 2 conditions"
    print("  Condition 1 Type:", data['conditions'][0]['type'])
    print("  Condition 2 Type:", data['conditions'][1]['type'])
    
    # Edit to add third condition
    multi_conditions.append({
        'type': 'date',
        'from': '2025-01-01',
        'to': '2025-12-31'
    })
    
    response = client.post(f'/analyzer/api/rule/{multi_rule_id}/update/', {
        'name': 'Multi Condition Updated',
        'category': 'ENTERTAINMENT',
        'rule_type': 'OR',
        'conditions': json.dumps(multi_conditions)
    })
    
    data = json.loads(response.content)
    assert data['success'], "Update failed"
    
    # Verify all 3 conditions
    response = client.get(f'/analyzer/api/rule/{multi_rule_id}/get/')
    data = json.loads(response.content)
    print(f"  Conditions After Edit: {len(data['conditions'])}")
    assert len(data['conditions']) == 3, "Should have 3 conditions after edit"
    print("  ✅ PASSED\n")
    
    print("=" * 70)
    print("ALL LOGIC FIX TESTS COMPLETED SUCCESSFULLY! ✅")
    print("=" * 70)
    print("\nSummary:")
    print("  ✅ Create rule with conditions - Working")
    print("  ✅ Get rule - Standardized format - Working")
    print("  ✅ Edit rule - Update conditions - Working")
    print("  ✅ Validation errors - Proper HTTP codes - Working")
    print("  ✅ Create & edit category - Working")
    print("  ✅ Multiple conditions - Working")
    print("  ✅ Format consistency - Verified")
    print("  ✅ Data persistence - Verified")
    print("\n🎉 All logical inconsistencies fixed and tested!")

if __name__ == '__main__':
    try:
        test_all_logic_fixes()
    except AssertionError as ae:
        print(f"\n❌ TEST FAILED: {str(ae)}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
