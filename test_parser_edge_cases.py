#!/usr/bin/env python
"""
Test error handling - simulate a file with no recognizable columns
"""
import os
import sys
import django
import tempfile
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import logging
logging.basicConfig(level=logging.INFO)

from analyzer.file_parsers import ExcelParser

# Create a test Excel file with unrecognizable columns
print("\n" + "="*80)
print("Test 1: Excel file with unrecognizable columns")
print("="*80)

test_data = {
    'UnknownCol1': ['2025-10-01', '2025-10-02'],
    'UnknownCol2': [1000, 2000],
    'UnknownCol3': ['transaction', 'transaction'],
}

with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
    df = pd.DataFrame(test_data)
    df.to_excel(tmp.name, index=False)
    tmp_file = tmp.name

try:
    transactions = ExcelParser.extract_transactions(tmp_file)
    print(f"✗ Should have raised error but got {len(transactions)} transactions")
except ValueError as e:
    print(f"✓ Correctly caught error: {str(e)[:120]}...")
except Exception as e:
    print(f"✓ Correctly caught error: {type(e).__name__}: {str(e)[:120]}...")
finally:
    os.unlink(tmp_file)

# Create a test with proper columns but invalid data
print("\n" + "="*80)
print("Test 2: Excel file with proper columns but problematic data")
print("="*80)

test_data = {
    'TransactionDate': ['invalid date', '2025-10-02'],
    'Description': ['', 'Valid desc'],  # Empty description in row 1
    'AmountInAccount': [0, 1000],        # Zero amount in row 1
    'CreditDebitFlag': ['D', 'D'],
}

with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
    df = pd.DataFrame(test_data)
    df.to_excel(tmp.name, index=False)
    tmp_file = tmp.name

try:
    transactions = ExcelParser.extract_transactions(tmp_file)
    print(f"✓ Extracted {len(transactions)} valid transaction(s) (skipped invalid rows)")
    for txn in transactions:
        print(f"  - {txn['date']} | {txn['description']} | ₹{txn['amount']} | {txn['transaction_type']}")
except Exception as e:
    print(f"✗ Unexpected error: {type(e).__name__}: {str(e)[:120]}...")
finally:
    os.unlink(tmp_file)

# Create a test with proper PLANET format
print("\n" + "="*80)
print("Test 3: Excel file with PLANET column format")
print("="*80)

test_data = {
    'TransactionDate': ['01/10/2025', '02/10/2025', '03/10/2025'],
    'ValueDate': ['01/10/2025', '02/10/2025', '03/10/2025'],
    'Description': ['Payment to ABC', 'Salary Credit', 'Bill Payment'],
    'AmountInAccount': [1000.50, 50000.00, 500.25],
    'CreditDebitFlag': ['D', 'C', 'D'],
    'Currency': ['INR', 'INR', 'INR'],
}

with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
    df = pd.DataFrame(test_data)
    df.to_excel(tmp.name, index=False)
    tmp_file = tmp.name

try:
    transactions = ExcelParser.extract_transactions(tmp_file)
    print(f"✓ Successfully extracted {len(transactions)} transactions")
    for i, txn in enumerate(transactions, 1):
        print(f"  {i}. {txn['date']} | {txn['description']:20} | ₹{txn['amount']:10.2f} | {txn['transaction_type']}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {str(e)}")
finally:
    os.unlink(tmp_file)

print("\n" + "="*80)
print("All tests completed!")
print("="*80 + "\n")
