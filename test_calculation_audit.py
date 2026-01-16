#!/usr/bin/env python
"""
Comprehensive audit of calculation logic across the project
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import Transaction, BankStatement, BankAccount, AnalysisSummary
from django.db.models import Sum, Count
from decimal import Decimal

print("=" * 80)
print("BANKWATCH CALCULATION AUDIT")
print("=" * 80)

# Get all transactions
all_transactions = Transaction.objects.all()
print(f"\n📊 TOTAL TRANSACTIONS IN DATABASE: {all_transactions.count()}")

# Breakdown by type
credit_count = all_transactions.filter(transaction_type='CREDIT').count()
debit_count = all_transactions.filter(transaction_type='DEBIT').count()

print(f"\n✓ CREDIT transactions: {credit_count}")
print(f"✗ DEBIT transactions: {debit_count}")

# Check for any unknown transaction types
unknown = all_transactions.exclude(transaction_type__in=['CREDIT', 'DEBIT']).count()
if unknown > 0:
    print(f"⚠️  UNKNOWN transaction types: {unknown}")
    for t in all_transactions.exclude(transaction_type__in=['CREDIT', 'DEBIT'])[:5]:
        print(f"   - {t.id}: {t.transaction_type}")

# Sum by type
total_income = all_transactions.filter(transaction_type='CREDIT').aggregate(
    total=Sum('amount')
)['total'] or Decimal('0')

total_expenses = all_transactions.filter(transaction_type='DEBIT').aggregate(
    total=Sum('amount')
)['total'] or Decimal('0')

net_savings = total_income - total_expenses

print(f"\n💰 AGGREGATED CALCULATIONS:")
print(f"   Total Income (CREDIT):   ₹{total_income:,.2f}")
print(f"   Total Expenses (DEBIT):  ₹{total_expenses:,.2f}")
print(f"   Net Savings:             ₹{net_savings:,.2f}")

# Check per statement
print(f"\n📋 CALCULATIONS PER STATEMENT:")
print("-" * 80)

statements = BankStatement.objects.all().order_by('-upload_date')
for stmt in statements[:10]:
    stmt_transactions = Transaction.objects.filter(statement=stmt)
    
    stmt_income = stmt_transactions.filter(transaction_type='CREDIT').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    stmt_expenses = stmt_transactions.filter(transaction_type='DEBIT').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    stmt_savings = stmt_income - stmt_expenses
    trans_count = stmt_transactions.count()
    
    # Check AnalysisSummary
    try:
        summary = AnalysisSummary.objects.get(statement=stmt)
        summary_match = (
            float(summary.total_income) == float(stmt_income) and
            float(summary.total_expenses) == float(stmt_expenses)
        )
        match_symbol = "✓" if summary_match else "✗"
    except AnalysisSummary.DoesNotExist:
        match_symbol = "❌"
        summary = None
    
    print(f"\n{match_symbol} Statement #{stmt.id} ({stmt.upload_date.date()})")
    print(f"   Transactions: {trans_count}")
    print(f"   Income:       ₹{stmt_income:,.2f}")
    print(f"   Expenses:     ₹{stmt_expenses:,.2f}")
    print(f"   Savings:      ₹{stmt_savings:,.2f}")
    
    if summary:
        print(f"   Summary stored: Income=₹{summary.total_income:,.2f}, Expenses=₹{summary.total_expenses:,.2f}")
        if not summary_match:
            print(f"   ⚠️  MISMATCH DETECTED!")
    else:
        print(f"   ⚠️  NO ANALYSIS SUMMARY FOUND!")

# Sample some transactions to verify type detection
print(f"\n📝 SAMPLE TRANSACTIONS (First 20):")
print("-" * 80)

sample_transactions = Transaction.objects.all()[:20]
for t in sample_transactions:
    print(f"ID: {t.id:4d} | Type: {t.transaction_type:6s} | Amount: ₹{t.amount:12,.2f} | {t.description[:40]}")

# Check for negative amounts
negative_amounts = all_transactions.filter(amount__lt=0).count()
if negative_amounts > 0:
    print(f"\n⚠️  WARNING: Found {negative_amounts} transactions with negative amounts!")
    for t in all_transactions.filter(amount__lt=0)[:5]:
        print(f"   - ID {t.id}: {t.transaction_type} ₹{t.amount}")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
