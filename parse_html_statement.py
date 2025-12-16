"""
Parse HTML bank statement file and extract transactions
"""

import os
import django
from datetime import datetime
from bs4 import BeautifulSoup

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import BankAccount, BankStatement, Transaction
from analyzer.upi_parser import UPIParser
from django.contrib.auth.models import User

def parse_html_statement(file_path):
    """Extract transactions from HTML bank statement"""
    transactions = []
    
    try:
        # Read HTML file
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all table rows
        rows = soup.find_all('tr')
        
        print(f"Found {len(rows)} rows in HTML")
        
        # Skip header row (row 0)
        for idx, row in enumerate(rows[1:], 1):
            cells = row.find_all('td')
            
            if len(cells) < 5:
                continue
            
            try:
                # Extract cell values (clean unicode spaces)
                cell_values = [cell.get_text(strip=True).replace('\u200b', '').strip() for cell in cells]
                
                # Skip header rows
                if cell_values[0] == 'TransactionDate':
                    continue
                
                # Parse fields
                date_str = cell_values[0]
                description = cell_values[2]
                debit_credit = cell_values[3]
                amount_str = cell_values[4]
                
                # Skip if empty
                if not date_str or not amount_str or not description:
                    continue
                
                # Parse date (DD/MM/YYYY)
                try:
                    date = datetime.strptime(date_str, '%d/%m/%Y').date()
                except ValueError:
                    continue
                
                # Parse amount
                try:
                    amount = float(amount_str.replace(',', ''))
                except ValueError:
                    continue
                
                # Determine transaction type
                transaction_type = 'DEBIT' if debit_credit.upper() == 'D' else 'CREDIT'
                
                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': amount,
                    'transaction_type': transaction_type
                })
                
            except (IndexError, ValueError):
                continue
        
        print(f"✓ Extracted {len(transactions)} valid transactions")
        return transactions
        
    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
        import traceback
        traceback.print_exc()
        return []

def process_statement():
    """Process the HTML bank statement file"""
    
    file_path = 'media/statements/1765369388986_PLANET_OCT.xls'
    
    print("=" * 70)
    print("PROCESSING PLANET OCT BANK STATEMENT (HTML FORMAT)")
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
            account_name='PLANET October Account',
            defaults={
                'account_number': 'PLANET-OCT-2025',
                'bank_name': 'Planet Bank'
            }
        )
        if created:
            print(f"✓ Created account: {account.account_name}")
        else:
            print(f"✓ Using account: {account.account_name}")
        
        # Extract transactions from HTML
        print("\n⏳ Parsing HTML statement...")
        transactions = parse_html_statement(file_path)
        
        if not transactions:
            print("❌ No transactions found")
            return False
        
        # Create BankStatement record
        statement = BankStatement.objects.create(
            account=account,
            file_type='HTML',
            original_filename='PLANET_OCT.xls',
            statement_period_start=transactions[0]['date'],
            statement_period_end=transactions[-1]['date']
        )
        print(f"\n✓ Created statement record (ID: {statement.id})")
        print(f"  Period: {transactions[0]['date']} to {transactions[-1]['date']}")
        
        # Import transactions
        print(f"\n⏳ Importing {len(transactions)} transactions...")
        
        imported = 0
        upi_parsed = 0
        
        for idx, txn in enumerate(transactions, 1):
            try:
                # Extract UPI metadata if applicable
                category = 'OTHER'
                
                if UPIParser.is_upi_description(txn['description']):
                    upi_data = UPIParser.parse_upi_fields(txn['description'])
                    upi_parsed += 1
                    # Try to categorize based on UPI description
                    if 'purpose' in upi_data:
                        purpose = upi_data['purpose'].upper()
                        if any(word in purpose for word in ['PURCHASE', 'SHOPPING']):
                            category = 'SHOPPING'
                        elif any(word in purpose for word in ['FOOD', 'RESTAURANT']):
                            category = 'FOOD'
                        elif any(word in purpose for word in ['TAXI', 'TRANSPORT']):
                            category = 'TRANSPORT'
                        elif any(word in purpose for word in ['MEDICINE', 'HEALTH']):
                            category = 'HEALTHCARE'
                
                # Create transaction
                Transaction.objects.create(
                    statement=statement,
                    date=txn['date'],
                    description=txn['description'],
                    amount=txn['amount'],
                    transaction_type=txn['transaction_type'],
                    category=category
                )
                
                imported += 1
                
                if idx % 100 == 0:
                    print(f"  ... processed {idx} transactions ({upi_parsed} UPI parsed)")
                    
            except Exception as e:
                print(f"  ⚠ Error on transaction {idx}: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("IMPORT SUMMARY")
        print("=" * 70)
        print(f"✓ Successfully imported: {imported} transactions")
        if upi_parsed > 0:
            print(f"✓ UPI transactions parsed: {upi_parsed}")
        
        # Show financial summary
        if imported > 0:
            debits = list(Transaction.objects.filter(
                statement=statement, transaction_type='DEBIT'
            ).values_list('amount', flat=True))
            credits = list(Transaction.objects.filter(
                statement=statement, transaction_type='CREDIT'
            ).values_list('amount', flat=True))
            
            total_debit = sum(debits) if debits else 0
            total_credit = sum(credits) if credits else 0
            
            print(f"\n💰 Financial Summary:")
            print(f"   Debits (Outgoing): ₹{total_debit:,.2f}")
            print(f"   Credits (Incoming): ₹{total_credit:,.2f}")
            print(f"   Net: ₹{total_credit - total_debit:,.2f}")
            
            # Category breakdown
            print(f"\n📊 Transactions by Category:")
            categories = {}
            for tx in Transaction.objects.filter(statement=statement):
                cat = tx.category
                if cat not in categories:
                    categories[cat] = {'count': 0, 'amount': 0}
                categories[cat]['count'] += 1
                if tx.transaction_type == 'DEBIT':
                    categories[cat]['amount'] += tx.amount
            
            for cat in sorted(categories.keys()):
                print(f"   {cat}: {categories[cat]['count']} transactions (₹{categories[cat]['amount']:,.2f})")
        
        print("\n" + "=" * 70)
        print("✅ FILE PROCESSING COMPLETE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error processing statement: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = process_statement()
    exit(0 if success else 1)
