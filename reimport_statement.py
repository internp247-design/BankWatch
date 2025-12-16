"""
Reimport the statement with proper transaction parsing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import BankStatement, Transaction, AnalysisSummary
from analyzer.file_parsers import StatementParser
from analyzer.upi_parser import UPIParser
from analyzer.rules_engine import categorize_with_rules

# Clear old statement
print("Clearing old statements...")
old_statements = BankStatement.objects.all()
for stmt in old_statements:
    print(f"  Deleting statement {stmt.id}")
    stmt.delete()

print("✓ Cleared old data\n")

# Get the uploaded file
file_path = 'media/statements/1765369388986_PLANET_OCT.xls'
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

# Get or create account/user
from django.contrib.auth.models import User
user = User.objects.first()
if not user:
    print("No users found")
    exit(1)

from analyzer.models import BankAccount
account = BankAccount.objects.filter(user=user).first()
if not account:
    print("No account found for user")
    exit(1)

# Create statement record
from datetime import datetime
statement = BankStatement.objects.create(
    account=account,
    file_type=BankStatement.EXCEL,
    original_filename='PLANET_OCT.xls',
    upload_date=datetime.now()
)
print(f"✓ Created statement record (ID: {statement.id})")

# Parse transactions
print("\nParsing transactions...")
transactions_data = StatementParser.parse_file(file_path, BankStatement.EXCEL)
print(f"✓ Extracted {len(transactions_data)} transactions")

# Update statement period
if transactions_data:
    statement.statement_period_start = transactions_data[0]['date']
    statement.statement_period_end = transactions_data[-1]['date']
    statement.save()
    print(f"  Period: {transactions_data[0]['date']} to {transactions_data[-1]['date']}")

# Create transactions
print(f"\nImporting {len(transactions_data)} transactions...")
created = 0
upi_parsed = 0
categories_used = {}

for idx, txn_data in enumerate(transactions_data, 1):
    # Determine category based on description
    category = 'OTHER'
    desc = txn_data['description'].upper()
    
    if UPIParser.is_upi_description(txn_data['description']):
        upi_data = UPIParser.parse_upi_fields(txn_data['description'])
        upi_parsed += 1
        
        # Try to categorize based on UPI data and description
        if 'purpose' in upi_data:
            purpose = upi_data['purpose'].upper()
        else:
            purpose = desc
        
        # Check description and purpose for keywords
        full_text = desc + ' ' + purpose
        
        if any(word in full_text for word in ['PURCHASE', 'SHOPPING', 'STORE', 'AMAZON', 'FLIPKART', 'MALL']):
            category = 'SHOPPING'
        elif any(word in full_text for word in ['FOOD', 'RESTAURANT', 'PIZZA', 'BURGER', 'CAFE', 'ZOMATO', 'TASTY', 'HOTEL']):
            category = 'FOOD'
        elif any(word in full_text for word in ['TAXI', 'TRANSPORT', 'METRO', 'BUS', 'CARZONRENT', 'UBER', 'OLA', 'AUTO', 'PETROL']):
            category = 'TRANSPORT'
        elif any(word in full_text for word in ['MEDICINE', 'HEALTH', 'DENTAL', 'HOSPITAL', 'CLINIC', 'DOCTOR']):
            category = 'HEALTHCARE'
        elif any(word in full_text for word in ['TRAVEL', 'HOTEL', 'BOOKING', 'FLIGHT', 'ACCOMMODATION']):
            category = 'TRAVEL'
        elif any(word in full_text for word in ['ENTERTAINMENT', 'MOVIE', 'CINEMA', 'TICKET', 'GAME']):
            category = 'ENTERTAINMENT'
        elif any(word in full_text for word in ['BILL', 'CHARGE', 'ELECTRICITY', 'WATER', 'INTERNET', 'AIRTEL', 'BROADBAND']):
            category = 'BILLS'
        elif any(word in full_text for word in ['SALARY', 'INCOME', 'DEPOSIT', 'CREDIT']):
            category = 'INCOME'
        
    categories_used[category] = categories_used.get(category, 0) + 1
    
    Transaction.objects.create(
        statement=statement,
        date=txn_data['date'],
        description=txn_data['description'][:500],
        amount=txn_data['amount'],
        transaction_type=txn_data['transaction_type'],
        category=category
    )
    created += 1
    
    if idx % 50 == 0:
        print(f"  ... processed {idx} transactions ({upi_parsed} UPI parsed)")

# Create Analysis Summary
transactions = Transaction.objects.filter(statement=statement)
total_income = sum(t.amount for t in transactions if t.transaction_type == 'CREDIT')
total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'DEBIT')

AnalysisSummary.objects.create(
    statement=statement,
    total_income=total_income,
    total_expenses=total_expenses,
    net_savings=total_income - total_expenses
)

print("\n" + "=" * 70)
print("IMPORT COMPLETE")
print("=" * 70)
print(f"✓ Imported: {created} transactions")
print(f"✓ UPI parsed: {upi_parsed} transactions")
print(f"\n💰 Summary:")
print(f"   Total Income (Credits): ₹{total_income:,.2f}")
print(f"   Total Expenses (Debits): ₹{total_expenses:,.2f}")
print(f"   Net Savings: ₹{total_income - total_expenses:,.2f}")

# Show category breakdown
print(f"\n📊 Categories During Import:")
for cat in sorted(categories_used.keys()):
    print(f"   {cat}: {categories_used[cat]} transactions")

# Verify in database
print(f"\n📊 Category Breakdown in Database:")
categories_db = {}
for tx in Transaction.objects.filter(statement=statement):
    cat = tx.category
    if cat not in categories_db:
        categories_db[cat] = {'count': 0, 'amount': 0}
    categories_db[cat]['count'] += 1
    if tx.transaction_type == 'DEBIT':
        categories_db[cat]['amount'] += tx.amount

for cat in sorted(categories_db.keys()):
    print(f"   {cat}: {categories_db[cat]['count']} trans (₹{categories_db[cat]['amount']:,.2f})")
