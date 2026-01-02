#!/usr/bin/env python
"""
Visual verification of conditions display on the page
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth.models import User
from analyzer.models import Rule, CustomCategory, CustomCategoryRule

def show_what_users_will_see():
    print("\n" + "=" * 100)
    print("WHAT USERS WILL SEE ON THE CREATE-YOUR-OWN PAGE")
    print("=" * 100)
    
    user = User.objects.filter(is_superuser=False).first()
    if not user:
        print("\nNo user found")
        return
    
    print(f"\nUser: {user.username}")
    print("\n" + "-" * 100)
    print("ACTIVE RULES SECTION")
    print("-" * 100)
    
    rules = Rule.objects.filter(user=user, is_active=True).order_by('name')[:5]
    
    for rule in rules:
        print(f"\n🔵 {rule.name}")
        
        if rule.conditions.all():
            conditions = rule.conditions.all()
            condition_strs = [str(c) for c in conditions]
            separator = f" {rule.get_rule_type_display().split()[0].upper()} "  # AND or OR
            condition_display = separator.join(condition_strs)
            print(f"   {condition_display}")
        else:
            print(f"   No conditions added")
        
        print(f"   → {rule.get_category_display()}")
    
    print("\n" + "-" * 100)
    print("MY CATEGORIES SECTION")
    print("-" * 100)
    
    categories = CustomCategory.objects.filter(user=user)[:3]
    
    if not categories:
        print("\n   (No custom categories yet)")
    else:
        for category in categories:
            print(f"\n📁 {category.name}")
            
            rules = category.customcategoryrule_set.all()
            if not rules:
                print(f"   No rules yet")
            else:
                for rule in rules:
                    print(f"   • {rule.name}")
                    
                    if rule.conditions.all():
                        conditions = rule.conditions.all()
                        for cond in conditions:
                            print(f"     - {cond}")
                    else:
                        print(f"     - No conditions added")
    
    print("\n" + "=" * 100)
    print("END OF DISPLAY")
    print("=" * 100 + "\n")

if __name__ == '__main__':
    show_what_users_will_see()
