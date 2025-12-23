#!/usr/bin/env python
"""
Test script to validate PDF export functionality
Run this from the Django project root: python test_pdf_export.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.views import export_rules_results_to_pdf
from django.test import RequestFactory
from django.contrib.auth.models import User
from analyzer.models import BankAccount, BankStatement, Transaction

def test_pdf_export():
    """Test PDF export functionality"""
    print("Testing PDF export functionality...")
    
    # Create a test request
    factory = RequestFactory()
    
    # Create or get a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    print(f"Using user: {user.username}")
    
    # Create test request
    request = factory.get('/analyzer/export/rules-results-pdf/', {
        'transaction_ids': [],
        'account_id': '',
        'show_changed': ''
    })
    request.user = user
    
    # Call the view
    try:
        response = export_rules_results_to_pdf(request)
        
        if response.status_code == 200:
            print("[OK] PDF export successful!")
            print(f"  Content-Type: {response.get('Content-Type')}")
            print(f"  Content-Disposition: {response.get('Content-Disposition')}")
            print(f"  Content size: {len(response.content)} bytes")
            return True
        else:
            print(f"[ERROR] Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error during PDF export: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_pdf_export()
    sys.exit(0 if success else 1)
