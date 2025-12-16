import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.models import Rule

print(f"Total rules: {Rule.objects.count()}")
print("\nRules:")
for rule in Rule.objects.all().order_by('category', 'name'):
    count = rule.conditions.count()
    print(f"  {rule.category:20} | {rule.name:30} | {count} conditions | Active: {rule.is_active}")

print(f"\nTotal keywords: {sum(r.conditions.count() for r in Rule.objects.all())}")
