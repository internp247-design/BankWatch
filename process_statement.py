"""
Process PLANET_OCT.xls bank statement file

This script reads the Excel file and extracts transaction data,
then stores it in the BankWatch database.
"""

import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import BankAccount, BankStatement, Transaction
from analyzer.file_parsers import StatementParser
from django.contrib.auth.models import User

def process_statement_file():
    """Process the PLANET_OCT.xls file"""
    
    file_path = 'media/statements/1765369388986_PLANET_OCT.xls'
    
    print("=" * 70)
    print("PROCESSING BANK STATEMENT FILE")
    print("=" * 70)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"\n📄 File: {file_path}")
    print(f"📊 Size: {os.path.getsize(file_path) / 1024:.2f} KB")
    print(f"📅 Modified: {datetime.fromtimestamp(os.path.getmtime(file_path))}")
    
    try:
        # Get or create default user and account
        user, created = User.objects.get_or_create(
            username='bankwatch_user',
            defaults={'first_name': 'Default', 'last_name': 'User'}
        )
        print(f"\n👤 User: {user.username}")
        
        account, created = BankAccount.objects.get_or_create(
            user=user,
            account_name='PLANET Account',
            defaults={
                'account_number': 'PLANET-OCT',
                'bank_name': 'Planet Bank'
            }
        )
        if created:
            print(f"✓ Created account: {account.account_name}")
        else:
            print(f"✓ Using existing account: {account.account_name}")
        
        # Extract file type from extension
        file_type = StatementParser.get_file_type(file_path)
        print(f"📋 File type: {file_type}")
        
        # Extract transactions from file
        print("\n⏳ Extracting transactions from file...")
        transactions = StatementParser.parse_file(file_path, file_type)
        
        if not transactions:
            print("❌ No transactions found in file")
            return False
        
        print(f"✓ Found {len(transactions)} transactions")
        
        # Create BankStatement record
        statement = BankStatement.objects.create(
            account=account,
            file_type=file_type,
            original_filename='PLANET_OCT.xls',
            statement_period_start=transactions[0].get('date') if transactions else None,
            statement_period_end=transactions[-1].get('date') if transactions else None,
        )
        print(f"\n✓ Created statement record (ID: {statement.id})")
        
        # Import transactions
        print(f"\n⏳ Importing {len(transactions)} transactions...")
        
        imported = 0
        skipped = 0
        errors = 0
        
        for idx, txn in enumerate(transactions, 1):
            try:
                # Validate required fields
                if not txn.get('date') or not txn.get('amount'):
                    skipped += 1
                    continue
                
                # Create transaction
                Transaction.objects.create(
                    statement=statement,
                    date=txn.get('date'),
                    description=txn.get('description', 'No description'),
                    amount=txn.get('amount', 0),
                    transaction_type=txn.get('transaction_type', 'DEBIT'),
                    category='OTHER'  # Default category
                )
                imported += 1
                
                if idx % 50 == 0:
                    print(f"  ... processed {idx} transactions")
                    
            except Exception as e:
                errors += 1
                print(f"  ⚠ Error importing transaction {idx}: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("IMPORT SUMMARY")
        print("=" * 70)
        print(f"✓ Successfully imported: {imported} transactions")
        if skipped > 0:
            print(f"⚠ Skipped: {skipped} transactions (missing required fields)")
        if errors > 0:
            print(f"❌ Errors: {errors} transactions")
        
        # Show transaction overview
        if imported > 0:
            total_debit = sum(t.amount for t in Transaction.objects.filter(
                statement=statement, transaction_type='DEBIT'))
            total_credit = sum(t.amount for t in Transaction.objects.filter(
                statement=statement, transaction_type='CREDIT'))
            
            print(f"\n💰 Financial Summary:")
            print(f"   Total Debit (Outgoing): ₹{total_debit:,.2f}")
            print(f"   Total Credit (Incoming): ₹{total_credit:,.2f}")
            print(f"   Net: ₹{total_credit - total_debit:,.2f}")
        
        print("\n" + "=" * 70)
        print("✅ FILE PROCESSING COMPLETE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = process_statement_file()
    exit(0 if success else 1)
