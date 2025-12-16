import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from django.contrib import messages
from django.db import transaction as db_transaction
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone

from .models import BankAccount, BankStatement, Transaction, AnalysisSummary, Rule, CustomCategory, CustomCategoryRule, CustomCategoryRuleCondition
from .forms import BankStatementForm
from .rules_forms import RuleForm, RuleConditionFormSet, CustomCategoryForm, CustomCategoryRuleForm, CustomCategoryRuleConditionFormSet
from .rules_engine import RulesEngine, categorize_with_rules
from collections import defaultdict

# Import file parsers with error handling
try:
    from .file_parsers import StatementParser
    FILE_PARSERS_AVAILABLE = True
except ImportError:
    FILE_PARSERS_AVAILABLE = False
    print("Warning: File parsers not available. Install required packages.")

try:
    from .pdf_parser import categorize_transaction
    CATEGORY_PARSER_AVAILABLE = True
except ImportError:
    CATEGORY_PARSER_AVAILABLE = False
    print("Warning: Category parser not available.")

@login_required
def dashboard(request):
    accounts = BankAccount.objects.filter(user=request.user)
    
    # If user has no accounts, create a default one
    if not accounts.exists():
        BankAccount.objects.create(
            user=request.user,
            account_name="Primary Account",
            bank_name="My Bank"
        )
        accounts = BankAccount.objects.filter(user=request.user)
    
    # Get recent transactions and analysis data
    recent_transactions = Transaction.objects.filter(
        statement__account__user=request.user
    ).select_related('statement').order_by('-date')[:10]
    
    # Calculate summary data from all statements
    all_transactions = Transaction.objects.filter(
        statement__account__user=request.user
    )
    
    total_income = all_transactions.filter(transaction_type='CREDIT').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    total_expenses = all_transactions.filter(transaction_type='DEBIT').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    net_savings = total_income - total_expenses
    
    # Get recent statements
    recent_statements = BankStatement.objects.filter(
        account__user=request.user
    ).order_by('-upload_date')[:5]
    
    # Calculate category totals for charts
    category_totals = {}
    expense_transactions = all_transactions.filter(transaction_type='DEBIT')
    
    for category_code, category_name in Transaction.CATEGORY_CHOICES:
        if category_code != 'INCOME':
            category_total = expense_transactions.filter(category=category_code).aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            if category_total > 0:
                category_totals[category_code] = {
                    'name': category_name,
                    'amount': float(category_total),
                    'percentage': 0
                }
    
    # Calculate percentages
    total_expenses_amount = sum(cat['amount'] for cat in category_totals.values())
    for category in category_totals.values():
        if total_expenses_amount > 0:
            category['percentage'] = round((category['amount'] / total_expenses_amount) * 100, 1)
    
    # Financial health score
    if total_income > 0:
        savings_rate = (net_savings / total_income) * 100
        if savings_rate >= 20:
            financial_health = {'score': 85, 'status': 'Excellent', 'message': 'Great savings rate!'}
        elif savings_rate >= 10:
            financial_health = {'score': 70, 'status': 'Good', 'message': 'Solid financial health'}
        else:
            financial_health = {'score': 50, 'status': 'Needs Attention', 'message': 'Consider increasing savings'}
    else:
        financial_health = {'score': 0, 'status': 'No Data', 'message': 'Upload statements to see your financial health'}
    
    context = {
        'accounts': accounts,
        'recent_transactions': recent_transactions,
        'monthly_income': total_income,
        'monthly_expenses': total_expenses,
        'monthly_savings': net_savings,
        'category_totals': category_totals,
        'financial_health': financial_health,
        'recent_statements': recent_statements,
    }
    
    return render(request, 'analyzer/dashboard.html', context)

@login_required
def upload_statement(request):
    """Handle upload of PDF, Excel, and CSV statements"""
    if request.method == 'POST':
        form = BankStatementForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get the account from form
                account = form.cleaned_data['account']
                
                # Check if user owns this account
                if account.user != request.user:
                    messages.error(request, 'You do not have permission to upload to this account.')
                    return redirect('upload_statement')
                
                # Get the filename
                filename = request.FILES['statement_file'].name
                
                # Check for duplicate statement on the same account
                existing_statements = BankStatement.objects.filter(
                    account=account,
                    original_filename=filename
                )
                
                if existing_statements.exists():
                    messages.warning(
                        request,
                        f'⚠️ Warning: A statement with the filename "{filename}" has already been uploaded to this account. '
                        f'Are you sure you want to upload it again? This may create duplicate transactions.'
                    )
                    return redirect('upload_statement')
                
                # Save the statement
                statement = form.save(commit=False)
                statement.original_filename = filename
                
                # Determine file type from filename
                filename = request.FILES['statement_file'].name.lower()
                if filename.endswith('.pdf'):
                    statement.file_type = BankStatement.PDF
                elif filename.endswith(('.xlsx', '.xls')):
                    statement.file_type = BankStatement.EXCEL
                elif filename.endswith('.csv'):
                    statement.file_type = BankStatement.CSV
                
                statement.save()
                
                if not FILE_PARSERS_AVAILABLE:
                    messages.error(request, 
                        'File parsing libraries not installed. '
                        'Please install: pip install pandas openpyxl xlrd pdfplumber'
                    )
                    return redirect('upload_statement')
                
                # Process the uploaded file
                file_path = os.path.join(settings.MEDIA_ROOT, str(statement.statement_file))
                
                try:
                    # Extract transactions
                    transactions_data = StatementParser.parse_file(file_path, statement.file_type)
                    
                    print(f"Extracted {len(transactions_data)} transactions from {statement.file_type} file")
                    
                    # Import UPI parser for better categorization
                    try:
                        from .upi_parser import UPIParser
                        UPI_PARSER_AVAILABLE = True
                    except ImportError:
                        UPI_PARSER_AVAILABLE = False
                    
                    # Create Transaction objects
                    created_count = 0
                    for transaction_data in transactions_data:
                        # Determine category with multiple strategies
                        category = 'OTHER'
                        desc = transaction_data['description'].upper()
                        
                        # Strategy 1: UPI parsing if available
                        if UPI_PARSER_AVAILABLE and UPIParser.is_upi_description(transaction_data['description']):
                            upi_data = UPIParser.parse_upi_fields(transaction_data['description'])
                            if 'purpose' in upi_data:
                                purpose = upi_data['purpose'].upper()
                            else:
                                purpose = desc
                            
                            # Check for keywords in both description and purpose
                            full_text = desc + ' ' + purpose
                            
                            if any(word in full_text for word in ['PURCHASE', 'SHOPPING', 'STORE', 'AMAZON', 'FLIPKART']):
                                category = 'SHOPPING'
                            elif any(word in full_text for word in ['FOOD', 'RESTAURANT', 'PIZZA', 'CAFE', 'ZOMATO']):
                                category = 'FOOD'
                            elif any(word in full_text for word in ['TAXI', 'TRANSPORT', 'METRO', 'CARZONRENT', 'PETROL']):
                                category = 'TRANSPORT'
                            elif any(word in full_text for word in ['MEDICINE', 'HEALTH', 'DENTAL', 'DOCTOR']):
                                category = 'HEALTHCARE'
                            elif any(word in full_text for word in ['TRAVEL', 'HOTEL', 'BOOKING', 'FLIGHT']):
                                category = 'TRAVEL'
                            elif any(word in full_text for word in ['ENTERTAINMENT', 'MOVIE', 'CINEMA']):
                                category = 'ENTERTAINMENT'
                            elif any(word in full_text for word in ['BILL', 'ELECTRICITY', 'INTERNET', 'AIRTEL']):
                                category = 'BILLS'
                        
                        # Strategy 2: Use rules engine if categorization not done
                        if category == 'OTHER':
                            rules_category = categorize_with_rules(transaction_data, request.user)
                            if rules_category:
                                category = rules_category
                        
                        # Strategy 3: Use ML parser if available and still OTHER
                        if category == 'OTHER' and CATEGORY_PARSER_AVAILABLE:
                            ml_category = categorize_transaction(
                                transaction_data['description'],
                                transaction_data['amount'],
                                transaction_data['transaction_type']
                            )
                            if ml_category:
                                category = ml_category
                        
                        Transaction.objects.create(
                            statement=statement,
                            date=transaction_data['date'],
                            description=transaction_data['description'][:500],
                            amount=transaction_data['amount'],
                            transaction_type=transaction_data['transaction_type'],
                            category=category
                        )
                        created_count += 1
                    
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
                    
                    messages.success(request, 
                        f'✅ Successfully uploaded and analyzed {statement.get_file_type_display()} file! '
                        f'Found {created_count} transactions.'
                    )
                    return redirect('statement_rules_prompt', statement_id=statement.id)
                    
                except Exception as e:
                    # If file processing fails, delete the statement and show error
                    statement.delete()
                    error_msg = f'Error processing file: {str(e)}'
                    print(error_msg)
                    messages.error(request, error_msg)
                    return render(request, 'analyzer/upload.html', {'form': form})
                    
            except Exception as e:
                messages.error(request, f'Error saving statement: {str(e)}')
                return render(request, 'analyzer/upload.html', {'form': form})
    else:
        form = BankStatementForm()
        form.fields['account'].queryset = BankAccount.objects.filter(user=request.user)
    
    return render(request, 'analyzer/upload.html', {'form': form})

@login_required
def analysis_results(request, statement_id):
    statement = get_object_or_404(BankStatement, id=statement_id, account__user=request.user)
    transactions = Transaction.objects.filter(statement=statement).order_by('-date')
    
    # Calculate summary data
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'CREDIT')
    total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'DEBIT')
    net_savings = total_income - total_expenses
    
    # Calculate category totals for the chart
    category_totals = {}
    for transaction in transactions.filter(transaction_type='DEBIT'):
        category = transaction.get_category_display()
        category_totals[category] = category_totals.get(category, 0) + float(transaction.amount)
    
    # Comprehensive color palette - unique colors for each category
    color_palette = [
        '#e67e22',  # Orange - Food
        '#9b59b6',  # Purple - Shopping
        '#3498db',  # Blue - Transport
        '#e74c3c',  # Red - Bills
        '#f1c40f',  # Yellow - Entertainment
        '#1abc9c',  # Turquoise
        '#34495e',  # Dark Gray
        '#16a085',  # Green
        '#d35400',  # Dark Orange
        '#8e44ad',  # Dark Purple
        '#c0392b',  # Dark Red
        '#27ae60',  # Green
        '#2980b9',  # Dark Blue
        '#f39c12',  # Golden
        '#95a5a6',  # Gray
    ]
    
    chart_labels = list(category_totals.keys())
    chart_data = list(category_totals.values())
    # Assign unique colors to each category in order
    chart_colors = [color_palette[i % len(color_palette)] for i in range(len(chart_labels))]
    
    # Get analysis summary if exists
    try:
        analysis_summary = AnalysisSummary.objects.get(statement=statement)
    except AnalysisSummary.DoesNotExist:
        analysis_summary = None
    
    # Get user's custom categories
    custom_categories = CustomCategory.objects.filter(user=request.user, is_active=True)
    
    context = {
        'statement': statement,
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_savings': net_savings,
        'category_totals': category_totals,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'chart_colors': chart_colors,
        'analysis_summary': analysis_summary,
        'custom_categories': custom_categories,
    }
    return render(request, 'analyzer/results.html', context)

@login_required
def create_first_account(request):
    if request.method == 'POST':
        account_name = request.POST.get('account_name')
        bank_name = request.POST.get('bank_name')
        
        if account_name:
            account = BankAccount.objects.create(
                user=request.user,
                account_name=account_name,
                bank_name=bank_name or 'My Bank'
            )
            messages.success(request, f'Account "{account_name}" created successfully!')
            return redirect('upload_statement')
    
    return render(request, 'analyzer/create_account.html')


@login_required
def create_account(request):
    """Create a new bank account for the logged-in user (general use)."""
    if request.method == 'POST':
        bank_name = request.POST.get('bank_name')
        account_name = request.POST.get('account_name')
        account_type = request.POST.get('account_type')
        account_number = request.POST.get('account_number')
        ifsc_code = request.POST.get('ifsc_code')
        description = request.POST.get('description')

        if bank_name:
            BankAccount.objects.create(
                user=request.user,
                bank_name=bank_name,
                account_name=account_name or bank_name,
                account_type=account_type,
                account_number=account_number,
                ifsc_code=ifsc_code,
                description=description
            )
            messages.success(request, f'Account "{bank_name}" created successfully!')
            return redirect('dashboard')

    return render(request, 'analyzer/create_account.html')

# ===========================================
# RULES ENGINE VIEWS
# ===========================================

@login_required
def rules_list(request):
    """List all rules"""
    rules = Rule.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'analyzer/rules_list.html', {'rules': rules})

@login_required
def create_rule(request):
    """Create a new rule"""
    if request.method == 'POST':
        form = RuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.user = request.user
            rule.save()
            messages.success(request, f'Rule "{rule.name}" created successfully!')
            return redirect('edit_rule', rule_id=rule.id)
    else:
        form = RuleForm()
    
    return render(request, 'analyzer/create_rule.html', {'form': form})

@login_required
def edit_rule(request, rule_id):
    """Edit an existing rule"""
    rule = get_object_or_404(Rule, id=rule_id, user=request.user)
    
    if request.method == 'POST':
        form = RuleForm(request.POST, instance=rule)
        formset = RuleConditionFormSet(request.POST, instance=rule)
        
        if form.is_valid() and formset.is_valid():
            try:
                form.save()
                formset.save()
                messages.success(request, f'Rule "{rule.name}" updated successfully!')
                return redirect('rules_list')
            except Exception as e:
                messages.error(request, f'Error saving rule: {str(e)}')
        else:
            # Form validation failed
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            for formset_error in formset.non_form_errors():
                error_messages.append(formset_error)
            
            if error_messages:
                messages.error(request, 'Please correct the errors: ' + '; '.join(error_messages))
    else:
        form = RuleForm(instance=rule)
        formset = RuleConditionFormSet(instance=rule)
    
    return render(request, 'analyzer/edit_rule.html', {
        'form': form,
        'formset': formset,
        'rule': rule
    })

@login_required
def delete_rule(request, rule_id):
    """Delete a rule"""
    rule = get_object_or_404(Rule, id=rule_id, user=request.user)
    if request.method == 'POST':
        rule_name = rule.name
        rule.delete()
        messages.success(request, f'Rule "{rule_name}" deleted successfully!')
        return redirect('rules_list')
    
    return render(request, 'analyzer/delete_rule.html', {'rule': rule})

@login_required
def apply_rules(request):
    """Apply rules to existing transactions"""
    # Get stats for display
    active_rules_count = Rule.objects.filter(user=request.user, is_active=True).count()
    total_transactions = Transaction.objects.filter(
        statement__account__user=request.user
    ).count()
    
    if request.method == 'POST':
        # Support account-scoped application: an optional account_id can be passed
        account_id = request.POST.get('account_id') or request.GET.get('account_id')

        # Support AJAX requests so the frontend can stop the spinner and show results
        engine = RulesEngine(request.user)
        if account_id:
            transactions = Transaction.objects.filter(
                statement__account__user=request.user,
                statement__account_id=account_id
            )
        else:
            transactions = Transaction.objects.filter(
                statement__account__user=request.user
            )

        updated_count = 0
        updated_ids = []
        prev_map = {}
        matched_map = {}
        with db_transaction.atomic():
            for transaction in transactions:
                transaction_data = {
                    'date': transaction.date,
                    'description': transaction.description,
                    'amount': float(transaction.amount),
                    'transaction_type': transaction.transaction_type
                }

                # Determine which rule (if any) matches and the target category
                matched_rule = engine.find_matching_rule(transaction_data)
                category = matched_rule.category if matched_rule else None

                if category and category != transaction.category:
                    # record previous category so we can show changes
                    prev_map[str(transaction.id)] = transaction.category
                    # record which rule matched
                    matched_map[str(transaction.id)] = matched_rule.name if matched_rule else None
                    transaction.category = category
                    transaction.save()
                    updated_count += 1
                    updated_ids.append(transaction.id)

        # If AJAX request, return JSON so JS can stop spinner and update UI
        # Store list of updated ids and previous categories in session so results view can show only changed
        if updated_ids:
            request.session['last_rules_applied_ids'] = updated_ids
            request.session['last_rules_applied_prev'] = prev_map
            request.session['last_rules_applied_rule'] = matched_map
        else:
            # clear previous session keys if nothing changed
            request.session.pop('last_rules_applied_ids', None)
            request.session.pop('last_rules_applied_prev', None)
            request.session.pop('last_rules_applied_rule', None)

        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            redirect_url = reverse('rules_application_results')
            sep = '?'
            if account_id:
                redirect_url += f'?account_id={account_id}'
                sep = '&'
            # instruct results page to show only changed transactions
            redirect_url += f"{sep}show_changed=1"
            return JsonResponse({
                'status': 'ok',
                'updated': updated_count,
                'total': transactions.count(),
                'message': f'Rules applied successfully! Updated {updated_count} out of {transactions.count()} transactions.',
                'redirect_url': redirect_url,
            })

        messages.success(request,
            f'Rules applied successfully! Updated {updated_count} out of {transactions.count()} transactions.'
        )
        return redirect('rules_list')
    
    # Provide accounts for the selector
    accounts = BankAccount.objects.filter(user=request.user)

    return render(request, 'analyzer/apply_rules.html', {
        'active_rules_count': active_rules_count,
        'total_transactions': total_transactions,
        'accounts': accounts,
    })

@login_required
def test_rules(request):
    """Test rules against sample transactions"""
    if request.method == 'POST':
        test_description = request.POST.get('description', '').strip()
        test_amount_str = request.POST.get('amount', '0')
        test_date = request.POST.get('date', '')
        
        # Validate amount
        try:
            test_amount = float(test_amount_str)
        except ValueError:
            test_amount = 0
        
        transaction_data = {
            'description': test_description,
            'amount': test_amount,
            'date': test_date,
            'transaction_type': 'DEBIT' if test_amount < 0 else 'CREDIT'
        }
        
        engine = RulesEngine(request.user)
        matching_rules = []
        
        for rule in engine.rules:
            if engine._matches_rule(transaction_data, rule):
                matching_rules.append(rule)
        
        return render(request, 'analyzer/test_rules.html', {
            'test_description': test_description,
            'test_amount': test_amount,
            'test_date': test_date,
            'matching_rules': matching_rules,
            'transaction_data': transaction_data
        })
    
    return render(request, 'analyzer/test_rules.html')


@login_required
def rules_application_results(request):
    """Show which rule (if any) and custom category (if any) matches each transaction. Supports optional account filter."""
    account_id = request.GET.get('account_id')
    show_changed = request.GET.get('show_changed') in ['1', 'true', 'True']
    engine = RulesEngine(request.user)
    
    # Import custom category engine
    from .rules_engine import CustomCategoryRulesEngine
    custom_category_engine = CustomCategoryRulesEngine(request.user)
    
    # If show_changed requested, read the list of ids from session (set by apply_rules)
    if show_changed:
        updated_ids = request.session.get('last_rules_applied_ids', [])
        # ensure we only fetch transactions belonging to this user (and optional account)
        if account_id:
            transactions = Transaction.objects.filter(
                id__in=updated_ids,
                statement__account__user=request.user,
                statement__account_id=account_id
            ).select_related('statement', 'statement__account').order_by('-date')
        else:
            transactions = Transaction.objects.filter(
                id__in=updated_ids,
                statement__account__user=request.user
            ).select_related('statement', 'statement__account').order_by('-date')
    else:
        if account_id:
            transactions = Transaction.objects.filter(
                statement__account__user=request.user,
                statement__account_id=account_id
            ).select_related('statement', 'statement__account').order_by('-date')
        else:
            transactions = Transaction.objects.filter(
                statement__account__user=request.user
            ).select_related('statement', 'statement__account').order_by('-date')

    results = []
    for tx in transactions:
        tx_data = {
            'date': tx.date,
            'description': tx.description,
            'amount': float(tx.amount),
            'transaction_type': tx.transaction_type
        }
        
        # Check for rule match
        matched_rule = engine.find_matching_rule(tx_data)
        matched_rule_category = matched_rule.category if matched_rule else None
        matched_rule_name = matched_rule.name if matched_rule else None
        
        # Check for custom category match
        matched_custom_category = custom_category_engine.apply_rules_to_transaction(tx_data)
        matched_custom_category_name = matched_custom_category.name if matched_custom_category else None
        
        # Only include if there's a match (rule or custom category)
        if matched_rule_name or matched_custom_category_name:
            results.append({
                'id': tx.id,
                'date': tx.date,
                'description': tx.description,
                'amount': tx.amount,
                'current_category': tx.category,
                'matched_rule_category': matched_rule_category,
                'matched_rule_name': matched_rule_name,
                'matched_custom_category_name': matched_custom_category_name,
                'previous_category': request.session.get('last_rules_applied_prev', {}).get(str(tx.id)) if show_changed else None,
                'account_name': tx.statement.account.account_name,
                'account_id': tx.statement.account.id,
            })

    # Get list of user's accounts for selector
    accounts = BankAccount.objects.filter(user=request.user)
    no_changes = show_changed and len(results) == 0

    # Compute totals per matched rule/category (always compute if there are results)
    rule_totals = []
    if results:
        totals = {}
        counts = {}
        for r in results:
            # Prefer custom category, then rule, then unmatched
            matched_name = r.get('matched_custom_category_name') or r.get('matched_rule_name') or 'Unmatched'
            amt = float(r.get('amount') or 0)
            totals[matched_name] = totals.get(matched_name, 0.0) + amt
            counts[matched_name] = counts.get(matched_name, 0) + 1
        # Build list sorted by total desc
        rule_totals = [
            {'rule_name': name, 'total': totals[name], 'count': counts[name]}
            for name in sorted(totals.keys(), key=lambda k: totals[k], reverse=True)
        ]

    # compute colspan for template (base 7 columns + previous column if show_changed)
    colspan = 7 + (1 if show_changed else 0)

    # Get user's custom categories
    custom_categories = CustomCategory.objects.filter(user=request.user, is_active=True)

    return render(request, 'analyzer/apply_rules_results.html', {
        'results': results,
        'accounts': accounts,
        'selected_account_id': int(account_id) if account_id else None,
        'show_changed': show_changed,
        'no_changes': no_changes,
        'rule_totals': rule_totals,
        'colspan': colspan,
        'custom_categories': custom_categories,
    })


@login_required
def rules_categorized(request):
    """Show rules grouped by category for the current user."""
    user_rules = Rule.objects.filter(user=request.user).order_by('category', '-created_at')
    grouped = defaultdict(list)
    for rule in user_rules:
        grouped[rule.get_category_display()].append(rule)

    # Convert to list of tuples for template ordering
    grouped_list = [(category, grouped[category]) for category in sorted(grouped.keys())]

    return render(request, 'analyzer/rules_categorized.html', {
        'grouped_rules': grouped_list,
    })

@login_required
def bulk_delete_transactions(request, statement_id=None):
    """Bulk delete transactions (for cleanup)"""
    if request.method == 'POST':
        if statement_id:
            # Delete transactions for specific statement
            transactions = Transaction.objects.filter(
                statement_id=statement_id,
                statement__account__user=request.user
            )
            statement = get_object_or_404(BankStatement, id=statement_id, account__user=request.user)
            count = transactions.count()
            transactions.delete()
            messages.success(request, f'Deleted {count} transactions from statement.')
            return redirect('dashboard')
        else:
            # Delete all user's transactions
            transactions = Transaction.objects.filter(
                statement__account__user=request.user
            )
            count = transactions.count()
            transactions.delete()
            messages.success(request, f'Deleted all {count} transactions.')
            return redirect('dashboard')
    
    if statement_id:
        statement = get_object_or_404(BankStatement, id=statement_id, account__user=request.user)
        return render(request, 'analyzer/confirm_delete.html', {
            'statement': statement,
            'object_type': 'transactions'
        })
    else:
        return render(request, 'analyzer/confirm_delete.html', {
            'object_type': 'all transactions'
        })

@login_required
def statement_rules_prompt(request, statement_id):
    """Show prompt to apply global rules to a statement"""
    statement = get_object_or_404(BankStatement, id=statement_id, account__user=request.user)
    
    # Check if statement already has rules applied
    if statement.rules_applied:
        return redirect('analysis_results', statement_id=statement_id)
    
    # Count active rules
    active_rules_count = Rule.objects.filter(user=request.user, is_active=True).count()
    
    if request.method == 'POST':
        apply_rules_choice = request.POST.get('apply_rules')
        
        if apply_rules_choice == 'yes':
            # Apply global rules to this statement
            transactions = Transaction.objects.filter(statement=statement)
            engine = RulesEngine(request.user)
            updated_count = 0
            
            with db_transaction.atomic():
                for transaction in transactions:
                    transaction_data = {
                        'date': transaction.date,
                        'description': transaction.description,
                        'amount': float(transaction.amount),
                        'transaction_type': transaction.transaction_type
                    }
                    
                    matched_rule = engine.find_matching_rule(transaction_data)
                    if matched_rule and matched_rule.category != transaction.category:
                        transaction.category = matched_rule.category
                        transaction.save()
                        updated_count += 1
            
            statement.rules_applied = True
            statement.save()
            
            messages.success(request, 
                f'✅ Applied global rules! Updated {updated_count} transaction(s).')
        else:
            # Mark as reviewed without applying rules
            statement.rules_applied = True
            statement.save()
            messages.info(request, 'Proceeding without applying global rules.')
        
        return redirect('analysis_results', statement_id=statement_id)
    
    context = {
        'statement': statement,
        'active_rules_count': active_rules_count,
    }
    return render(request, 'analyzer/statement_rules_prompt.html', context)

@login_required
def toggle_rule_active(request):
    """AJAX endpoint to toggle rule active status"""
    if request.method == 'POST' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        rule_id = request.POST.get('rule_id')
        try:
            rule = Rule.objects.get(id=rule_id, user=request.user)
            rule.is_active = not rule.is_active
            rule.save()
            return JsonResponse({
                'success': True,
                'is_active': rule.is_active,
                'message': f'Rule "{rule.name}" is now {"active" if rule.is_active else "inactive"}.'
            })
        except Rule.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Rule not found.'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)


@login_required
def view_account_details(request, account_id):
    """View account-specific financial overview"""
    account = get_object_or_404(BankAccount, id=account_id, user=request.user)
    
    # Get transactions for this account only
    account_transactions = Transaction.objects.filter(
        statement__account=account
    ).select_related('statement').order_by('-date')
    
    recent_transactions = account_transactions[:15]
    
    # Calculate summary data for this account only
    total_income = account_transactions.filter(transaction_type='CREDIT').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    total_expenses = account_transactions.filter(transaction_type='DEBIT').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    net_savings = total_income - total_expenses
    
    # Calculate category totals for charts
    category_totals = {}
    expense_transactions = account_transactions.filter(transaction_type='DEBIT')
    
    for category_code, category_name in Transaction.CATEGORY_CHOICES:
        if category_code != 'INCOME':
            category_total = expense_transactions.filter(category=category_code).aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            if category_total > 0:
                category_totals[category_code] = {
                    'name': category_name,
                    'amount': float(category_total),
                    'percentage': 0
                }
    
    # Calculate percentages
    total_expenses_amount = sum(cat['amount'] for cat in category_totals.values())
    for category in category_totals.values():
        if total_expenses_amount > 0:
            category['percentage'] = round((category['amount'] / total_expenses_amount) * 100, 1)
    
    # Financial health score
    if total_income > 0:
        savings_rate = (net_savings / total_income) * 100
        if savings_rate >= 20:
            financial_health = {'score': 85, 'status': 'Excellent', 'message': 'Great savings rate!'}
        elif savings_rate >= 10:
            financial_health = {'score': 70, 'status': 'Good', 'message': 'Solid financial health'}
        else:
            financial_health = {'score': 50, 'status': 'Needs Attention', 'message': 'Consider increasing savings'}
    else:
        financial_health = {'score': 0, 'status': 'No Data', 'message': 'No transactions for this account'}
    
    context = {
        'account': account,
        'transactions': account_transactions,
        'recent_transactions': recent_transactions,
        'monthly_income': total_income,
        'monthly_expenses': total_expenses,
        'monthly_savings': net_savings,
        'category_totals': category_totals,
        'financial_health': financial_health,
    }
    
    return render(request, 'analyzer/account_details.html', context)


@login_required
def delete_account(request, account_id):
    """Delete a bank account"""
    account = get_object_or_404(BankAccount, id=account_id, user=request.user)
    
    if request.method == 'POST':
        account_name = account.account_name
        account.delete()
        messages.success(request, f'Account "{account_name}" has been deleted successfully.')
        return redirect('dashboard')
    
    # Show confirmation page for GET
    context = {'account': account}
    return render(request, 'analyzer/delete_account.html', context)


@login_required
def change_rule_status_on_results(request):
    """Toggle rule active status from results page (AJAX endpoint)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        rule_id = request.POST.get('rule_id')
        
        try:
            rule = Rule.objects.get(id=rule_id)
            rule.is_active = not rule.is_active
            rule.save()
            return JsonResponse({
                'success': True,
                'is_active': rule.is_active,
                'message': f'Rule is now {"active" if rule.is_active else "inactive"}.'
            })
        except Rule.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Rule not found.'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)


# ============= CUSTOM CATEGORY VIEWS =============

@login_required
def create_custom_category_and_rule(request):
    """Create a custom category and its rule in one interface"""
    if request.method == 'POST':
        category_form = CustomCategoryForm(request.POST)
        
        if category_form.is_valid():
            # Save custom category
            custom_category = category_form.save(commit=False)
            custom_category.user = request.user
            custom_category.save()
            
            # Redirect to create rule for this category
            messages.success(request, f'Custom category "{custom_category.name}" created successfully!')
            return redirect('create_custom_category_rule', category_id=custom_category.id)
    else:
        category_form = CustomCategoryForm()
    
    context = {
        'form': category_form,
        'page_title': 'Create Custom Category',
        'step': 1,
        'step_title': 'Step 1: Create Custom Category'
    }
    return render(request, 'analyzer/create_custom_category.html', context)


@login_required
def create_custom_category_rule(request, category_id):
    """Create a rule for a custom category"""
    custom_category = get_object_or_404(CustomCategory, id=category_id, user=request.user)
    
    if request.method == 'POST':
        rule_form = CustomCategoryRuleForm(request.POST)
        
        if rule_form.is_valid():
            with db_transaction.atomic():
                # Save rule first
                rule = rule_form.save(commit=False)
                rule.user = request.user
                rule.custom_category = custom_category
                rule.save()
                
                # Now bind the formset to the saved rule
                condition_formset = CustomCategoryRuleConditionFormSet(request.POST, instance=rule)
                
                if condition_formset.is_valid():
                    # Save conditions
                    condition_formset.save()
                    messages.success(request, f'Rule "{rule.name}" created successfully for "{custom_category.name}"!')
                    return redirect('custom_categories_list')
                else:
                    # If formset is invalid, delete the rule and redisplay the form with errors
                    rule.delete()
        else:
            condition_formset = CustomCategoryRuleConditionFormSet()
    else:
        rule_form = CustomCategoryRuleForm()
        condition_formset = CustomCategoryRuleConditionFormSet()
    
    context = {
        'custom_category': custom_category,
        'rule_form': rule_form,
        'condition_formset': condition_formset,
        'page_title': f'Create Rule for {custom_category.name}',
        'step': 2,
        'step_title': 'Step 2: Create Category Rule'
    }
    return render(request, 'analyzer/create_custom_category_rule.html', context)


@login_required
def custom_categories_list(request):
    """List all custom categories for the user"""
    custom_categories = CustomCategory.objects.filter(user=request.user).prefetch_related('rules')
    
    context = {
        'custom_categories': custom_categories,
        'page_title': 'My Custom Categories'
    }
    return render(request, 'analyzer/custom_categories_list.html', context)


@login_required
def edit_custom_category_rule(request, rule_id):
    """Edit a custom category rule"""
    rule = get_object_or_404(CustomCategoryRule, id=rule_id, user=request.user)
    
    if request.method == 'POST':
        rule_form = CustomCategoryRuleForm(request.POST, instance=rule)
        condition_formset = CustomCategoryRuleConditionFormSet(request.POST, instance=rule)
        
        if rule_form.is_valid() and condition_formset.is_valid():
            with db_transaction.atomic():
                rule_form.save()
                condition_formset.save()
                
                messages.success(request, f'Rule "{rule.name}" updated successfully!')
                return redirect('custom_categories_list')
    else:
        rule_form = CustomCategoryRuleForm(instance=rule)
        condition_formset = CustomCategoryRuleConditionFormSet(instance=rule)
    
    context = {
        'custom_category': rule.custom_category,
        'rule': rule,
        'rule_form': rule_form,
        'condition_formset': condition_formset,
        'page_title': f'Edit Rule: {rule.name}',
        'is_edit': True
    }
    return render(request, 'analyzer/create_custom_category_rule.html', context)


@login_required
def delete_custom_category_rule(request, rule_id):
    """Delete a custom category rule"""
    rule = get_object_or_404(CustomCategoryRule, id=rule_id, user=request.user)
    category_name = rule.custom_category.name
    
    if request.method == 'POST':
        rule.delete()
        messages.success(request, f'Rule deleted successfully!')
        return redirect('custom_categories_list')
    
    context = {
        'rule': rule,
        'page_title': 'Delete Rule'
    }
    return render(request, 'analyzer/delete_custom_category_rule.html', context)


@login_required
def delete_custom_category(request, category_id):
    """Delete a custom category"""
    custom_category = get_object_or_404(CustomCategory, id=category_id, user=request.user)
    
    if request.method == 'POST':
        category_name = custom_category.name
        custom_category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('custom_categories_list')
    
    context = {
        'custom_category': custom_category,
        'page_title': 'Delete Custom Category'
    }
    return render(request, 'analyzer/delete_custom_category.html', context)


@login_required
def apply_custom_category(request, statement_id):
    """Apply multiple custom categories to transactions in a statement"""
    if request.method == 'POST':
        category_ids = request.POST.getlist('category_ids')
        
        if not category_ids:
            return JsonResponse({
                'success': False,
                'message': 'Please select at least one category to apply.',
                'matched_transaction_ids': []
            })
        
        try:
            statement = get_object_or_404(BankStatement, id=statement_id, account__user=request.user)
            
            # Get all selected custom categories
            custom_categories = CustomCategory.objects.filter(
                id__in=category_ids,
                user=request.user
            )
            
            if not custom_categories.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'No categories found.',
                    'matched_transaction_ids': []
                })
            
            # Apply rules to transactions
            from .rules_engine import CustomCategoryRulesEngine
            engine = CustomCategoryRulesEngine(request.user)
            
            transactions = Transaction.objects.filter(statement=statement)
            matched_transaction_ids = []
            category_names = []
            category_colors = []
            
            for category in custom_categories:
                category_names.append(category.name)
                category_colors.append(category.color)
                
                # Get the rules for this custom category
                rules = CustomCategoryRule.objects.filter(custom_category=category, is_active=True)
                
                if not rules.exists():
                    continue
                
                for transaction in transactions:
                    transaction_data = {
                        'description': transaction.description,
                        'amount': transaction.amount,
                        'date': transaction.date
                    }
                    
                    # Check if transaction matches the custom category rules
                    matching_category = engine.apply_rules_to_transaction(transaction_data)
                    
                    # Only apply if the matching category is our selected category
                    if matching_category and matching_category.id == category.id:
                        if transaction.id not in matched_transaction_ids:
                            matched_transaction_ids.append(transaction.id)
            
            if matched_transaction_ids:
                return JsonResponse({
                    'success': True,
                    'message': f'Applied {len(custom_categories)} categor{"ies" if len(custom_categories) > 1 else "y"} to {len(matched_transaction_ids)} matching transactions.',
                    'category_names': category_names,
                    'category_colors': category_colors,
                    'matched_transaction_ids': matched_transaction_ids,
                    'applied_count': len(matched_transaction_ids)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'No transactions matched the rules for the selected categor{"ies" if len(custom_categories) > 1 else "y"}.',
                    'matched_transaction_ids': []
                })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}',
                'matched_transaction_ids': []
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.',
        'matched_transaction_ids': []
    })


@login_required
def apply_custom_category_rules(request):
    """Apply multiple custom categories to transactions from rule application results"""
    if request.method == 'POST':
        category_ids = request.POST.getlist('category_ids')
        
        if not category_ids:
            return JsonResponse({
                'success': False,
                'message': 'Please select at least one category to apply.',
                'matched_transaction_ids': []
            })
        
        try:
            # Get all selected custom categories with their rules and conditions
            custom_categories = CustomCategory.objects.filter(
                id__in=category_ids,
                user=request.user
            ).prefetch_related('rules__conditions')
            
            if not custom_categories.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'No categories found for your account.',
                    'matched_transaction_ids': []
                })
            
            # Import the engine
            from .rules_engine import CustomCategoryRulesEngine
            
            # Get all transactions for this user
            transactions = Transaction.objects.filter(
                statement__account__user=request.user
            )
            
            if not transactions.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'No transactions found in your account.',
                    'matched_transaction_ids': []
                })
            
            matched_transaction_ids = []
            category_names = []
            category_colors = []
            
            for category in custom_categories:
                category_names.append(category.name)
                category_colors.append(category.color)
                
                # Get the active rules for this custom category (from prefetched data)
                active_rules = [rule for rule in category.rules.all() if rule.is_active]
                
                if not active_rules:
                    # No active rules for this category, skip it
                    continue
                
                for transaction in transactions:
                    transaction_data = {
                        'description': transaction.description,
                        'amount': float(transaction.amount),
                        'date': transaction.date
                    }
                    
                    # Check if transaction matches ANY of this category's rules
                    matches_category = False
                    for rule in active_rules:
                        # Get all conditions for this rule
                        conditions = list(rule.conditions.all())
                        
                        if not conditions:
                            # If rule has no conditions, skip it
                            continue
                        
                        if CustomCategoryRulesEngine._matches_rule_static(transaction_data, rule):
                            matches_category = True
                            break
                    
                    if matches_category:
                        if transaction.id not in matched_transaction_ids:
                            matched_transaction_ids.append(transaction.id)
            
            if matched_transaction_ids:
                return JsonResponse({
                    'success': True,
                    'message': f'Applied {len(custom_categories)} categor{"ies" if len(custom_categories) > 1 else "y"} to {len(matched_transaction_ids)} matching transactions.',
                    'category_names': category_names,
                    'category_colors': category_colors,
                    'matched_transaction_ids': matched_transaction_ids,
                    'applied_count': len(matched_transaction_ids)
                })
            else:
                # Check if we have any categories with active rules
                categories_with_rules = [cat for cat in custom_categories if any(r.is_active for r in cat.rules.all())]
                
                if not categories_with_rules:
                    return JsonResponse({
                        'success': False,
                        'message': 'Selected categories have no active rules. Please activate the rules first.',
                        'matched_transaction_ids': []
                    })
                
                return JsonResponse({
                    'success': False,
                    'message': f'No transactions matched the rules for the selected categor{"ies" if len(custom_categories) > 1 else "y"}.',
                    'matched_transaction_ids': []
                })
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error in apply_custom_category_rules: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}',
                'matched_transaction_ids': []
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.',
        'matched_transaction_ids': []
    })


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
    
    # Calculate percentages
    total_all = total_income + total_expenses
    income_percentage = (total_income / total_all * 100) if total_all > 0 else 0
    expense_percentage = (total_expenses / total_all * 100) if total_all > 0 else 0
    
    # Calculate financial health
    if total_income > 0:
        savings_rate = (net_savings / total_income) * 100
        if savings_rate >= 20:
            health_status = 'Excellent'
            health_score = 85
        elif savings_rate >= 10:
            health_status = 'Good'
            health_score = 70
        else:
            health_status = 'Needs Attention'
            health_score = 50
    else:
        health_status = 'No Data'
        health_score = 0
    
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


@login_required
def export_rules_results_to_excel(request):
    """Export rule application results to Excel file - only table data, no page content"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        messages.error(request, 'Excel export not available. Please install openpyxl.')
        return redirect('rules_application_results')
    
    try:
        # Get query parameters
        account_id = request.GET.get('account_id', '')
        show_changed = request.GET.get('show_changed', '') == '1'
        transaction_ids = request.GET.getlist('transaction_ids')
        
        # If specific transaction IDs provided, use only those (filtered results)
        if transaction_ids:
            all_transactions = Transaction.objects.filter(
                id__in=transaction_ids,
                statement__account__user=request.user
            ).select_related('statement').order_by('-date')
        else:
            # Fallback: Get all transactions for the account
            all_transactions = Transaction.objects.filter(
                statement__account__user=request.user
            ).select_related('statement').order_by('-date')
            
            # Filter by account if specified
            if account_id:
                try:
                    account = BankAccount.objects.get(id=account_id, user=request.user)
                    all_transactions = all_transactions.filter(statement__account=account)
                except BankAccount.DoesNotExist:
                    pass
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = 'Results'
        
        # Define styles
        header_fill = PatternFill(start_color='0D47A1', end_color='0D47A1', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF', size=11)
        border = Border(
            left=Side(style='thin', color='D3D3D3'),
            right=Side(style='thin', color='D3D3D3'),
            top=Side(style='thin', color='D3D3D3'),
            bottom=Side(style='thin', color='D3D3D3')
        )
        center_align = Alignment(horizontal='center', vertical='center')
        left_align = Alignment(horizontal='left', vertical='center')
        
        # Prepare headers based on whether show_changed is enabled
        if show_changed:
            headers = ['Date', 'Account', 'Description', 'Amount', 'Previous Category', 'Current Category', 'Matched Rule', 'Custom Category']
            column_widths = [12, 18, 40, 12, 18, 18, 20, 18]
        else:
            headers = ['Date', 'Account', 'Description', 'Amount', 'Category', 'Matched Rule', 'Custom Category']
            column_widths = [12, 18, 40, 12, 18, 20, 18]
        
        # Add headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border
            cell.alignment = center_align
        
        # Add transaction data
        row_num = 2
        for transaction in all_transactions:
            col_num = 1
            
            # Date
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = transaction.date.strftime('%Y-%m-%d') if transaction.date else ''
            cell.border = border
            cell.alignment = center_align
            col_num += 1
            
            # Account
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = transaction.statement.account.account_name if transaction.statement else ''
            cell.border = border
            cell.alignment = left_align
            col_num += 1
            
            # Description
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = transaction.description
            cell.border = border
            cell.alignment = left_align
            col_num += 1
            
            # Amount
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = float(transaction.amount) if transaction.amount else 0
            cell.border = border
            cell.number_format = '#,##0.00'
            cell.alignment = center_align
            col_num += 1
            
            if show_changed:
                # Previous Category (from session data)
                cell = ws.cell(row=row_num, column=col_num)
                # This would need to be passed from the view
                cell.value = '-'
                cell.border = border
                cell.alignment = left_align
                col_num += 1
            
            # Current Category
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = transaction.get_category_display()
            cell.border = border
            cell.alignment = left_align
            col_num += 1
            
            # Matched Rule (check if category was matched by any rule)
            matched_rule = '-'
            rules = Rule.objects.filter(user=request.user, is_active=True).order_by('name')
            for rule in rules:
                if rule.category == transaction.category:
                    matched_rule = rule.name
                    break
            
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = matched_rule
            cell.border = border
            cell.alignment = left_align
            col_num += 1
            
            # Custom Category
            cell = ws.cell(row=row_num, column=col_num)
            custom_cat = transaction.custom_category.name if transaction.custom_category else '-'
            cell.value = custom_cat
            cell.border = border
            cell.alignment = left_align
            
            row_num += 1
        
        # Adjust column widths
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = width
        
        # Freeze header row
        ws.freeze_panes = 'A2'
        
        # Create HTTP response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="rule_results.xlsx"'
        
        # Save workbook to response
        wb.save(response)
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting results: {str(e)}')
        return redirect('rules_application_results')
