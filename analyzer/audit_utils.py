"""
Audit utility functions for calculating forensic audit report metrics.
All calculations are done in real-time from transaction data.
"""

from decimal import Decimal
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import statistics


def calculate_duplicate_count(transactions):
    """
    Detect and count duplicate transactions (same date + amount + description).
    
    Returns:
        int: Count of duplicate transactions
    """
    seen = set()
    duplicates = set()
    
    for txn in transactions:
        # Create a tuple key for deduplication
        key = (
            txn.date.isoformat(),
            str(txn.amount),
            txn.description.strip().lower()
        )
        
        if key in seen:
            duplicates.add(txn.id)
        else:
            seen.add(key)
    
    return len(duplicates)


def calculate_data_integrity(transactions):
    """
    Calculate data integrity metrics including quality score.
    
    Quality Score = (total_transactions - duplicates) / total_transactions * 100
    Validation Status: Pass (>80%), Warning (50-80%), Fail (<50%)
    
    Returns:
        dict: Data integrity metrics
    """
    if not transactions:
        return {
            'quality_score': 0,
            'total_transactions': 0,
            'date_range_days': 0,
            'statements_count': 0,
            'duplicate_count': 0,
            'validation_status': 'Fail',
            'earliest_date': None,
            'latest_date': None
        }
    
    total_txns = transactions.count()
    duplicate_count = calculate_duplicate_count(transactions)
    
    # Quality score = percentage of non-duplicate transactions
    if total_txns > 0:
        quality_score = int(((total_txns - duplicate_count) / total_txns) * 100)
    else:
        quality_score = 0
    
    # Determine validation status
    if quality_score >= 80:
        validation_status = 'Pass'
    elif quality_score >= 50:
        validation_status = 'Warning'
    else:
        validation_status = 'Fail'
    
    # Calculate date range
    dates = transactions.values_list('date', flat=True).distinct()
    if dates:
        earliest_date = min(dates)
        latest_date = max(dates)
        date_range_days = (latest_date - earliest_date).days
    else:
        earliest_date = None
        latest_date = None
        date_range_days = 0
    
    # Count unique statements
    statements_count = transactions.values('statement').distinct().count()
    
    return {
        'quality_score': quality_score,
        'total_transactions': total_txns,
        'date_range_days': date_range_days,
        'statements_count': statements_count,
        'duplicate_count': duplicate_count,
        'validation_status': validation_status,
        'earliest_date': earliest_date,
        'latest_date': latest_date
    }


def calculate_financial_summary(transactions):
    """
    Calculate financial overview metrics.
    
    Returns:
        dict: Financial summary with income, expenses, net change, and savings rate
    """
    if not transactions:
        return {
            'total_credits': Decimal('0.00'),
            'total_debits': Decimal('0.00'),
            'net_change': Decimal('0.00'),
            'savings_rate': 0.0
        }
    
    # Calculate totals
    credit_data = transactions.filter(transaction_type='CREDIT').aggregate(
        total=Sum('amount')
    )
    total_credits = credit_data['total'] or Decimal('0.00')
    
    debit_data = transactions.filter(transaction_type='DEBIT').aggregate(
        total=Sum('amount')
    )
    total_debits = debit_data['total'] or Decimal('0.00')
    
    net_change = total_credits - total_debits
    
    # Calculate savings rate
    if total_credits > 0:
        savings_rate = float((net_change / total_credits) * 100)
    else:
        savings_rate = 0.0
    
    return {
        'total_credits': total_credits,
        'total_debits': total_debits,
        'net_change': net_change,
        'savings_rate': round(savings_rate, 2)
    }


def identify_high_value_transactions(transactions):
    """
    Identify high-value transactions (top 5% by absolute amount).
    
    Returns:
        list: List of high-value transaction dicts
    """
    if not transactions:
        return []
    
    # Get all transaction amounts
    amounts = list(transactions.values_list('amount', flat=True))
    
    if len(amounts) < 20:  # If less than 20 txns, consider all as high-value
        percentile_95 = min(amounts)
    else:
        # Calculate 95th percentile
        amounts_sorted = sorted(amounts, reverse=True)
        index = max(0, int(len(amounts_sorted) * 0.05) - 1)
        percentile_95 = amounts_sorted[index]
    
    # Filter transactions at or above 95th percentile
    high_value_txns = transactions.filter(
        amount__gte=percentile_95
    ).order_by('-amount')
    
    result = []
    for txn in high_value_txns[:50]:  # Limit to top 50
        result.append({
            'id': txn.id,
            'date': txn.date,
            'description': txn.description,
            'category': txn.category,
            'category_label': txn.get_category_display(),
            'user_label': txn.user_label or '',
            'amount': txn.amount,
            'type': txn.transaction_type,
            'action': 'Review' if txn.transaction_type == 'DEBIT' else 'Confirm',
            'is_manually_edited': txn.is_manually_edited
        })
    
    return result


def analyze_transaction_channels(transactions):
    """
    Analyze transactions by payment channel (UPI, NEFT, CASH, OTHERS).
    
    Identifies channel based on description patterns:
    - UPI: contains 'upi', 'gpay', 'phonepe', 'paytm'
    - NEFT: contains 'neft', 'imps', 'rtgs'
    - CASH: contains 'cash', 'atm', 'withdrawal'
    - OTHERS: default
    
    Returns:
        dict: Channel analysis with counts, percentages, amounts, and risk levels
    """
    if not transactions:
        return {
            'UPI': {'count': 0, 'percentage': 0, 'amount': Decimal('0'), 'risk_level': 'Low'},
            'NEFT': {'count': 0, 'percentage': 0, 'amount': Decimal('0'), 'risk_level': 'Low'},
            'CASH': {'count': 0, 'percentage': 0, 'amount': Decimal('0'), 'risk_level': 'Low'},
            'OTHERS': {'count': 0, 'percentage': 0, 'amount': Decimal('0'), 'risk_level': 'Low'}
        }
    
    total_txns = transactions.count()
    total_amount = transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    channels = {
        'UPI': {'txns': [], 'keywords': ['upi', 'gpay', 'phonepe', 'paytm']},
        'NEFT': {'txns': [], 'keywords': ['neft', 'imps', 'rtgs']},
        'CASH': {'txns': [], 'keywords': ['cash', 'atm', 'withdrawal']},
        'OTHERS': {'txns': []}
    }
    
    # Categorize transactions
    for txn in transactions:
        desc_lower = txn.description.lower()
        matched = False
        
        for channel, config in channels.items():
            if channel == 'OTHERS':
                continue
            
            if any(keyword in desc_lower for keyword in config['keywords']):
                channels[channel]['txns'].append(txn)
                matched = True
                break
        
        if not matched:
            channels['OTHERS']['txns'].append(txn)
    
    # Calculate metrics for each channel
    result = {}
    for channel, data in channels.items():
        channel_txns = data['txns']
        count = len(channel_txns)
        percentage = (count / total_txns * 100) if total_txns > 0 else 0
        amount = sum(txn.amount for txn in channel_txns)
        
        # Calculate risk level based on frequency
        if percentage > 50:
            risk_level = 'High'  # Over-concentrated channel
        elif percentage > 25:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        result[channel] = {
            'count': count,
            'percentage': round(percentage, 1),
            'amount': amount,
            'risk_level': risk_level
        }
    
    return result


def extract_counterparties(transactions):
    """
    Extract counterparties (entities) from transaction descriptions.
    Groups by normalized description to identify frequent counterparties.
    
    Returns:
        list: Counterparties with transaction counts, credit/debit percentages, and risk
    """
    if not transactions:
        return []
    
    # Group transactions by normalized description
    counterparty_groups = defaultdict(list)
    
    for txn in transactions:
        # Normalize description: take first few words or up to first special char
        desc = txn.description.strip()
        # Simple grouping: use first 30 chars of description
        key = desc[:40].lower()
        counterparty_groups[key].append(txn)
    
    # Calculate metrics for each counterparty
    result = []
    total_txns = transactions.count()
    
    for name, txns in counterparty_groups.items():
        count = len(txns)
        
        # Calculate credit/debit percentages
        credits = sum(1 for t in txns if t.transaction_type == 'CREDIT')
        debits = sum(1 for t in txns if t.transaction_type == 'DEBIT')
        
        credit_concentration = (credits / count * 100) if count > 0 else 0
        debit_concentration = (debits / count * 100) if count > 0 else 0
        
        total_amount = sum(txn.amount for txn in txns)
        
        # Calculate risk level based on concentration
        concentration_ratio = (count / total_txns * 100) if total_txns > 0 else 0
        
        if concentration_ratio > 20:
            risk_level = 'High'
        elif concentration_ratio > 10:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        result.append({
            'name': name.title(),
            'count': count,
            'credit_concentration': round(credit_concentration, 1),
            'debit_concentration': round(debit_concentration, 1),
            'total_amount': total_amount,
            'risk_level': risk_level
        })
    
    # Sort by count descending
    result.sort(key=lambda x: x['count'], reverse=True)
    
    return result


def calculate_monthly_risk_analysis(transactions):
    """
    Analyze transactions by month to identify risk patterns.
    
    Returns:
        list: Monthly analysis with credits, debits, net flow, and risk flags
    """
    if not transactions:
        return []
    
    # Group by month
    monthly_data = defaultdict(lambda: {'credits': Decimal('0'), 'debits': Decimal('0'), 'txns': []})
    
    for txn in transactions:
        month_key = txn.date.strftime('%b %Y')
        monthly_data[month_key]['txns'].append(txn)
        
        if txn.transaction_type == 'CREDIT':
            monthly_data[month_key]['credits'] += txn.amount
        else:
            monthly_data[month_key]['debits'] += txn.amount
    
    # Calculate metrics and risk flags
    result = []
    
    for month, data in sorted(monthly_data.items()):
        credits = data['credits']
        debits = data['debits']
        net_flow = credits - debits
        txns = data['txns']
        
        # Identify risk flags
        risk_flags = []
        
        # Flag 1: Unusual credit/debit ratio
        if credits > 0 and debits > 0:
            ratio = debits / credits
            if ratio > 2:
                risk_flags.append('High spending ratio')
            elif ratio < 0.2:
                risk_flags.append('Low spending')
        
        # Flag 2: Large single transaction
        amounts = [t.amount for t in txns]
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            if max_amount > avg_amount * 3:
                risk_flags.append('Unusual large transaction')
        
        # Flag 3: High transaction count
        if len(txns) > 100:
            risk_flags.append('High transaction frequency')
        
        # Determine risk level
        if len(risk_flags) >= 2:
            risk_level = 'High'
        elif len(risk_flags) >= 1:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        result.append({
            'month': month,
            'credits': credits,
            'debits': debits,
            'net_flow': net_flow,
            'risk_level': risk_level,
            'risk_flags': risk_flags
        })
    
    # Sort by date (month key format allows alphabetical sort for recent months)
    return sorted(result, key=lambda x: x['month'])


def calculate_risk_level(transactions):
    """
    Calculate overall risk level for the account based on transaction patterns.
    
    Returns:
        str: Overall risk level ('High', 'Medium', or 'Low')
    """
    if not transactions:
        return 'Low'
    
    # Get all amounts for statistical analysis
    amounts = list(transactions.values_list('amount', flat=True))
    
    if len(amounts) < 3:
        return 'Low'
    
    # Calculate standard deviation
    mean_amount = sum(amounts) / len(amounts)
    variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
    std_dev = variance ** 0.5
    
    # Count outliers (amounts > mean + 2*std_dev)
    outlier_threshold = mean_amount + (2 * std_dev)
    outlier_count = sum(1 for x in amounts if x > outlier_threshold)
    outlier_ratio = outlier_count / len(amounts)
    
    # Risk assessment
    if outlier_ratio > 0.1:  # More than 10% outliers
        return 'High'
    elif outlier_ratio > 0.05:  # More than 5% outliers
        return 'Medium'
    else:
        return 'Low'


def get_audit_report_data(account):
    """
    Get all audit report data for an account.
    This is the main function called by the view.
    
    Args:
        account: BankAccount instance
    
    Returns:
        dict: Complete audit report data
    """
    # Get all transactions for the account
    from .models import Transaction
    
    transactions = Transaction.objects.filter(
        statement__account=account
    ).select_related('statement').order_by('-date')
    
    # Check if no data
    if not transactions.exists():
        return {
            'no_data': True,
            'data_integrity': None,
            'financial_summary': None,
            'high_value_transactions': None,
            'transaction_mix': None,
            'monthly_risks': None,
            'counterparties': None
        }
    
    # Calculate all metrics
    return {
        'no_data': False,
        'data_integrity': calculate_data_integrity(transactions),
        'financial_summary': calculate_financial_summary(transactions),
        'high_value_transactions': identify_high_value_transactions(transactions),
        'transaction_mix': analyze_transaction_channels(transactions),
        'monthly_risks': calculate_monthly_risk_analysis(transactions),
        'counterparties': extract_counterparties(transactions)
    }
