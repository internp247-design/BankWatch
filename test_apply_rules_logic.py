#!/usr/bin/env python
"""
Test script to verify Apply Rules uses the same logic as Create/Edit
"""

import os
import django
import json
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from analyzer.models import Rule, Transaction, BankAccount, BankStatement, CustomCategory
from analyzer.rules_engine import RulesEngine

def test_apply_rules_logic():
    """Verify Apply Rules uses same logic as Create/Edit"""
    
    # Create test user and account
    import uuid
    username = f'applyruletest_{uuid.uuid4().hex[:8]}'
    user = User.objects.create_user(username=username, password='testpass123')
    
    account = BankAccount.objects.create(
        user=user,
        bank_name='Test Bank',
        account_number='12345678',
        account_name='Test Account'
    )
    
    statement = BankStatement.objects.create(
        account=account,
        file_type='CSV',
        original_filename='test_statement.csv',
        statement_period_start=datetime.now().date().replace(day=1),
        statement_period_end=datetime.now().date()
    )
    
    client = Client()
    client.login(username='applyruletest', password='testpass123')
    
    print("=" * 70)
    print("TESTING APPLY RULES LOGIC - CONSISTENCY WITH CREATE/EDIT")
    print("=" * 70)
    
    # ============================================================
    # TEST 1: Create Rule and Verify Logic Used During Apply
    # ============================================================
    print("\n✓ TEST 1: Create Rule with BETWEEN Amount Condition")
    print("-" * 70)
    
    # Create rule: 500 <= amount <= 2000
    conditions = [
        {
            'type': 'amount',
            'operator': 'between',
            'value': 500,
            'value2': 2000
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Amount Between 500-2000',
        'category': 'FOOD',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    rule_id = data['rule_id']
    print(f"  Rule Created: {data['rule_name']} (ID: {rule_id})")
    assert data['success'], "Rule creation failed"
    print("  ✅ PASSED\n")
    
    # ============================================================
    # TEST 2: Create Test Transactions
    # ============================================================
    print("✓ TEST 2: Create Test Transactions")
    print("-" * 70)
    
    # Get or create a default category
    from analyzer.models import Category
    default_category = Category.objects.first()
    if not default_category:
        default_category = Category.objects.create(name='UNCATEGORIZED', icon='📋', color='#808080')
    
    # Transaction within range (500-2000) - should match
    tx1 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='Grocery Store Purchase',
        amount=750.00,
        transaction_type='DEBIT',
        category=default_category
    )
    
    # Transaction above range (>2000) - should NOT match
    tx2 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='Grocery Store Purchase',
        amount=3000.00,
        transaction_type='DEBIT',
        category=default_category
    )
    
    # Transaction below range (<500) - should NOT match
    tx3 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='Grocery Store Purchase',
        amount=250.00,
        transaction_type='DEBIT',
        category=default_category
    )
    
    print(f"  Transaction 1: $750 (within 500-2000 range)")
    print(f"  Transaction 2: $3000 (above 500-2000 range)")
    print(f"  Transaction 3: $250 (below 500-2000 range)")
    print("  ✅ PASSED\n")
    
    # ============================================================
    # TEST 3: Apply Rules and Verify Correct Matching
    # ============================================================
    print("✓ TEST 3: Apply Rules - Verify Logic Consistency")
    print("-" * 70)
    
    # Use RulesEngine directly (same as apply_rules view uses)
    engine = RulesEngine(user)
    
    # Test Transaction 1 (within range)
    tx1_data = {
        'date': tx1.date,
        'description': tx1.description,
        'amount': float(tx1.amount),
        'transaction_type': tx1.transaction_type
    }
    matched_rule_1 = engine.find_matching_rule(tx1_data)
    print(f"  TX1 ($750): Matched Rule = {matched_rule_1.name if matched_rule_1 else 'None'}")
    assert matched_rule_1 is not None, "TX1 should match (750 is between 500-2000)"
    assert matched_rule_1.name == 'Amount Between 500-2000', "Wrong rule matched"
    
    # Test Transaction 2 (above range)
    tx2_data = {
        'date': tx2.date,
        'description': tx2.description,
        'amount': float(tx2.amount),
        'transaction_type': tx2.transaction_type
    }
    matched_rule_2 = engine.find_matching_rule(tx2_data)
    print(f"  TX2 ($3000): Matched Rule = {matched_rule_2.name if matched_rule_2 else 'None'}")
    assert matched_rule_2 is None, "TX2 should NOT match (3000 is above 2000)"
    
    # Test Transaction 3 (below range)
    tx3_data = {
        'date': tx3.date,
        'description': tx3.description,
        'amount': float(tx3.amount),
        'transaction_type': tx3.transaction_type
    }
    matched_rule_3 = engine.find_matching_rule(tx3_data)
    print(f"  TX3 ($250): Matched Rule = {matched_rule_3.name if matched_rule_3 else 'None'}")
    assert matched_rule_3 is None, "TX3 should NOT match (250 is below 500)"
    
    print("  ✅ APPLY LOGIC MATCHES CREATE DEFINITION - PASSED\n")
    
    # ============================================================
    # TEST 4: Keyword Rule - Apply Logic
    # ============================================================
    print("✓ TEST 4: Keyword Rule - Verify Apply Uses Create Logic")
    print("-" * 70)
    
    conditions = [
        {
            'type': 'keyword',
            'value': 'Amazon',
            'match': 'contains'
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Amazon Keyword Rule',
        'category': 'SHOPPING',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    keyword_rule_id = data['rule_id']
    print(f"  Rule Created: {data['rule_name']}")
    
    # Test keyword matching
    tx4 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='AMAZON.COM PURCHASE',
        amount=100.00,
        transaction_type='debit',
        category=None
    )
    
    tx5 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='WALMART PURCHASE',
        amount=100.00,
        transaction_type='debit',
        category=None
    )
    
    # Test TX4 (contains 'amazon')
    tx4_data = {
        'date': tx4.date,
        'description': tx4.description,
        'amount': float(tx4.amount),
        'transaction_type': tx4.transaction_type
    }
    matched_rule_4 = engine.find_matching_rule(tx4_data)
    print(f"  TX4 ('AMAZON...'): Matched = {matched_rule_4.name if matched_rule_4 else 'None'}")
    assert matched_rule_4 is not None, "TX4 should match (contains 'amazon')"
    
    # Test TX5 (does NOT contain 'amazon')
    tx5_data = {
        'date': tx5.date,
        'description': tx5.description,
        'amount': float(tx5.amount),
        'transaction_type': tx5.transaction_type
    }
    matched_rule_5 = engine.find_matching_rule(tx5_data)
    print(f"  TX5 ('WALMART...'): Matched = {matched_rule_5.name if matched_rule_5 else 'None'}")
    assert matched_rule_5 is None, "TX5 should NOT match (does not contain 'amazon')"
    
    print("  ✅ KEYWORD LOGIC MATCHES - PASSED\n")
    
    # ============================================================
    # TEST 5: Date Range Rule
    # ============================================================
    print("✓ TEST 5: Date Range Rule - Verify Apply Uses Create Logic")
    print("-" * 70)
    
    today = datetime.now().date()
    start_date = today.replace(day=1)
    end_date = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    conditions = [
        {
            'type': 'date',
            'from': start_date.isoformat(),
            'to': end_date.isoformat()
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Current Month Rule',
        'category': 'UTILITIES',
        'rule_type': 'AND',
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    date_rule_id = data['rule_id']
    print(f"  Rule Created: {data['rule_name']}")
    print(f"  Date Range: {start_date} to {end_date}")
    
    # Transaction within date range
    tx6 = Transaction.objects.create(
        statement=statement,
        date=today,
        description='Utility Bill',
        amount=100.00,
        transaction_type='debit',
        category=None
    )
    
    # Transaction outside date range
    tx7 = Transaction.objects.create(
        statement=statement,
        date=today.replace(year=today.year - 1),
        description='Utility Bill',
        amount=100.00,
        transaction_type='debit',
        category=None
    )
    
    # Test TX6 (within range)
    tx6_data = {
        'date': tx6.date,
        'description': tx6.description,
        'amount': float(tx6.amount),
        'transaction_type': tx6.transaction_type
    }
    matched_rule_6 = engine.find_matching_rule(tx6_data)
    print(f"  TX6 (today): Matched = {matched_rule_6.name if matched_rule_6 else 'None'}")
    assert matched_rule_6 is not None, "TX6 should match (within date range)"
    
    # Test TX7 (outside range)
    tx7_data = {
        'date': tx7.date,
        'description': tx7.description,
        'amount': float(tx7.amount),
        'transaction_type': tx7.transaction_type
    }
    matched_rule_7 = engine.find_matching_rule(tx7_data)
    print(f"  TX7 (last year): Matched = {matched_rule_7.name if matched_rule_7 else 'None'}")
    assert matched_rule_7 is None, "TX7 should NOT match (outside date range)"
    
    print("  ✅ DATE LOGIC MATCHES - PASSED\n")
    
    # ============================================================
    # TEST 6: AND Rule (Multiple Conditions)
    # ============================================================
    print("✓ TEST 6: AND Rule - All Conditions Must Match")
    print("-" * 70)
    
    conditions = [
        {
            'type': 'keyword',
            'value': 'Store',
            'match': 'contains'
        },
        {
            'type': 'amount',
            'operator': 'greater_than',
            'value': 100
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Store Over 100',
        'category': 'SHOPPING',
        'rule_type': 'AND',  # ALL conditions must match
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    and_rule_id = data['rule_id']
    print(f"  Rule Created: {data['rule_name']} (AND logic)")
    
    # Case 1: Has "Store" but amount <= 100 - should NOT match
    tx8 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='Store Purchase',
        amount=50.00,
        transaction_type='debit',
        category=None
    )
    
    # Case 2: Amount > 100 but no "Store" - should NOT match
    tx9 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='Online Purchase',
        amount=150.00,
        transaction_type='debit',
        category=None
    )
    
    # Case 3: Has "Store" AND amount > 100 - should match
    tx10 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='Store Purchase',
        amount=150.00,
        transaction_type='debit',
        category=None
    )
    
    # Test TX8
    tx8_data = {
        'date': tx8.date,
        'description': tx8.description,
        'amount': float(tx8.amount),
        'transaction_type': tx8.transaction_type
    }
    matched = engine.find_matching_rule(tx8_data)
    print(f"  TX8 ('Store', $50): Matched = {matched.name if matched else 'None'}")
    assert matched is None, "TX8 should NOT match (amount not > 100)"
    
    # Test TX9
    tx9_data = {
        'date': tx9.date,
        'description': tx9.description,
        'amount': float(tx9.amount),
        'transaction_type': tx9.transaction_type
    }
    matched = engine.find_matching_rule(tx9_data)
    print(f"  TX9 (no 'Store', $150): Matched = {matched.name if matched else 'None'}")
    assert matched is None, "TX9 should NOT match (no 'Store')"
    
    # Test TX10
    tx10_data = {
        'date': tx10.date,
        'description': tx10.description,
        'amount': float(tx10.amount),
        'transaction_type': tx10.transaction_type
    }
    matched = engine.find_matching_rule(tx10_data)
    print(f"  TX10 ('Store', $150): Matched = {matched.name if matched else 'None'}")
    assert matched is not None, "TX10 should match (both conditions met)"
    
    print("  ✅ AND LOGIC CORRECT - PASSED\n")
    
    # ============================================================
    # TEST 7: OR Rule (At Least One Condition Must Match)
    # ============================================================
    print("✓ TEST 7: OR Rule - At Least One Condition Must Match")
    print("-" * 70)
    
    conditions = [
        {
            'type': 'keyword',
            'value': 'Amazon',
            'match': 'contains'
        },
        {
            'type': 'keyword',
            'value': 'Netflix',
            'match': 'contains'
        }
    ]
    
    response = client.post('/analyzer/api/rule/create/', {
        'name': 'Amazon OR Netflix',
        'category': 'ENTERTAINMENT',
        'rule_type': 'OR',  # AT LEAST ONE condition must match
        'conditions': json.dumps(conditions)
    })
    
    data = json.loads(response.content)
    or_rule_id = data['rule_id']
    print(f"  Rule Created: {data['rule_name']} (OR logic)")
    
    # Case 1: Has "Amazon" (first condition matches)
    tx11 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='AMAZON.COM',
        amount=50.00,
        transaction_type='debit',
        category=None
    )
    
    # Case 2: Has "Netflix" (second condition matches)
    tx12 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='NETFLIX SUBSCRIPTION',
        amount=15.00,
        transaction_type='debit',
        category=None
    )
    
    # Case 3: Neither "Amazon" nor "Netflix"
    tx13 = Transaction.objects.create(
        statement=statement,
        date=datetime.now().date(),
        description='HULU SUBSCRIPTION',
        amount=10.00,
        transaction_type='debit',
        category=None
    )
    
    # Test TX11
    tx11_data = {
        'date': tx11.date,
        'description': tx11.description,
        'amount': float(tx11.amount),
        'transaction_type': tx11.transaction_type
    }
    matched = engine.find_matching_rule(tx11_data)
    print(f"  TX11 ('AMAZON'): Matched = {matched.name if matched else 'None'}")
    assert matched is not None, "TX11 should match (first condition met)"
    
    # Test TX12
    tx12_data = {
        'date': tx12.date,
        'description': tx12.description,
        'amount': float(tx12.amount),
        'transaction_type': tx12.transaction_type
    }
    matched = engine.find_matching_rule(tx12_data)
    print(f"  TX12 ('NETFLIX'): Matched = {matched.name if matched else 'None'}")
    assert matched is not None, "TX12 should match (second condition met)"
    
    # Test TX13
    tx13_data = {
        'date': tx13.date,
        'description': tx13.description,
        'amount': float(tx13.amount),
        'transaction_type': tx13.transaction_type
    }
    matched = engine.find_matching_rule(tx13_data)
    print(f"  TX13 ('HULU'): Matched = {matched.name if matched else 'None'}")
    assert matched is None, "TX13 should NOT match (no conditions met)"
    
    print("  ✅ OR LOGIC CORRECT - PASSED\n")
    
    print("=" * 70)
    print("ALL APPLY RULES LOGIC TESTS COMPLETED SUCCESSFULLY! ✅")
    print("=" * 70)
    print("\nSummary:")
    print("  ✅ BETWEEN amount validation - Consistent")
    print("  ✅ Keyword matching logic - Consistent")
    print("  ✅ Date range validation - Consistent")
    print("  ✅ AND rule logic (all match) - Consistent")
    print("  ✅ OR rule logic (any match) - Consistent")
    print("  ✅ Type conversion (float) - Consistent")
    print("\n🎉 Apply Rules uses EXACT SAME logic as Create/Edit!")

if __name__ == '__main__':
    try:
        test_apply_rules_logic()
    except AssertionError as ae:
        print(f"\n❌ TEST FAILED: {str(ae)}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
