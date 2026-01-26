#!/usr/bin/env python
"""
Clean up and re-parse the problematic PDF with the new fix.
This script will help you verify that debits and credits are now parsed correctly.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import BankStatement, Transaction
from analyzer.file_parsers import PDFParser

print("=" * 100)
print("CLEANUP AND RE-PARSE - PROBLEMATIC PDF")
print("=" * 100)

# Find statements with the problematic PDF
statements = BankStatement.objects.filter(original_filename__contains='3558')

if not statements.exists():
    print("\n⚠️  No statements found with '3558' in filename")
    print("Available statements:")
    for stmt in BankStatement.objects.all()[:10]:
        print(f"  - {stmt.original_filename}")
else:
    for stmt in statements:
        print(f"\n📁 Found statement: {stmt.original_filename}")
        print(f"   Current transactions: {stmt.transaction_set.count()}")
        
        # Show current state
        debits = stmt.transaction_set.filter(transaction_type='DEBIT')
        credits = stmt.transaction_set.filter(transaction_type='CREDIT')
        
        print(f"   Current DEBIT count: {debits.count()}")
        print(f"   Current CREDIT count: {credits.count()}")
        
        if debits.count() > 0:
            print(f"\n   Sample DEBIT transactions (first 3):")
            for trans in debits[:3]:
                print(f"     - {trans.date} | {trans.description[:50]} | ₹{trans.amount}")
        
        if credits.count() > 0:
            print(f"\n   Sample CREDIT transactions (first 3):")
            for trans in credits[:3]:
                print(f"     - {trans.date} | {trans.description[:50]} | ₹{trans.amount}")
        
        # Ask user if they want to clean up
        response = input(f"\n❓ Delete all {stmt.transaction_set.count()} transactions and re-parse? (yes/no): ").strip().lower()
        
        if response == 'yes':
            print(f"\n🗑️  Deleting {stmt.transaction_set.count()} transactions...")
            stmt.transaction_set.all().delete()
            print(f"✅ Deleted! Statement now has {stmt.transaction_set.count()} transactions")
            
            # Now try to re-parse
            if stmt.statement_file:
                file_path = stmt.statement_file.path
                print(f"\n🔄 Re-parsing from: {file_path}")
                
                try:
                    # Use the appropriate parser
                    if stmt.file_type == 'PDF':
                        transactions_data = PDFParser.extract_transactions(file_path)
                    elif stmt.file_type == 'EXCEL':
                        from analyzer.file_parsers import ExcelParser
                        transactions_data = ExcelParser.extract_transactions(file_path)
                    elif stmt.file_type == 'CSV':
                        from analyzer.file_parsers import CSVParser
                        transactions_data = CSVParser.extract_transactions(file_path)
                    else:
                        transactions_data = []
                    
                    print(f"✅ Parser found {len(transactions_data)} transactions")
                    
                    if transactions_data:
                        # Show first 5 parsed transactions
                        print(f"\n   First 5 re-parsed transactions:")
                        for i, trans in enumerate(transactions_data[:5], 1):
                            print(f"     {i}. {trans['date']} | {trans['description'][:40]} | ₹{trans['amount']} ({trans['transaction_type']})")
                        
                        # Import transactions into database
                        from decimal import Decimal
                        created_count = 0
                        for trans_data in transactions_data:
                            try:
                                Transaction.objects.create(
                                    bank_statement=stmt,
                                    date=trans_data['date'],
                                    description=trans_data['description'],
                                    amount=Decimal(str(trans_data['amount'])),
                                    transaction_type=trans_data['transaction_type'],
                                    category='OTHER'
                                )
                                created_count += 1
                            except Exception as e:
                                print(f"     ❌ Error creating transaction: {e}")
                        
                        print(f"\n✅ Successfully created {created_count} transactions in database")
                        
                        # Show final statistics
                        debits_after = stmt.transaction_set.filter(transaction_type='DEBIT').count()
                        credits_after = stmt.transaction_set.filter(transaction_type='CREDIT').count()
                        print(f"\n📊 Final statistics:")
                        print(f"   Total: {debits_after + credits_after}")
                        print(f"   DEBIT: {debits_after}")
                        print(f"   CREDIT: {credits_after}")
                        
                except Exception as e:
                    print(f"❌ Error during re-parsing: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ No file attached to statement")
        else:
            print("\n⏭️  Skipped - no changes made")

print("\n" + "=" * 100)
print("SCRIPT COMPLETE")
print("=" * 100)
