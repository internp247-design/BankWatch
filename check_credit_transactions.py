#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Transaction

user = User.objects.filter(is_superuser=False).first()
transactions = Transaction.objects.filter(statement__account__user=user)

print(f"Total Transactions: {transactions.count()}")
print(f"DEBIT: {transactions.filter(transaction_type='DEBIT').count()}")
print(f"CREDIT: {transactions.filter(transaction_type='CREDIT').count()}")

# Find any credit transactions
credits = transactions.filter(transaction_type='CREDIT')[:5]
if credits.exists():
    print("\nSample CREDIT transactions:")
    for tx in credits:
        print(f"  {tx.description[:80]}")
else:
    print("\n❌ NO CREDIT TRANSACTIONS IN DATABASE!")

# Check if "cr" appears in any DEBIT description
debit_with_cr = transactions.filter(transaction_type='DEBIT', description__icontains='cr')
print(f"\nDEBIT transactions with 'cr' in description: {debit_with_cr.count()}")
if debit_with_cr.count() > 0:
    print("Sample:")
    for tx in debit_with_cr[:3]:
        print(f"  {tx.description[:80]}")
