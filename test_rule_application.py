#!/usr/bin/env python
"""
Test script to verify rules are being applied correctly
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Rule, RuleCondition, Transaction
from analyzer.rules_engine import RulesEngine, categorize_with_rules
from datetime import datetime

def test_rule_application():
    """Test if rules are being applied correctly"""
    
    print("=" * 70)
    print("TESTING RULE APPLICATION")
    print("=" * 70)
    
    # Get user
    user = User.objects.filter(is_superuser=False).first()
    if not user:
        print("No test user found")
        return
    
    print(f"\nTest User: {user.username}\n")
    
    # Get first transaction
    tx = Transaction.objects.filter(statement__account__user=user).first()
    if not tx:
        print("No transactions found")
        return
    
    print(f"Test Transaction:")
    print(f"  Description: {tx.description}")
    print(f"  Amount: ₹{tx.amount}")
    print(f"  Current Category: {tx.category}\n")
    
    # Prepare transaction data
    tx_data = {
        'date': tx.date,
        'description': tx.description,
        'amount': float(tx.amount),
        'transaction_type': tx.transaction_type
    }
    
    # Test with categorize_with_rules
    print("Step 1: Test categorize_with_rules():")
    result = categorize_with_rules(tx_data, user)
    print(f"  Result: {result}\n")
    
    # Test with RulesEngine
    print("Step 2: Test RulesEngine directly:")
    engine = RulesEngine(user)
    
    # Show active rules
    active_rules = Rule.objects.filter(user=user, is_active=True)
    print(f"  Active Rules: {active_rules.count()}")
    
    for rule in active_rules[:3]:
        print(f"    - {rule.name} → {rule.category}")
        matches = engine._matches_rule(tx_data, rule)
        print(f"      Matches: {matches}")
        
        if matches:
            for cond in rule.conditions.all():
                cond_matches = engine._matches_condition(tx_data, cond)
                print(f"        {cond.condition_type}: {cond_matches}")
    
    # Test find_matching_rule
    print(f"\n  find_matching_rule() result:")
    matched_rule = engine.find_matching_rule(tx_data)
    print(f"    Matched Rule: {matched_rule.name if matched_rule else 'None'}")
    print(f"    Would be categorized as: {matched_rule.category if matched_rule else 'Using fallback'}\n")
    
    # Check if we can create a simple test rule
    print("Step 3: Create and test a simple keyword rule:")
    test_rule_name = f"TEST RULE {datetime.now().timestamp()}"
    
    # Create a rule that matches the transaction
    test_rule = Rule.objects.create(
        user=user,
        name=test_rule_name,
        category='SHOPPING',
        rule_type='OR',
        is_active=True
    )
    
    # Get the first word of the description
    first_word = tx.description.split()[0]
    
    # Create a condition that should match
    RuleCondition.objects.create(
        rule=test_rule,
        condition_type='KEYWORD',
        keyword=first_word,
        keyword_match_type='CONTAINS'
    )
    
    print(f"  Created rule: {test_rule_name}")
    print(f"  Condition: Contains '{first_word}'\n")
    
    # Refresh engine
    engine = RulesEngine(user)
    
    # Test if the rule matches
    matched = engine.find_matching_rule(tx_data)
    print(f"  Rule matching result: {matched.name if matched else 'No match'}")
    print(f"  Should match our test rule: {matched.name == test_rule_name if matched else False}\n")
    
    # Clean up
    test_rule.delete()
    print("Cleaned up test rule\n")
    
    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)

if __name__ == '__main__':
    try:
        test_rule_application()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
