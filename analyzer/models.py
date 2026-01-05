from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=100)
    account_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.account_name} - {self.bank_name}"
    
    def get_balance(self):
        # Import here to avoid circular import
        from .models import Transaction
        transactions = Transaction.objects.filter(statement__account=self)
        income = transactions.filter(transaction_type='CREDIT').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        expenses = transactions.filter(transaction_type='DEBIT').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        return income - expenses

class BankStatement(models.Model):
    # File types - defined as class constants
    PDF = 'PDF'
    EXCEL = 'EXCEL'
    CSV = 'CSV'
    FILE_TYPE_CHOICES = [
        (PDF, 'PDF Document'),
        (EXCEL, 'Excel Spreadsheet'),
        (CSV, 'CSV File'),
    ]
    
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    statement_file = models.FileField(upload_to='statements/', null=True, blank=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default=PDF)
    upload_date = models.DateTimeField(auto_now_add=True)
    statement_period_start = models.DateField(null=True, blank=True)
    statement_period_end = models.DateField(null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    rules_applied = models.BooleanField(default=False)  # Track if global rules have been applied
    
    def __str__(self):
        return f"Statement for {self.account.account_name} - {self.upload_date}"
    
    def clean(self):
        """Validate file type"""
        if self.statement_file:
            filename = self.statement_file.name.lower()
            if filename.endswith('.pdf'):
                self.file_type = self.PDF
            elif filename.endswith(('.xlsx', '.xls')):
                self.file_type = self.EXCEL
            elif filename.endswith('.csv'):
                self.file_type = self.CSV
            else:
                raise ValidationError('Unsupported file type. Please upload PDF, Excel, or CSV files.')

class Transaction(models.Model):
    CATEGORY_CHOICES = [
        ('INCOME', 'Income'),
        ('FOOD', 'Food & Dining'),
        ('SHOPPING', 'Shopping'),
        ('BILLS', 'Bills & Utilities'),
        ('TRANSPORT', 'Transportation'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('HEALTHCARE', 'Healthcare'),
        ('LOAN', 'Loan & EMI'),
        ('TRAVEL', 'Travel'),
        ('OTHER', 'Other'),
    ]
    
    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('DEBIT', 'Debit'), ('CREDIT', 'Credit')])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    # User-assigned label/subcategory for manual overrides
    user_label = models.CharField(max_length=100, blank=True, null=True, help_text="User-assigned label or subcategory")
    # Flag to track if user has manually edited this transaction
    is_manually_edited = models.BooleanField(default=False)
    # User who last edited this transaction
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_transactions')
    # Timestamp of last edit
    last_edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.date} - {self.description} - {self.amount}"
    
    def get_category_icon(self):
        icons = {
            'INCOME': 'fa-money-bill-wave',
            'FOOD': 'fa-utensils',
            'SHOPPING': 'fa-shopping-bag',
            'BILLS': 'fa-file-invoice',
            'TRANSPORT': 'fa-car',
            'ENTERTAINMENT': 'fa-film',
            'HEALTHCARE': 'fa-heartbeat',
            'LOAN': 'fa-hand-holding-usd',
            'TRAVEL': 'fa-plane',
            'OTHER': 'fa-circle'
        }
        return icons.get(self.category, 'fa-circle')
    
    def get_category_color(self):
        colors = {
            'INCOME': '#27ae60',
            'FOOD': '#e67e22',
            'SHOPPING': '#9b59b6',
            'BILLS': '#e74c3c',
            'TRANSPORT': '#3498db',
            'ENTERTAINMENT': '#f1c40f',
            'HEALTHCARE': '#e74c3c',
            'LOAN': '#34495e',
            'TRAVEL': '#1abc9c',
            'OTHER': '#95a5a6'
        }
        return colors.get(self.category, '#95a5a6')

class AnalysisSummary(models.Model):
    statement = models.OneToOneField(BankStatement, on_delete=models.CASCADE)
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    analysis_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Summary for {self.statement}"

# RULES ENGINE MODELS (keep as before)
class Rule(models.Model):
    """Rule for categorizing transactions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rules')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=Transaction.CATEGORY_CHOICES, default='OTHER')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Rule Type
    RULE_TYPE_CHOICES = [
        ('AND', 'All conditions must match (AND)'),
        ('OR', 'Any condition matches (OR)'),
    ]
    rule_type = models.CharField(max_length=3, choices=RULE_TYPE_CHOICES, default='AND')
    
    def __str__(self):
        return f"{self.name} → {self.get_category_display()}"
    
    def get_category_color(self):
        # Import here to avoid circular import
        from .models import Transaction
        return Transaction().get_category_color()

class RuleCondition(models.Model):
    """Individual condition within a rule"""
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='conditions')
    
    CONDITION_TYPE_CHOICES = [
        ('KEYWORD', 'Keyword in Description'),
        ('AMOUNT', 'Amount Range'),
        ('DATE', 'Date Range'),
        ('SOURCE', 'Transaction Source/Channel'),
    ]
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPE_CHOICES)
    
    # For KEYWORD condition
    keyword = models.CharField(max_length=100, blank=True)
    keyword_match_type = models.CharField(max_length=20, choices=[
        ('CONTAINS', 'Contains'),
        ('STARTS_WITH', 'Starts With'),
        ('ENDS_WITH', 'Ends With'),
        ('EXACT', 'Exact Match'),
    ], blank=True)
    
    # For AMOUNT condition
    amount_operator = models.CharField(max_length=20, choices=[
        ('EQUALS', 'Equals'),
        ('GREATER_THAN', 'Greater Than'),
        ('LESS_THAN', 'Less Than'),
        ('BETWEEN', 'Between'),
        ('GREATER_THAN_EQUAL', 'Greater Than or Equal'),
        ('LESS_THAN_EQUAL', 'Less Than or Equal'),
    ], blank=True)
    amount_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    amount_value2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # For DATE condition
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    
    # For SOURCE condition
    source_channel = models.CharField(max_length=50, blank=True, choices=[
        ('PAYTM', 'Paytm'),
        ('PHONEPE', 'PhonePe'),
        ('GOOGLE_PAY', 'Google Pay'),
        ('UPI', 'UPI'),
        ('DEBIT_CARD', 'Debit Card'),
        ('CREDIT_CARD', 'Credit Card'),
        ('NET_BANKING', 'Net Banking'),
        ('CHEQUE', 'Cheque'),
        ('NEFT', 'NEFT'),
        ('RTGS', 'RTGS'),
    ])
    
    def __str__(self):
        if self.condition_type == 'KEYWORD':
            return f"Keyword: {self.keyword}"
        elif self.condition_type == 'AMOUNT':
            if self.amount_operator == 'BETWEEN' and self.amount_value2:
                return f"Amount between {self.amount_value} and {self.amount_value2}"
            return f"Amount {self.get_amount_operator_display()}: {self.amount_value}"
        elif self.condition_type == 'DATE':
            return f"Date: {self.date_start} to {self.date_end}"
        elif self.condition_type == 'SOURCE':
            return f"Source: {self.get_source_channel_display()}"
        return f"Condition #{self.id}"


class CustomCategory(models.Model):
    """Custom category created by user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#95a5a6')  # Hex color
    icon = models.CharField(max_length=50, default='fa-circle')  # FontAwesome icon
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        unique_together = ('user', 'name')
        verbose_name_plural = "Custom Categories"


class CustomCategoryRule(models.Model):
    """Rule for custom categories"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_category_rules')
    custom_category = models.ForeignKey(CustomCategory, on_delete=models.CASCADE, related_name='rules')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Rule Type
    RULE_TYPE_CHOICES = [
        ('AND', 'All conditions must match (AND)'),
        ('OR', 'Any condition matches (OR)'),
    ]
    rule_type = models.CharField(max_length=3, choices=RULE_TYPE_CHOICES, default='AND')
    
    def __str__(self):
        return f"{self.name} → {self.custom_category.name}"


class CustomCategoryRuleCondition(models.Model):
    """Individual condition within a custom category rule"""
    rule = models.ForeignKey(CustomCategoryRule, on_delete=models.CASCADE, related_name='conditions')
    
    CONDITION_TYPE_CHOICES = [
        ('KEYWORD', 'Keyword in Description'),
        ('AMOUNT', 'Amount Range'),
        ('DATE', 'Date Range'),
    ]
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPE_CHOICES)
    
    # For KEYWORD condition
    keyword = models.CharField(max_length=100, blank=True)
    keyword_match_type = models.CharField(max_length=20, choices=[
        ('CONTAINS', 'Contains'),
        ('STARTS_WITH', 'Starts With'),
        ('ENDS_WITH', 'Ends With'),
        ('EXACT', 'Exact Match'),
    ], blank=True)
    
    # For AMOUNT condition
    amount_operator = models.CharField(max_length=20, choices=[
        ('EQUALS', 'Equals'),
        ('GREATER_THAN', 'Greater Than'),
        ('LESS_THAN', 'Less Than'),
        ('BETWEEN', 'Between'),
        ('GREATER_THAN_EQUAL', 'Greater Than or Equal'),
        ('LESS_THAN_EQUAL', 'Less Than or Equal'),
    ], blank=True)
    amount_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    amount_value2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # For DATE condition
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    
    def __str__(self):
        if self.condition_type == 'KEYWORD':
            return f"Keyword: {self.keyword}"
        elif self.condition_type == 'AMOUNT':
            if self.amount_operator == 'BETWEEN' and self.amount_value2:
                return f"Amount between {self.amount_value} and {self.amount_value2}"
            return f"Amount {self.get_amount_operator_display()}: {self.amount_value}"
        elif self.condition_type == 'DATE':
            return f"Date: {self.date_start} to {self.date_end}"
        return f"Condition #{self.id}"