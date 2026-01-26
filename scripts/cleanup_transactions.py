#!/usr/bin/env python
"""
Clean up transactions from the problematic PDF so we can re-parse with the fix.
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import BankStatement, Transaction

# Find statements with the problematic PDF
statements = BankStatement.objects.filter(original_filename__contains='3558')

if statements.exists():
    for stmt in statements:
        print(f"\n📁 Found: {stmt.original_filename}")
        
        # Count by type
        total = stmt.transaction_set.count()
        debits = stmt.transaction_set.filter(transaction_type='DEBIT').count()
        credits = stmt.transaction_set.filter(transaction_type='CREDIT').count()
        
        print(f"   Total transactions: {total}")
        print(f"   DEBIT: {debits}, CREDIT: {credits}")
        
        if total > 0:
            print(f"\n   🗑️  Deleting all {total} transactions...")
            stmt.transaction_set.all().delete()
            print(f"   ✅ Deleted! Now statement has {stmt.transaction_set.count()} transactions")
            print(f"\n   You can now re-upload the PDF and it will parse correctly with the new fix!")
else:
    print("❌ No matching statements found")
    print("\nAvailable statements:")
    for stmt in BankStatement.objects.all()[:10]:
        print(f"  - {stmt.original_filename}")
