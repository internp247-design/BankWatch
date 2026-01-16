#!/usr/bin/env python
"""
Test PDF parsing to ensure CREDIT vs DEBIT detection is correct
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import Transaction, BankStatement
from django.db.models import Q

print("=" * 80)
print("PDF TRANSACTION TYPE DETECTION AUDIT")
print("=" * 80)

# Get latest statement (likely from PDF)
latest_stmt = BankStatement.objects.latest('upload_date')
print(f"\nAnalyzing Statement: #{latest_stmt.id}")
print(f"Filename: {latest_stmt.statement_file}")
print(f"Upload Date: {latest_stmt.upload_date}")

transactions = Transaction.objects.filter(statement=latest_stmt).order_by('date')
print(f"Total Transactions: {transactions.count()}")

# Count by type
credits = transactions.filter(transaction_type='CREDIT').count()
debits = transactions.filter(transaction_type='DEBIT').count()
unknown = transactions.exclude(transaction_type__in=['CREDIT', 'DEBIT']).count()

print(f"\nType Breakdown:")
print(f"  CREDIT (Income):  {credits}")
print(f"  DEBIT (Expense):  {debits}")
print(f"  UNKNOWN:          {unknown}")

# Check descriptions for CR/DR markers
print(f"\n📝 CHECKING FOR CR/DR MARKERS IN DESCRIPTIONS:")
print("-" * 80)

cr_marked = transactions.filter(Q(description__icontains='CR') | Q(description__icontains=' CR')).count()
dr_marked = transactions.filter(Q(description__icontains='DR') | Q(description__icontains=' DR')).count()
both_marked = transactions.filter(Q(description__icontains='CR') | Q(description__icontains=' CR')).filter(
    Q(description__icontains='DR') | Q(description__icontains=' DR')
).count()

print(f"Descriptions with CR marker: {cr_marked}")
print(f"Descriptions with DR marker: {dr_marked}")
print(f"Descriptions with both CR and DR: {both_marked}")

# Sample analysis
print(f"\n📋 SAMPLE TRANSACTIONS WITH ANALYSIS:")
print("-" * 80)

for t in transactions[:15]:
    has_cr = 'CR' in t.description.upper() or ' CR' in t.description
    has_dr = 'DR' in t.description.upper() or ' DR' in t.description
    
    print(f"\nID: {t.id} | Type: {t.transaction_type:6s} | Amount: ₹{t.amount:12,.2f}")
    print(f"Description: {t.description}")
    print(f"Has CR marker: {has_cr} | Has DR marker: {has_dr}")
    
    # Verify if type matches expected from markers
    if has_dr and t.transaction_type != 'DEBIT':
        print(f"⚠️  MISMATCH: Has DR marker but type is {t.transaction_type}")
    elif has_cr and t.transaction_type != 'CREDIT':
        print(f"⚠️  MISMATCH: Has CR marker but type is {t.transaction_type}")

# Check a few CREDIT transactions
print(f"\n✓ ALL CREDIT TRANSACTIONS:")
print("-" * 80)

credit_trans = transactions.filter(transaction_type='CREDIT').order_by('-amount')[:10]
for t in credit_trans:
    print(f"ID: {t.id} | Amount: ₹{t.amount:12,.2f} | {t.description[:60]}")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
