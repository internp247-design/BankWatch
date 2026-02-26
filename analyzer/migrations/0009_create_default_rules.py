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
    
    default_rules_config = [
        {
            'name': 'Total Credit',
            'description': 'All credit/income transactions',
            'category': 'INCOME',
            'is_summary': False,
            'conditions': [
                {
                    'condition_type': 'SOURCE',
                    'source_channel': 'CREDIT',
                }
            ]
        },
        {
            'name': 'Total Debit',
            'description': 'All debit/expense transactions',
            'category': 'OTHER',
            'is_summary': False,
            'conditions': [
                {
                    'condition_type': 'AMOUNT',
                    'amount_operator': 'LESS_THAN',
                    'amount_value': Decimal('0'),
                }
            ]
        },
        {
            'name': 'UPI Total',
            'description': 'All UPI transactions',
            'category': 'OTHER',
            'is_summary': False,
            'conditions': [
                {
                    'condition_type': 'KEYWORD',
                    'keyword': 'UPI',
                    'keyword_match_type': 'CONTAINS',
                }
            ]
        },
        {
            'name': 'ATM Withdrawals',
            'description': 'All ATM withdrawals',
            'category': 'OTHER',
            'is_summary': False,
            'conditions': [
                {
                    'condition_type': 'KEYWORD',
                    'keyword': 'ATM',
                    'keyword_match_type': 'CONTAINS',
                }
            ]
        },
        {
            'name': 'Large Transactions',
            'description': 'Transactions over 10,000',
            'category': 'OTHER',
            'is_summary': False,
            'conditions': [
                {
                    'condition_type': 'AMOUNT',
                    'amount_operator': 'GREATER_THAN',
                    'amount_value': Decimal('10000'),
                }
            ]
        },
        {
            'name': 'Net Savings',
            'description': 'Summary of net savings',
            'category': 'INCOME',
            'is_summary': True,
            'conditions': []
        },
    ]
    
    for rule_config in default_rules_config:
        # Check if rule already exists
        rule, created = Rule.objects.get_or_create(
            user=system_user,
            name=rule_config['name'],
            defaults={
                'category': rule_config['category'],
                'is_active': True,
                'rule_type': 'OR',
                'is_default': True,
                'is_summary_rule': rule_config['is_summary'],
            }
        )
        
        # Only add conditions if rule was just created (not existing)
        if created and rule_config['conditions']:
            for cond_config in rule_config['conditions']:
                RuleCondition.objects.create(
                    rule=rule,
                    **cond_config
                )


def remove_default_rules(apps, schema_editor):
    """Remove the default rules if migration is reversed"""
    Rule = apps.get_model('analyzer', 'Rule')
    User = apps.get_model('auth', 'User')
    
    try:
        system_user = User.objects.get(username='system_rules')
        Rule.objects.filter(user=system_user, is_default=True).delete()
        # Optionally delete the system user
        # system_user.delete()
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0008_rule_is_default_is_summary_rule_userdefaultrulepreference'),
    ]

    operations = [
        migrations.RunPython(create_default_rules, remove_default_rules),
    ]
