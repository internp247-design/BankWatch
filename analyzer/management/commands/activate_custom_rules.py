"""
Django management command to activate all inactive custom category rules
"""
from django.core.management.base import BaseCommand
from analyzer.models import CustomCategoryRule


class Command(BaseCommand):
    help = 'Activate all inactive custom category rules'

    def handle(self, *args, **options):
        # Get all inactive rules
        inactive_rules = CustomCategoryRule.objects.filter(is_active=False)
        count = inactive_rules.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('All rules are already active!'))
            return
        
        # Activate them
        inactive_rules.update(is_active=True)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Successfully activated {count} rule{"s" if count > 1 else ""}')
        )
        
        # Show details
        for rule in CustomCategoryRule.objects.filter(is_active=True):
            conditions = rule.conditions.count()
            self.stdout.write(
                f"  - {rule.name} ({rule.custom_category.name}) - {conditions} condition{'s' if conditions != 1 else ''}"
            )
