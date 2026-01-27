#!/usr/bin/env python
"""
Test script to verify pagination with persistent date filters implementation
Run this script to validate the Results page pagination fix
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
sys.path.insert(0, '/c/Users/princ/OneDrive/Documents/New Project 15 12 25/BankWatch')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from analyzer.models import BankAccount, BankStatement, Transaction
from datetime import datetime, timedelta
from decimal import Decimal

class PaginationTestCase(TestCase):
    """Test pagination with persistent date filters"""
    
    def setUp(self):
        """Create test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create account
        self.account = BankAccount.objects.create(
            user=self.user,
            account_name='Test Account',
            account_number='1234567890',
            bank_name='Test Bank',
            is_primary=True
        )
        
        # Create statement
        self.statement = BankStatement.objects.create(
            account=self.account,
            statement_period_start=datetime(2026, 1, 1).date(),
            statement_period_end=datetime(2026, 1, 25).date(),
            total_credit=Decimal('500000.00'),
            total_debit=Decimal('300000.00'),
            opening_balance=Decimal('100000.00'),
            closing_balance=Decimal('300000.00')
        )
        
        # Create 50 test transactions (5 per day for 10 days)
        base_date = datetime(2026, 1, 15)
        for day in range(10):
            current_date = (base_date - timedelta(days=day)).date()
            
            for i in range(5):
                # Income transaction
                Transaction.objects.create(
                    statement=self.statement,
                    date=current_date,
                    description=f'Income {day}-{i}',
                    amount=Decimal('10000.00'),
                    transaction_type='CREDIT',
                    category='Income'
                )
                
                # Expense transaction
                Transaction.objects.create(
                    statement=self.statement,
                    date=current_date,
                    description=f'Expense {day}-{i}',
                    amount=Decimal('6000.00'),
                    transaction_type='DEBIT',
                    category='Food'
                )
        
        # Create client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_pagination_api_returns_correct_page_metadata(self):
        """Test that API returns correct pagination metadata"""
        response = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/',
            {'period': 'all', 'page': 1}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check pagination metadata exists
        self.assertIn('current_page', data)
        self.assertIn('total_pages', data)
        self.assertIn('has_next', data)
        self.assertIn('has_previous', data)
        self.assertIn('page_range', data)
        
        # Check values
        self.assertEqual(data['current_page'], 1)
        self.assertTrue(data['has_next'])
        self.assertFalse(data['has_previous'])
        self.assertEqual(len(data['transactions']), 10)  # 10 per page
        
    def test_pagination_page_2_contains_different_transactions(self):
        """Test that page 2 returns different transactions"""
        response1 = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/',
            {'period': 'all', 'page': 1}
        )
        
        response2 = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/',
            {'period': 'all', 'page': 2}
        )
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Get transaction IDs
        ids1 = {tx['id'] for tx in data1['transactions']}
        ids2 = {tx['id'] for tx in data2['transactions']}
        
        # No overlap between pages
        self.assertEqual(len(ids1 & ids2), 0)
        
    def test_date_filter_5days_with_pagination(self):
        """Test that 5-day filter persists across pages"""
        response = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/',
            {'period': '5days', 'page': 1}
        )
        
        data = response.json()
        
        # Should have fewer transactions due to 5-day filter
        self.assertLess(data['transaction_count'], 100)  # Not all 100 transactions
        self.assertEqual(len(data['transactions']), min(10, data['transaction_count']))
        
    def test_date_filter_summary_totals_consistent(self):
        """Test that summary totals are for full filtered set, not just current page"""
        response = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/',
            {'period': '30days', 'page': 1}
        )
        
        data = response.json()
        
        # Summary should be for all filtered transactions
        # Not just the 10 on current page
        total_transactions = data['transaction_count']
        page_transactions = len(data['transactions'])
        
        self.assertGreaterEqual(total_transactions, page_transactions)
        
        # Income and expenses should reflect full filtered set
        self.assertGreater(data['income'], 0)
        self.assertGreater(data['expenses'], 0)
        
    def test_custom_date_range_with_pagination(self):
        """Test custom date range persists with pagination"""
        response = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/',
            {
                'period': 'custom',
                'start_date': '2026-01-10',
                'end_date': '2026-01-20',
                'page': 1
            }
        )
        
        data = response.json()
        
        self.assertEqual(data['success'], True)
        self.assertEqual(data['period'], 'custom')
        self.assertGreater(len(data['transactions']), 0)
        
    def test_invalid_page_defaults_to_page_1(self):
        """Test that invalid page numbers default to page 1"""
        response = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/',
            {'period': 'all', 'page': 9999}  # Beyond total pages
        )
        
        data = response.json()
        
        # Should default to page 1
        self.assertEqual(data['current_page'], 1)
        
    def test_empty_result_set_pagination(self):
        """Test pagination with no transactions matching filter"""
        response = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/',
            {
                'period': 'custom',
                'start_date': '2025-01-01',  # Before all transactions
                'end_date': '2025-01-31',
                'page': 1
            }
        )
        
        data = response.json()
        
        self.assertEqual(data['transaction_count'], 0)
        self.assertEqual(len(data['transactions']), 0)
        self.assertEqual(data['total_pages'], 0)

def run_tests():
    """Run all pagination tests"""
    print("=" * 70)
    print("PAGINATION WITH PERSISTENT DATE FILTERS - TEST SUITE")
    print("=" * 70)
    print()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True, keepdb=False)
    
    failures = test_runner.run_tests(['__main__'])
    
    print()
    print("=" * 70)
    if failures == 0:
        print("✅ ALL TESTS PASSED - Pagination implementation is working correctly!")
    else:
        print(f"❌ {failures} TEST(S) FAILED - Review implementation")
    print("=" * 70)
    
    return failures

if __name__ == '__main__':
    sys.exit(run_tests())
