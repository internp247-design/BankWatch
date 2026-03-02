# Data migration to create 6 default rules

from django.db import migrations
from decimal import Decimal


def create_default_rules(apps, schema_editor):
    """Create the 6 default rules to auto-apply on results page"""
    Rule = apps.get_model('analyzer', 'Rule')
    RuleCondition = apps.get_model('analyzer', 'RuleCondition')
    User = apps.get_model('auth', 'User')
    
    # Get or create a system user for global default rules
    system_user, created = User.objects.get_or_create(
        username='system_rules',
        defaults={'email': 'system@bankwatch.local', 'is_staff': False}
    )
    
    # Rule 1: Total Credit — matches 'credit' OR 'cr'
    rule1, created = Rule.objects.get_or_create(
        user=system_user,
        name='Total Credit',
        defaults={
            'category': 'INCOME',
            'is_active': True,
            'rule_type': 'OR',  # ANY condition matches
            'is_default': True,
            'is_summary_rule': False,
        }
    )
    if created:
        RuleCondition.objects.create(
            rule=rule1,
            condition_type='KEYWORD',
            keyword='credit',
            keyword_match_type='CONTAINS',
        )
        RuleCondition.objects.create(
            rule=rule1,
            condition_type='KEYWORD',
            keyword='cr',
            keyword_match_type='CONTAINS',
        )
    
    # Rule 2: Total Debit — matches amount < 0 OR 'dr' OR 'debit'
    rule2, created = Rule.objects.get_or_create(
        user=system_user,
        name='Total Debit',
        defaults={
            'category': 'OTHER',
            'is_active': True,
            'rule_type': 'OR',  # ANY condition matches
            'is_default': True,
            'is_summary_rule': False,
        }
    )
    if created:
        RuleCondition.objects.create(
            rule=rule2,
            condition_type='AMOUNT',
            amount_operator='LESS_THAN',
            amount_value=Decimal('0'),
        )
        RuleCondition.objects.create(
            rule=rule2,
            condition_type='KEYWORD',
            keyword='dr',
            keyword_match_type='CONTAINS',
        )
        RuleCondition.objects.create(
            rule=rule2,
            condition_type='KEYWORD',
            keyword='debit',
            keyword_match_type='CONTAINS',
        )
    
    # Rule 3: UPI Total — matches 'UPI'
    rule3, created = Rule.objects.get_or_create(
        user=system_user,
        name='UPI Total',
        defaults={
            'category': 'OTHER',
            'is_active': True,
            'rule_type': 'OR',
            'is_default': True,
            'is_summary_rule': False,
        }
    )
    if created:
        RuleCondition.objects.create(
            rule=rule3,
            condition_type='KEYWORD',
            keyword='UPI',
            keyword_match_type='CONTAINS',
        )
    
    # Rule 4: ATM Withdrawals — matches 'ATM'
    rule4, created = Rule.objects.get_or_create(
        user=system_user,
        name='ATM Withdrawals',
        defaults={
            'category': 'OTHER',
            'is_active': True,
            'rule_type': 'OR',
            'is_default': True,
            'is_summary_rule': False,
        }
    )
    if created:
        RuleCondition.objects.create(
            rule=rule4,
            condition_type='KEYWORD',
            keyword='ATM',
            keyword_match_type='CONTAINS',
        )
    
    # Rule 5: Large Transactions — matches amount > 10,000
    rule5, created = Rule.objects.get_or_create(
        user=system_user,
        name='Large Transactions',
        defaults={
            'category': 'OTHER',
            'is_active': True,
            'rule_type': 'OR',
            'is_default': True,
            'is_summary_rule': False,
        }
    )
    if created:
        RuleCondition.objects.create(
            rule=rule5,
            condition_type='AMOUNT',
            amount_operator='GREATER_THAN',
            amount_value=Decimal('10000'),
        )
    
    # Rule 6: Net Savings — summary-only rule (no conditions, aggregates all)
    rule6, created = Rule.objects.get_or_create(
        user=system_user,
        name='Net Savings',
        defaults={
            'category': 'INCOME',
            'is_active': True,
            'rule_type': 'OR',
            'is_default': True,
            'is_summary_rule': True,
        }
    )
    # No conditions for summary rule


def remove_default_rules(apps, schema_editor):
    """Remove the default rules if migration is reversed"""
    Rule = apps.get_model('analyzer', 'Rule')
    User = apps.get_model('auth', 'User')
    
    try:
        system_user = User.objects.get(username='system_rules')
        Rule.objects.filter(user=system_user, is_default=True).delete()
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0008_rule_is_default_is_summary_rule_userdefaultrulepreference'),
    ]

    operations = [
        migrations.RunPython(create_default_rules, remove_default_rules),
    ]
