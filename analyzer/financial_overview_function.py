@login_required
def get_financial_overview_data(request):
    """Get financial overview data for different time periods (AJAX endpoint)"""
    time_period = request.GET.get('period', 'all')
    
    # Get all transactions for this user
    all_transactions = Transaction.objects.filter(
        statement__account__user=request.user
    )
    
    # Filter by time period
    now = timezone.now().date()
    if time_period == '30days':
        start_date = now - timedelta(days=30)
        transactions = all_transactions.filter(date__gte=start_date)
    elif time_period == '90days':
        start_date = now - timedelta(days=90)
        transactions = all_transactions.filter(date__gte=start_date)
    else:  # all time
        transactions = all_transactions
    
    # Calculate income and expenses
    total_income = transactions.filter(transaction_type='CREDIT').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    total_expenses = transactions.filter(transaction_type='DEBIT').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    net_savings = total_income - total_expenses
    
    # Calculate percentages correctly
    # Savings rate: percentage of income that is saved (negative if spending exceeds income)
    if total_income > 0:
        savings_rate = (net_savings / total_income) * 100
    else:
        savings_rate = 0 if net_savings == 0 else -100  # All expenses with no income = -100%
    
    # Calculate financial health based on savings rate
    if total_income > 0:
        if savings_rate >= 20:
            health_status = 'Excellent'
            health_score = 85
        elif savings_rate >= 10:
            health_status = 'Good'
            health_score = 70
        elif savings_rate >= 0:
            health_status = 'Needs Attention'
            health_score = 50
        elif savings_rate >= -20:
            health_status = 'Poor'
            health_score = 30
        else:
            health_status = 'Critical'
            health_score = 10
    else:
        health_status = 'No Data'
        health_score = 0
    
    # For percentage displays: show what percentage of income was spent
    # This is more useful for users than showing income vs total
    expense_percentage = (total_expenses / total_income * 100) if total_income > 0 else 0
    income_percentage = 100  # Income is always 100% of itself
    
    return JsonResponse({
        'success': True,
        'income': float(total_income),
        'expenses': float(total_expenses),
        'savings': float(net_savings),
        'income_percentage': round(income_percentage, 1),
        'expense_percentage': round(expense_percentage, 1),
        'health_status': health_status,
        'health_score': health_score,
        'transaction_count': transactions.count(),
        'period': time_period
    })
