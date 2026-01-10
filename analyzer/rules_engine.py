from .models import Rule, RuleCondition, Transaction
from django.utils import timezone

class RulesEngine:
    """Engine to apply rules to transactions"""
    
    def __init__(self, user):
        self.user = user
        self.rules = Rule.objects.filter(user=user, is_active=True).prefetch_related('conditions')
    
    def apply_rules_to_transaction(self, transaction_data):
        """Apply all rules to a transaction and return matching category"""
        for rule in self.rules:
            if self._matches_rule(transaction_data, rule):
                return rule.category
        return None  # No rule matched

    def find_matching_rule(self, transaction_data):
        """Return the Rule object that matches the transaction, or None."""
        for rule in self.rules:
            if self._matches_rule(transaction_data, rule):
                return rule
        return None
    
    def _matches_rule(self, transaction_data, rule):
        """Check if transaction matches a specific rule"""
        conditions = rule.conditions.all()
        
        if not conditions.exists():
            return False
        
        if rule.rule_type == 'AND':
            # ALL conditions must match
            for condition in conditions:
                if not self._matches_condition(transaction_data, condition):
                    return False
            return True
        else:  # OR logic
            # ANY condition must match
            for condition in conditions:
                if self._matches_condition(transaction_data, condition):
                    return True
            return False
    
    def _matches_condition(self, transaction_data, condition):
        """Check if transaction matches a specific condition"""
        if condition.condition_type == 'KEYWORD':
            return self._matches_keyword_condition(transaction_data, condition)
        elif condition.condition_type == 'AMOUNT':
            return self._matches_amount_condition(transaction_data, condition)
        elif condition.condition_type == 'DATE':
            return self._matches_date_condition(transaction_data, condition)
        elif condition.condition_type == 'SOURCE':
            return self._matches_source_condition(transaction_data, condition)
        return False
    
    def _matches_keyword_condition(self, transaction_data, condition):
        """Check keyword condition - matches against description, category, or user_label"""
        keyword = condition.keyword.lower().strip()
        
        if not keyword:
            return False
        
        # Check description
        description = transaction_data.get('description', '').lower()
        
        # Check category (including user-edited category)
        category = transaction_data.get('category', '').lower()
        
        # Check user_label (subcategory/label)
        user_label = transaction_data.get('user_label', '').lower().strip()
        
        # Combine all fields for matching
        search_fields = [description, category, user_label]
        
        # Apply matching logic based on condition type
        if condition.keyword_match_type == 'CONTAINS':
            # Check if keyword is contained in ANY of the fields
            return any(keyword in field for field in search_fields if field)
        elif condition.keyword_match_type == 'STARTS_WITH':
            # Check if ANY field starts with keyword
            return any(field.startswith(keyword) for field in search_fields if field)
        elif condition.keyword_match_type == 'ENDS_WITH':
            # Check if ANY field ends with keyword
            return any(field.endswith(keyword) for field in search_fields if field)
        elif condition.keyword_match_type == 'EXACT':
            # Check if keyword exactly matches ANY field
            return any(field == keyword for field in search_fields if field)
        return False
    
    def _matches_amount_condition(self, transaction_data, condition):
        """Check amount condition"""
        amount = float(transaction_data.get('amount', 0))
        amount_value = float(condition.amount_value or 0)
        
        if condition.amount_operator == 'EQUALS':
            return amount == amount_value
        elif condition.amount_operator == 'GREATER_THAN':
            return amount > amount_value
        elif condition.amount_operator == 'LESS_THAN':
            return amount < amount_value
        elif condition.amount_operator == 'BETWEEN':
            amount_value2 = float(condition.amount_value2 or 0)
            return amount_value <= amount <= amount_value2
        elif condition.amount_operator == 'GREATER_THAN_EQUAL':
            return amount >= amount_value
        elif condition.amount_operator == 'LESS_THAN_EQUAL':
            return amount <= amount_value
        return False
    
    def _matches_date_condition(self, transaction_data, condition):
        """Check date condition"""
        date = transaction_data.get('date')
        if not date:
            return False
        
        # Ensure date is a date object
        if isinstance(date, str):
            from datetime import datetime
            try:
                date = datetime.strptime(date, '%Y-%m-%d').date()
            except:
                return False
        
        if condition.date_start and condition.date_end:
            return condition.date_start <= date <= condition.date_end
        elif condition.date_start:
            return date >= condition.date_start
        elif condition.date_end:
            return date <= condition.date_end
        return False
    
    def _matches_source_condition(self, transaction_data, condition):
        """Check source/channel condition"""
        description = transaction_data.get('description', '').lower()
        source = condition.source_channel.lower()
        
        if not source:
            return False
            
        # Basic source detection
        source_keywords = {
            'paytm': ['paytm'],
            'phonepe': ['phonepe', 'phone pe'],
            'google_pay': ['google pay', 'gpay', 'googlepay'],
            'upi': ['upi', 'immediate payment service'],
            'debit_card': ['debit card', 'dc', 'atm card'],
            'credit_card': ['credit card', 'cc'],
            'net_banking': ['net banking', 'internet banking'],
            'cheque': ['cheque', 'chq'],
            'neft': ['neft'],
            'rtgs': ['rtgs'],
        }
        
        if source in source_keywords:
            keywords = source_keywords[source]
            return any(keyword in description for keyword in keywords)
        
        return False

def categorize_with_rules(transaction_data, user):
    """Enhanced categorization using rules engine"""
    engine = RulesEngine(user)
    rule_category = engine.apply_rules_to_transaction(transaction_data)
    
    if rule_category:
        return rule_category
    
    # Fallback to original keyword-based categorization
    from .pdf_parser import categorize_transaction
    return categorize_transaction(
        transaction_data['description'],
        transaction_data['amount'],
        transaction_data['transaction_type']
    )


# ============= CUSTOM CATEGORY RULES ENGINE =============

class CustomCategoryRulesEngine:
    """Engine to apply custom category rules to transactions"""
    
    def __init__(self, user):
        self.user = user
        from .models import CustomCategoryRule
        self.rules = CustomCategoryRule.objects.filter(user=user, is_active=True).prefetch_related('conditions')
    
    def apply_rules_to_transaction(self, transaction_data):
        """Apply all custom category rules to a transaction and return matching category"""
        for rule in self.rules:
            if self._matches_rule(transaction_data, rule):
                return rule.custom_category
        return None
    
    def find_matching_rule(self, transaction_data):
        """Return the CustomCategoryRule object that matches the transaction, or None."""
        for rule in self.rules:
            if self._matches_rule(transaction_data, rule):
                return rule
        return None
    
    def _matches_rule(self, transaction_data, rule):
        """Check if transaction matches a specific custom category rule"""
        conditions = rule.conditions.all()
        
        if not conditions.exists():
            return False
        
        if rule.rule_type == 'AND':
            # ALL conditions must match
            for condition in conditions:
                if not self._matches_condition(transaction_data, condition):
                    return False
            return True
        else:  # OR logic
            # ANY condition must match
            for condition in conditions:
                if self._matches_condition(transaction_data, condition):
                    return True
            return False
    
    def _matches_condition(self, transaction_data, condition):
        """Check if transaction matches a specific custom category condition"""
        if condition.condition_type == 'KEYWORD':
            return self._matches_keyword_condition(transaction_data, condition)
        elif condition.condition_type == 'AMOUNT':
            return self._matches_amount_condition(transaction_data, condition)
        elif condition.condition_type == 'DATE':
            return self._matches_date_condition(transaction_data, condition)
        return False
    
    def _matches_keyword_condition(self, transaction_data, condition):
        """Check keyword condition - matches against description, category, or user_label"""
        keyword = condition.keyword.lower().strip()
        
        if not keyword:
            return False
        
        # Check description
        description = transaction_data.get('description', '').lower()
        
        # Check category (including user-edited category)
        category = transaction_data.get('category', '').lower()
        
        # Check user_label (subcategory/label)
        user_label = transaction_data.get('user_label', '').lower().strip()
        
        # Combine all fields for matching
        search_fields = [description, category, user_label]
        
        # Apply matching logic based on condition type
        if condition.keyword_match_type == 'CONTAINS':
            # Check if keyword is contained in ANY of the fields
            return any(keyword in field for field in search_fields if field)
        elif condition.keyword_match_type == 'STARTS_WITH':
            # Check if ANY field starts with keyword
            return any(field.startswith(keyword) for field in search_fields if field)
        elif condition.keyword_match_type == 'ENDS_WITH':
            # Check if ANY field ends with keyword
            return any(field.endswith(keyword) for field in search_fields if field)
        elif condition.keyword_match_type == 'EXACT':
            # Check if keyword exactly matches ANY field
            return any(field == keyword for field in search_fields if field)
        return False
    
    def _matches_amount_condition(self, transaction_data, condition):
        """Check amount condition"""
        amount = float(transaction_data.get('amount', 0))
        amount_value = float(condition.amount_value or 0)
        
        if condition.amount_operator == 'EQUALS':
            return amount == amount_value
        elif condition.amount_operator == 'GREATER_THAN':
            return amount > amount_value
        elif condition.amount_operator == 'LESS_THAN':
            return amount < amount_value
        elif condition.amount_operator == 'BETWEEN':
            amount_value2 = float(condition.amount_value2 or 0)
            return amount_value <= amount <= amount_value2
        elif condition.amount_operator == 'GREATER_THAN_EQUAL':
            return amount >= amount_value
        elif condition.amount_operator == 'LESS_THAN_EQUAL':
            return amount <= amount_value
        return False
    
    def _matches_date_condition(self, transaction_data, condition):
        """Check date condition"""
        date = transaction_data.get('date')
        if not date:
            return False
        
        if condition.date_start and date < condition.date_start:
            return False
        if condition.date_end and date > condition.date_end:
            return False
        
        return True
    
    @staticmethod
    def _matches_rule_static(transaction_data, rule):
        """Static method to check if transaction matches a specific custom category rule (without needing self)"""
        conditions = rule.conditions.all()
        
        if not conditions.exists():
            return False
        
        if rule.rule_type == 'AND':
            # ALL conditions must match
            for condition in conditions:
                if not CustomCategoryRulesEngine._matches_condition_static(transaction_data, condition):
                    return False
            return True
        else:  # OR logic
            # ANY condition must match
            for condition in conditions:
                if CustomCategoryRulesEngine._matches_condition_static(transaction_data, condition):
                    return True
            return False
    
    @staticmethod
    def _matches_condition_static(transaction_data, condition):
        """Static method to check condition"""
        if condition.condition_type == 'KEYWORD':
            return CustomCategoryRulesEngine._matches_keyword_condition_static(transaction_data, condition)
        elif condition.condition_type == 'AMOUNT':
            return CustomCategoryRulesEngine._matches_amount_condition_static(transaction_data, condition)
        elif condition.condition_type == 'DATE':
            return CustomCategoryRulesEngine._matches_date_condition_static(transaction_data, condition)
        return False
    
    @staticmethod
    def _matches_keyword_condition_static(transaction_data, condition):
        """Check keyword condition (static)"""
        description = transaction_data.get('description', '').lower()
        keyword = condition.keyword.lower()
        
        if not keyword:
            return False
            
        if condition.keyword_match_type == 'CONTAINS':
            return keyword in description
        elif condition.keyword_match_type == 'STARTS_WITH':
            return description.startswith(keyword)
        elif condition.keyword_match_type == 'ENDS_WITH':
            return description.endswith(keyword)
        elif condition.keyword_match_type == 'EXACT':
            return description == keyword
        return False
    
    @staticmethod
    def _matches_amount_condition_static(transaction_data, condition):
        """Check amount condition (static)"""
        amount = float(transaction_data.get('amount', 0))
        amount_value = float(condition.amount_value or 0)
        
        if condition.amount_operator == 'EQUALS':
            return amount == amount_value
        elif condition.amount_operator == 'GREATER_THAN':
            return amount > amount_value
        elif condition.amount_operator == 'LESS_THAN':
            return amount < amount_value
        elif condition.amount_operator == 'BETWEEN':
            amount_value2 = float(condition.amount_value2 or 0)
            return amount_value <= amount <= amount_value2
        elif condition.amount_operator == 'GREATER_THAN_EQUAL':
            return amount >= amount_value
        elif condition.amount_operator == 'LESS_THAN_EQUAL':
            return amount <= amount_value
        return False
    
    @staticmethod
    def _matches_date_condition_static(transaction_data, condition):
        """Check date condition (static)"""
        date = transaction_data.get('date')
        if not date:
            return False
        
        if condition.date_start and date < condition.date_start:
            return False
        if condition.date_end and date > condition.date_end:
            return False
        
        return True