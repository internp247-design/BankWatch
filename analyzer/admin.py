from django.contrib import admin
from .models import (
    BankAccount, BankStatement, Transaction, AnalysisSummary, 
    Rule, RuleCondition, CustomCategory, CustomCategoryRule, CustomCategoryRuleCondition
)

# Register your models here.

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'bank_name', 'user', 'created_at')
    list_filter = ('bank_name', 'created_at')
    search_fields = ('account_name', 'bank_name')

@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = ('account', 'file_type', 'upload_date', 'rules_applied')
    list_filter = ('file_type', 'upload_date')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'category', 'amount', 'transaction_type')
    list_filter = ('category', 'transaction_type', 'date')
    search_fields = ('description',)

@admin.register(AnalysisSummary)
class AnalysisSummaryAdmin(admin.ModelAdmin):
    list_display = ('statement', 'total_income', 'total_expenses', 'net_savings')

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'user', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name',)

@admin.register(RuleCondition)
class RuleConditionAdmin(admin.ModelAdmin):
    list_display = ('rule', 'condition_type')
    list_filter = ('condition_type',)

@admin.register(CustomCategory)
class CustomCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username')

@admin.register(CustomCategoryRule)
class CustomCategoryRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'custom_category', 'user', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)

@admin.register(CustomCategoryRuleCondition)
class CustomCategoryRuleConditionAdmin(admin.ModelAdmin):
    list_display = ('rule', 'condition_type')
    list_filter = ('condition_type',)
