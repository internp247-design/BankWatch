from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from .models import BankAccount, BankStatement, Transaction
from decimal import Decimal


class DateFiltrationTestCase(TestCase):
    """Test suite for date filtration across all pages"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
        
        # Create a test account
        self.account = BankAccount.objects.create(
            user=self.user,
            account_name='Test Account',
            bank_name='Test Bank'
        )
        
        # Create a test statement
        self.statement = BankStatement.objects.create(
            account=self.account,
            statement_period_start=date.today() - timedelta(days=100),
            statement_period_end=date.today()
        )
        
        # Create transactions with different dates
        self.now = timezone.now().date()
        
        # Transaction from 2 days ago
        Transaction.objects.create(
            statement=self.statement,
            date=self.now - timedelta(days=2),
            description='Test Transaction 2 days ago',
            amount=Decimal('1000.00'),
            transaction_type='CREDIT',
            category='INCOME'
        )
        
        # Transaction from 5 days ago
        Transaction.objects.create(
            statement=self.statement,
            date=self.now - timedelta(days=5),
            description='Test Transaction 5 days ago',
            amount=Decimal('500.00'),
            transaction_type='DEBIT',
            category='FOOD'
        )
        
        # Transaction from 10 days ago
        Transaction.objects.create(
            statement=self.statement,
            date=self.now - timedelta(days=10),
            description='Test Transaction 10 days ago',
            amount=Decimal('200.00'),
            transaction_type='DEBIT',
            category='TRANSPORT'
        )
        
        # Transaction from 20 days ago
        Transaction.objects.create(
            statement=self.statement,
            date=self.now - timedelta(days=20),
            description='Test Transaction 20 days ago',
            amount=Decimal('1500.00'),
            transaction_type='DEBIT',
            category='BILLS'
        )
        
        # Transaction from 50 days ago
        Transaction.objects.create(
            statement=self.statement,
            date=self.now - timedelta(days=50),
            description='Test Transaction 50 days ago',
            amount=Decimal('800.00'),
            transaction_type='CREDIT',
            category='INCOME'
        )
        
        # Transaction from 100 days ago
        Transaction.objects.create(
            statement=self.statement,
            date=self.now - timedelta(days=100),
            description='Test Transaction 100 days ago',
            amount=Decimal('300.00'),
            transaction_type='DEBIT',
            category='ENTERTAINMENT'
        )
    
    def test_financial_overview_all_time(self):
        """Test financial overview with all time period"""
        response = self.client.get('/analyzer/api/financial-overview/?period=all')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['transaction_count'], 6)
        self.assertEqual(float(data['income']), 1800.00)  # 1000 + 800
        self.assertEqual(float(data['expenses']), 2500.00)  # 500 + 200 + 1500 + 300
    
    def test_financial_overview_5days(self):
        """Test financial overview with 5 days filter"""
        response = self.client.get('/analyzer/api/financial-overview/?period=5days')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['transaction_count'], 2)  # 2 days ago, 5 days ago
        self.assertEqual(float(data['income']), 1000.00)  # 2 days ago transaction
        self.assertEqual(float(data['expenses']), 500.00)  # 5 days ago transaction
    
    def test_financial_overview_7days(self):
        """Test financial overview with 7 days filter (includes 1 week)"""
        response = self.client.get('/analyzer/api/financial-overview/?period=7days')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        # 2 days ago and 5 days ago (10 days > 7 days, so not included)
        self.assertEqual(data['transaction_count'], 2)
    
    def test_financial_overview_15days(self):
        """Test financial overview with 15 days filter"""
        response = self.client.get('/analyzer/api/financial-overview/?period=15days')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['transaction_count'], 3)  # 2, 5, 10 days ago
        self.assertEqual(float(data['income']), 1000.00)
        self.assertEqual(float(data['expenses']), 700.00)  # 500 + 200
    
    def test_financial_overview_30days(self):
        """Test financial overview with 30 days filter"""
        response = self.client.get('/analyzer/api/financial-overview/?period=30days')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['transaction_count'], 4)  # 2, 5, 10, 20 days ago
        self.assertEqual(float(data['income']), 1000.00)
        self.assertEqual(float(data['expenses']), 2200.00)  # 500 + 200 + 1500
    
    def test_financial_overview_90days(self):
        """Test financial overview with 90 days filter"""
        response = self.client.get('/analyzer/api/financial-overview/?period=90days')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['transaction_count'], 5)  # All except 100 days ago
        self.assertEqual(float(data['income']), 1800.00)  # 1000 + 800
        self.assertEqual(float(data['expenses']), 2200.00)  # 500 + 200 + 1500
    
    def test_account_transactions_filtered_all_time(self):
        """Test account transactions with all time filter"""
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/transactions-filtered/?period=all&page=1'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['transactions']), 6)
    
    def test_account_transactions_filtered_5days(self):
        """Test account transactions with 5 days filter"""
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/transactions-filtered/?period=5days&page=1'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['transactions']), 2)
    
    def test_account_transactions_filtered_7days(self):
        """Test account transactions with 7 days filter"""
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/transactions-filtered/?period=7days&page=1'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['transactions']), 2)  # 2, 5 days ago
    
    def test_account_transactions_filtered_15days(self):
        """Test account transactions with 15 days filter"""
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/transactions-filtered/?period=15days&page=1'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['transactions']), 3)  # 2, 5, 10 days ago
    
    def test_account_transactions_filtered_30days(self):
        """Test account transactions with 30 days filter"""
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/transactions-filtered/?period=30days&page=1'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['transactions']), 4)  # 2, 5, 10, 20 days ago
    
    def test_account_transactions_filtered_90days(self):
        """Test account transactions with 90 days filter"""
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/transactions-filtered/?period=90days&page=1'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['transactions']), 5)  # All except 100 days ago
    
    def test_account_summary_all_time(self):
        """Test account summary with all time filter"""
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/summary/?period=all'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(float(data['income']), 1800.00)
        self.assertEqual(float(data['expenses']), 2500.00)
    
    def test_account_summary_5days(self):
        """Test account summary with 5 days filter"""
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/summary/?period=5days'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(float(data['income']), 1000.00)
        self.assertEqual(float(data['expenses']), 500.00)
        self.assertEqual(float(data['savings']), 500.00)
    
    def test_account_summary_30days(self):
        """Test account summary with 30 days filter"""
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/summary/?period=30days'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(float(data['income']), 1000.00)
        self.assertEqual(float(data['expenses']), 2200.00)
        self.assertEqual(float(data['savings']), -1200.00)
    
    def test_results_transactions_filtered_all_time(self):
        """Test results transactions with all time filter"""
        response = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/?period=all'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['transactions']), 6)
        self.assertEqual(float(data['income']), 1800.00)
        self.assertEqual(float(data['expenses']), 2500.00)
    
    def test_results_transactions_filtered_custom_date_range(self):
        """Test results transactions with custom date range"""
        start_date = (self.now - timedelta(days=15)).strftime('%Y-%m-%d')
        end_date = (self.now - timedelta(days=5)).strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/?period=custom&start_date={start_date}&end_date={end_date}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        # Should include transactions from 10 days ago (within range)
        # Should not include 2 days ago (after range) or 20 days ago (before start)
        self.assertEqual(len(data['transactions']), 2)  # 10 days ago and 5 days ago
    
    def test_results_transactions_filtered_custom_date_invalid(self):
        """Test results transactions with invalid custom date range"""
        start_date = '2024-01-01'
        end_date = '2023-01-01'  # End before start - invalid
        
        response = self.client.get(
            f'/analyzer/api/statements/{self.statement.id}/transactions-filtered/?period=custom&start_date={start_date}&end_date={end_date}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should handle gracefully or show error
        # The view checks if start_date > end_date on frontend, but backend should too
    
    def test_date_parameter_consistency(self):
        """Test that parameter names are consistent across endpoints"""
        # All endpoints should accept 'all', '5days', '7days', '15days', '30days', '90days'
        periods = ['all', '5days', '7days', '15days', '30days', '90days']
        
        for period in periods:
            response1 = self.client.get(f'/analyzer/api/financial-overview/?period={period}')
            response2 = self.client.get(f'/analyzer/api/accounts/{self.account.id}/transactions-filtered/?period={period}&page=1')
            response3 = self.client.get(f'/analyzer/api/accounts/{self.account.id}/summary/?period={period}')
            
            self.assertEqual(response1.status_code, 200, f"Financial overview failed for period: {period}")
            self.assertEqual(response2.status_code, 200, f"Account transactions failed for period: {period}")
            self.assertEqual(response3.status_code, 200, f"Account summary failed for period: {period}")
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access other users' data"""
        # Create another user
        other_user = User.objects.create_user(username='otheruser', password='testpass')
        
        # Try to access with unauthorized user
        self.client.logout()
        self.client.login(username='otheruser', password='testpass')
        
        response = self.client.get(
            f'/analyzer/api/accounts/{self.account.id}/transactions-filtered/?period=all&page=1'
        )
        self.assertEqual(response.status_code, 404)  # Should not find account from other user

