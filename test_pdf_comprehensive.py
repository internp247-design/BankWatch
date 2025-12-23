#!/usr/bin/env python
"""
Comprehensive PDF Export Test
Tests all aspects of the PDF export functionality
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from analyzer.views import export_rules_results_to_pdf
from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from analyzer.models import BankAccount, BankStatement, Transaction
from datetime import datetime, timedelta
import json

def create_test_data():
    """Create test data for PDF export"""
    user, _ = User.objects.get_or_create(
        username='testuser_pdf',
        defaults={'email': 'test@example.com', 'is_active': True}
    )
    
    account, _ = BankAccount.objects.get_or_create(
        user=user,
        account_name='Test Account',
        defaults={
            'bank_name': 'Test Bank',
            'account_number': '1234567890'
        }
    )
    
    statement, _ = BankStatement.objects.get_or_create(
        account=account,
        statement_period_start=datetime.now().date() - timedelta(days=30),
        defaults={
            'statement_period_end': datetime.now().date(),
            'original_filename': 'test_statement.pdf',
            'file_type': BankStatement.PDF
        }
    )
    
    # Create test transactions
    transactions = []
    categories = ['FOOD', 'SHOPPING', 'TRANSPORT', 'ENTERTAINMENT', 'UTILITIES']
    
    for i in range(5):
        tx = Transaction.objects.create(
            statement=statement,
            date=datetime.now().date() - timedelta(days=i),
            description=f'Test Transaction {i+1}',
            amount=100 + (i * 50),
            transaction_type='DEBIT',
            category=categories[i % len(categories)]
        )
        transactions.append(tx)
    
    print(f"Created test data:")
    print(f"  User: {user.username}")
    print(f"  Account: {account.account_name}")
    print(f"  Statement: {statement.id}")
    print(f"  Transactions: {len(transactions)}")
    
    return user, account, statement, transactions

def test_pdf_export_get_request():
    """Test PDF export with GET request"""
    print("\n" + "="*60)
    print("TEST 1: PDF Export with GET Request")
    print("="*60)
    
    user, account, statement, transactions = create_test_data()
    
    factory = RequestFactory()
    tx_ids = ','.join(str(tx.id) for tx in transactions[:3])
    
    request = factory.get(
        '/analyzer/export/rules-results-pdf/',
        {
            'transaction_ids': [tx.id for tx in transactions[:3]],
            'account_id': account.id,
        }
    )
    request.user = user
    
    try:
        response = export_rules_results_to_pdf(request)
        
        # Verify response
        assert response.status_code == 200, f"Status code: {response.status_code}"
        assert response['Content-Type'] == 'application/pdf', f"Content-Type: {response['Content-Type']}"
        assert 'attachment' in response['Content-Disposition'], f"No attachment header"
        assert len(response.content) > 1000, f"PDF too small: {len(response.content)} bytes"
        
        print("✓ GET Request Test PASSED")
        print(f"  Response Status: {response.status_code}")
        print(f"  Content-Type: {response['Content-Type']}")
        print(f"  File Size: {len(response.content)} bytes")
        return True
        
    except Exception as e:
        print(f"✗ GET Request Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_export_empty():
    """Test PDF export with no data"""
    print("\n" + "="*60)
    print("TEST 2: PDF Export with No Data")
    print("="*60)
    
    user, _ = User.objects.get_or_create(
        username='testuser_empty',
        defaults={'email': 'empty@example.com'}
    )
    
    factory = RequestFactory()
    request = factory.get('/analyzer/export/rules-results-pdf/')
    request.user = user
    
    try:
        response = export_rules_results_to_pdf(request)
        
        # Verify response
        assert response.status_code == 200, f"Status code: {response.status_code}"
        assert response['Content-Type'] == 'application/pdf', f"Content-Type: {response['Content-Type']}"
        assert len(response.content) > 500, f"PDF too small: {len(response.content)} bytes"
        
        print("✓ Empty Data Test PASSED")
        print(f"  Response Status: {response.status_code}")
        print(f"  Content-Type: {response['Content-Type']}")
        print(f"  File Size: {len(response.content)} bytes")
        return True
        
    except Exception as e:
        print(f"✗ Empty Data Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_url_resolution():
    """Test URL resolution"""
    print("\n" + "="*60)
    print("TEST 3: URL Resolution")
    print("="*60)
    
    from django.urls import reverse
    
    try:
        url = reverse('export_rules_results_pdf')
        print(f"✓ URL Resolution PASSED")
        print(f"  URL Name: export_rules_results_pdf")
        print(f"  URL Path: {url}")
        return True
    except Exception as e:
        print(f"✗ URL Resolution FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PDF DOWNLOAD COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("URL Resolution", test_url_resolution()))
    results.append(("Empty Data Export", test_pdf_export_empty()))
    results.append(("GET Request Export", test_pdf_export_get_request()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED ✓" if result else "FAILED ✗"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - PDF export is working correctly!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
