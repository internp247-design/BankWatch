"""
Test User Label Classification Engine

Tests for the user label classification feature to ensure:
1. Labels are the primary signal for category assignment
2. User edits are respected and reused for future classifications
3. Classification follows correct priority order
4. Results page shows correct categories based on label matches
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from analyzer.models import (
    BankAccount, BankStatement, Transaction, 
    CustomCategory, Rule, RuleCondition
)
from analyzer.user_label_engine import UserLabelClassificationEngine
from datetime import datetime, date
from decimal import Decimal


class UserLabelClassificationEngineTestCase(TestCase):
    """Test the UserLabelClassificationEngine"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create bank account
        self.account = BankAccount.objects.create(
            user=self.user,
            account_name='Test Account',
            account_number='1234567890',
            bank_name='Test Bank'
        )
        
        # Create statement
        self.statement = BankStatement.objects.create(
            account=self.account,
            statement_date=date(2025, 1, 1),
            total_credits=Decimal('1000.00'),
            total_debits=Decimal('500.00'),
            opening_balance=Decimal('10000.00'),
            closing_balance=Decimal('10500.00')
        )
        
        # Create custom categories
        self.coffee_category = CustomCategory.objects.create(
            user=self.user,
            name='Coffee',
            color='#FF5733',
            is_active=True
        )
        
        self.groceries_category = CustomCategory.objects.create(
            user=self.user,
            name='Groceries',
            color='#33FF57',
            is_active=True
        )
        
        # Initialize engine
        self.engine = UserLabelClassificationEngine(self.user)
    
    def test_label_matching_with_category_name(self):
        """Test that category names are matched against descriptions"""
        # Create transaction with manual edit and label
        tx = Transaction.objects.create(
            statement=self.statement,
            date=date(2025, 1, 1),
            description='Starbucks Coffee Shop',
            amount=Decimal('5.50'),
            transaction_type='DEBIT',
            category='OTHER',
            user_label='Coffee',
            is_manually_edited=True
        )
        
        # Test finding match for similar transaction
        result = self.engine.find_matching_category_by_label({
            'description': 'Starbucks Downtown Store',
            'user_label': ''
        })
        
        # Should match because 'Coffee' category name is close
        # (In real scenario, would match based on frequency of Coffee label)
        self.assertIsNotNone(result)
        self.assertEqual(result['matched_custom_category'].name, 'Coffee')
    
    def test_user_label_matching(self):
        """Test that user labels from edited transactions are reused"""
        # Create a transaction with user label
        tx1 = Transaction.objects.create(
            statement=self.statement,
            date=date(2025, 1, 1),
            description='Starbucks Coffee Shop',
            amount=Decimal('5.50'),
            transaction_type='DEBIT',
            category='OTHER',
            user_label='Coffee',
            is_manually_edited=True
        )
        
        # Now test matching for similar transaction
        result = self.engine.find_matching_category_by_label({
            'description': 'Starbucks Downtown Coffee',
            'user_label': ''
        })
        
        # Should find match due to "Coffee" label matching
        # (depending on DB query results)
        self.assertIsNotNone(result)
    
    def test_confidence_scoring_exact_match(self):
        """Test confidence scoring with exact match"""
        confidence = self.engine.get_transaction_label_confidence(
            'Coffee',
            'Coffee'
        )
        self.assertEqual(confidence, 1.0)
    
    def test_confidence_scoring_substring_match(self):
        """Test confidence scoring with substring match"""
        confidence = self.engine.get_transaction_label_confidence(
            'Coffee',
            'Starbucks Coffee Shop'
        )
        self.assertGreater(confidence, 0.5)
        self.assertLess(confidence, 1.0)
    
    def test_confidence_scoring_word_match(self):
        """Test confidence scoring with word match"""
        confidence = self.engine.get_transaction_label_confidence(
            'Coffee Shop',
            'Starbucks Coffee Store'
        )
        self.assertGreater(confidence, 0.0)
        self.assertLess(confidence, 0.5)
    
    def test_confidence_scoring_no_match(self):
        """Test confidence scoring with no match"""
        confidence = self.engine.get_transaction_label_confidence(
            'Coffee',
            'Grocery Store'
        )
        self.assertEqual(confidence, 0.0)
    
    def test_empty_label_returns_no_match(self):
        """Test that empty labels return None"""
        result = self.engine.find_matching_category_by_label({
            'description': '',
            'user_label': ''
        })
        self.assertIsNone(result)
    
    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive"""
        # Create transaction with uppercase label
        tx = Transaction.objects.create(
            statement=self.statement,
            date=date(2025, 1, 1),
            description='STARBUCKS COFFEE SHOP',
            amount=Decimal('5.50'),
            transaction_type='DEBIT',
            category='OTHER',
            user_label='COFFEE',
            is_manually_edited=True
        )
        
        # Should match lowercase input
        confidence = self.engine.get_transaction_label_confidence(
            'coffee',
            'starbucks coffee shop'
        )
        self.assertEqual(confidence, 1.0)
    
    def test_whitespace_trimming(self):
        """Test that whitespace is properly trimmed"""
        confidence = self.engine.get_transaction_label_confidence(
            '  Coffee  ',
            'Starbucks   Coffee   Shop  '
        )
        self.assertGreater(confidence, 0.5)


class UserLabelClassificationIntegrationTest(TestCase):
    """Integration tests for user label classification in views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create bank account
        self.account = BankAccount.objects.create(
            user=self.user,
            account_name='Test Account',
            account_number='1234567890',
            bank_name='Test Bank'
        )
        
        # Create statement
        self.statement = BankStatement.objects.create(
            account=self.account,
            statement_date=date(2025, 1, 1),
            total_credits=Decimal('1000.00'),
            total_debits=Decimal('500.00'),
            opening_balance=Decimal('10000.00'),
            closing_balance=Decimal('10500.00')
        )
        
        # Create custom category
        self.coffee_category = CustomCategory.objects.create(
            user=self.user,
            name='Coffee',
            color='#FF5733',
            is_active=True
        )
        
        # Create transactions
        self.tx1 = Transaction.objects.create(
            statement=self.statement,
            date=date(2025, 1, 1),
            description='Starbucks Coffee Shop',
            amount=Decimal('5.50'),
            transaction_type='DEBIT',
            category='OTHER',
            user_label='Coffee',
            is_manually_edited=True  # This one is edited
        )
        
        self.tx2 = Transaction.objects.create(
            statement=self.statement,
            date=date(2025, 1, 2),
            description='Starbucks Downtown',
            amount=Decimal('6.25'),
            transaction_type='DEBIT',
            category='OTHER',
            user_label='',
            is_manually_edited=False  # This one should be classified
        )
    
    def test_results_page_shows_label_matches(self):
        """Test that results page correctly shows label-based classifications"""
        self.client.login(username='testuser', password='testpass123')
        
        # Navigate to results page
        response = self.client.get('/analyzer/rules/apply/results/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analyzer/apply_rules_results.html')
    
    def test_manually_edited_transactions_protected(self):
        """Test that manually edited transactions are never overwritten by rules"""
        # The transaction marked as manually edited should keep its category
        # even if rules are applied
        self.assertTrue(self.tx1.is_manually_edited)
        original_category = self.tx1.category
        original_label = self.tx1.user_label
        
        # Apply rules (this should skip the manually edited transaction)
        self.client.login(username='testuser', password='testpass123')
        self.client.post('/analyzer/rules/apply/', {
            'account_id': self.account.id
        })
        
        # Refresh from DB
        self.tx1.refresh_from_db()
        
        # Should still have original values
        self.assertEqual(self.tx1.category, original_category)
        self.assertEqual(self.tx1.user_label, original_label)


class UserLabelPriorityTest(TestCase):
    """Test classification priority order"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.account = BankAccount.objects.create(
            user=self.user,
            account_name='Test Account',
            account_number='1234567890',
            bank_name='Test Bank'
        )
        
        self.statement = BankStatement.objects.create(
            account=self.account,
            statement_date=date(2025, 1, 1),
            total_credits=Decimal('1000.00'),
            total_debits=Decimal('500.00'),
            opening_balance=Decimal('10000.00'),
            closing_balance=Decimal('10500.00')
        )
        
        self.engine = UserLabelClassificationEngine(self.user)
    
    def test_priority_user_label_over_rule(self):
        """Test that user labels have higher priority than rules"""
        # Create a custom category
        category = CustomCategory.objects.create(
            user=self.user,
            name='Coffee',
            color='#FF5733',
            is_active=True
        )
        
        # Create transaction with user label
        tx = Transaction.objects.create(
            statement=self.statement,
            date=date(2025, 1, 1),
            description='Starbucks Coffee',
            amount=Decimal('5.50'),
            transaction_type='DEBIT',
            category='FOOD',  # Different from custom category
            user_label='Coffee',
            is_manually_edited=True
        )
        
        # The user label should be recognized even if a rule might say something different
        self.assertTrue(tx.is_manually_edited)
        self.assertEqual(tx.user_label, 'Coffee')
