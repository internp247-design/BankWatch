"""
User Label Classification Engine

Classifies transactions based on user-edited labels.
User-edited labels are the PRIMARY signal for category assignment.
This engine matches new transactions against labels of previously edited transactions.
"""

from .models import Transaction, CustomCategory


class UserLabelClassificationEngine:
    """
    Engine to classify transactions based on user-edited labels.
    
    Priority:
    1. User-edited labels matching category names (highest)
    2. Custom category keyword match
    3. Standard rules (lowest)
    """
    
    def __init__(self, user):
        self.user = user
    
    def find_matching_category_by_label(self, transaction_data):
        """
        Find a matching custom category based on user-edited labels.
        
        Args:
            transaction_data: dict with 'description', 'user_label', etc.
        
        Returns:
            dict with matched_custom_category and match source, or None if no match
        """
        # Get the search text (description + label)
        description = transaction_data.get('description', '').lower().strip()
        user_label = transaction_data.get('user_label', '').lower().strip()
        search_text = f"{description} {user_label}".strip()
        
        if not search_text:
            return None
        
        # PRIORITY 1: Check user-created custom categories for name match
        custom_categories = CustomCategory.objects.filter(
            user=self.user,
            is_active=True
        )
        
        for category in custom_categories:
            category_name = category.name.lower().strip()
            if not category_name:
                continue
            
            # Exact match or contains match (highest priority)
            if category_name == description or category_name in description:
                return {
                    'matched_custom_category': category,
                    'matched_custom_category_id': category.id,
                    'matched_custom_category_name': category.name,
                    'matched_label': category.name,  # Use category name as label
                    'source': 'custom_category_name_match'
                }
        
        # PRIORITY 2: Check user labels from edited transactions
        # Find all transactions with user labels that were manually edited
        labeled_transactions = Transaction.objects.filter(
            statement__account__user=self.user,
            is_manually_edited=True,
            user_label__isnull=False
        ).exclude(user_label__exact='').values_list('user_label', 'category').distinct()
        
        best_match = None
        best_label_length = 0
        best_category = None
        best_label_text = None
        
        for label, category in labeled_transactions:
            if not label:
                continue
            
            label_lower = label.lower().strip()
            
            # Check if label appears in description
            if label_lower in description:
                # Prefer longer, more specific matches
                if len(label_lower) > best_label_length:
                    best_label_length = len(label_lower)
                    best_match = label
                    best_category = category
                    best_label_text = label  # Store the actual label text
        
        # If we found a user label match, try to find corresponding custom category
        if best_category and best_match:
            # Try to find a custom category with matching name
            for category in custom_categories:
                if category.name.lower().strip() == best_match.lower().strip():
                    return {
                        'matched_custom_category': category,
                        'matched_custom_category_id': category.id,
                        'matched_custom_category_name': category.name,
                        'matched_label': best_label_text,  # Return the matched label text
                        'source': 'user_label_category_match'
                    }
        
        return None
    
    def get_transaction_label_confidence(self, user_label, description):
        """
        Calculate confidence score for a user label matching a transaction description.
        
        Args:
            user_label: User-entered label text
            description: Transaction description
        
        Returns:
            float 0.0 to 1.0 (higher = stronger match)
        """
        if not user_label or not description:
            return 0.0
        
        user_label_lower = user_label.lower().strip()
        description_lower = description.lower().strip()
        
        # Exact match (highest confidence)
        if user_label_lower == description_lower:
            return 1.0
        
        # Substring match (high confidence)
        if user_label_lower in description_lower:
            # Score based on percentage of description matched
            match_ratio = len(user_label_lower) / len(description_lower)
            return min(0.9, 0.5 + (match_ratio * 0.4))  # 0.5 to 0.9
        
        # Word-level match (medium confidence)
        user_words = set(user_label_lower.split())
        desc_words = set(description_lower.split())
        common_words = user_words & desc_words
        
        if common_words:
            match_ratio = len(common_words) / len(user_words)
            return match_ratio * 0.4  # 0.0 to 0.4
        
        return 0.0
