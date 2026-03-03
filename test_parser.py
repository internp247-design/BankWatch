#!/usr/bin/env python
"""
Quick test script to verify Excel parser works with PLANET file format
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import logging
logging.basicConfig(level=logging.DEBUG)

from analyzer.file_parsers import StatementParser, ExcelParser

# Test with the PLANET file
excel_file = os.path.join(
    os.path.dirname(__file__),
    'media/statements/1765369388986_PLANET_OCT.xls'
)

print(f"\n{'='*80}")
print(f"Testing Excel Parser with PLANET Bank Format")
print(f"File: {excel_file}")
print(f"File exists: {os.path.exists(excel_file)}")
print(f"{'='*80}\n")

try:
    transactions = ExcelParser.extract_transactions(excel_file)
    
    print(f"\n{'='*80}")
    print(f"✓ SUCCESS! Extracted {len(transactions)} transactions")
    print(f"{'='*80}\n")
    
    # Show first 5 transactions
    print("First 5 transactions:")
    for i, txn in enumerate(transactions[:5], 1):
        print(f"{i}. {txn['date']} | {txn['description'][:50]:50} | ₹{txn['amount']:10.2f} | {txn['transaction_type']}")
    
    if len(transactions) > 5:
        print(f"\n... and {len(transactions) - 5} more transactions\n")
    
    # Show last 5 transactions
    if len(transactions) > 5:
        print("\nLast 5 transactions:")
        for i, txn in enumerate(transactions[-5:], len(transactions) - 4):
            print(f"{i}. {txn['date']} | {txn['description'][:50]:50} | ₹{txn['amount']:10.2f} | {txn['transaction_type']}")
    
    # Summary
    debits = [t for t in transactions if t['transaction_type'] == 'DEBIT']
    credits = [t for t in transactions if t['transaction_type'] == 'CREDIT']
    
    print(f"\n{'='*80}")
    print(f"Summary:")
    print(f"  Total Transactions: {len(transactions)}")
    print(f"  Debits: {len(debits)}")
    print(f"  Credits: {len(credits)}")
    print(f"  Total Debit Amount: ₹{sum(t['amount'] for t in debits):,.2f}")
    print(f"  Total Credit Amount: ₹{sum(t['amount'] for t in credits):,.2f}")
    print(f"{'='*80}\n")
    
except Exception as e:
    print(f"\n{'='*80}")
    print(f"✗ ERROR: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print(f"{'='*80}\n")
    import traceback
    traceback.print_exc()
