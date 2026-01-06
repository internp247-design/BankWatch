# User Label Classification Feature

## Overview

The User Label Classification Engine implements a priority-based transaction categorization system that makes **user-edited labels the primary signal** for category assignment. This allows the system to learn from user edits and apply them to future transactions automatically.

## How It Works

### Classification Priority

When a transaction is being categorized, the system follows this priority order:

```
1️⃣ USER-EDITED LABELS (HIGHEST PRIORITY)
   ├─ User-entered labels matching category names
   └─ Labels from previously edited transactions

2️⃣ CUSTOM CATEGORY RULES (MEDIUM PRIORITY)
   └─ User-created categories with keyword matching

3️⃣ STANDARD RULES (LOWEST PRIORITY)
   └─ Rules defined by user, only if above don't match
```

### Key Features

✅ **Persistent Learning**
- Once a user edits a transaction with a label, that label is saved
- Future transactions with similar descriptions use that label for classification
- Case-insensitive, trimmed text matching

✅ **Label-Based Matching**
- Transaction descriptions are matched against user-entered labels
- Custom category names are matched against transaction descriptions
- Longer, more specific matches are preferred over shorter ones

✅ **Manual Edits Are Protected**
- When applying rules, manually edited transactions are always skipped
- User labels are never overwritten by automatic rules
- You control which transactions are auto-classified

✅ **Result Page Accuracy**
- Categories listed on the results page reflect actual label matches
- Pie charts show correct totals based on label-matched categories
- Summary tables include only transactions with confirmed matches

## Implementation Details

### New Files

**`analyzer/user_label_engine.py`**
- Contains `UserLabelClassificationEngine` class
- Handles label-based transaction classification
- Manages confidence scoring for matches

### Modified Files

**`analyzer/views.py`**
- Updated `rules_application_results()` function
- Added priority-based classification logic
- Integrated user label engine into transaction processing

### Database Fields Used

- `Transaction.user_label` - User-entered label/subcategory
- `Transaction.is_manually_edited` - Whether user edited the transaction
- `CustomCategory.name` - Custom category name for matching
- `CustomCategory.is_active` - Only active categories are considered

## Usage Example

### Scenario: User Edits a Transaction

1. User views account details
2. Finds transaction: "Starbucks Coffee Shop - $5.50"
3. Clicks category badge to edit
4. Changes category to "Food" and adds label: "Coffee"
5. Saves changes

### What Happens Next

When the user applies rules or views the results page:

1. System encounters another transaction: "Starbucks Downtown - $6.25"
2. Checks user labels from edited transactions
3. Finds "Coffee" in the label matches
4. Automatically classifies new transaction with same category as the original edit
5. On results page, both show under the same category with correct totals

### Rules Still Work

If a transaction doesn't match any user label:

1. System checks custom category rules
2. Then checks standard rules
3. This ensures rules aren't ignored, just deprioritized behind user edits

## Configuration

No configuration needed! The feature is automatic and works with:
- Existing user-created categories
- Existing rules
- Manually edited transactions

## API Reference

### UserLabelClassificationEngine

```python
from analyzer.user_label_engine import UserLabelClassificationEngine

engine = UserLabelClassificationEngine(user)

# Find matching category by label
result = engine.find_matching_category_by_label({
    'description': 'Coffee Shop Purchase',
    'user_label': 'Coffee'
})

# Result dictionary (if match found):
# {
#     'matched_custom_category': <CustomCategory object>,
#     'matched_custom_category_id': 123,
#     'matched_custom_category_name': 'Coffee',
#     'source': 'custom_category_name_match' or 'user_label_category_match'
# }

# Get confidence score
confidence = engine.get_transaction_label_confidence(
    'Coffee', 
    'Starbucks Coffee Shop'
)  # Returns: 0.5-0.9 (match found)
```

## Testing the Feature

### Manual Testing Steps

1. **Create a custom category** (e.g., "Coffee")
2. **Edit a transaction** with that label/category
3. **Go to Rules Apply page**
4. **View Results** - check if similar transactions are auto-classified
5. **Verify pie charts** show correct category totals

### Expected Behavior

- ✅ Manually edited transaction keeps its label
- ✅ Similar transactions are auto-classified to same category
- ✅ Results page shows correct category listings
- ✅ Pie charts reflect accurate category totals
- ✅ Rules are not applied to manually edited transactions

## Troubleshooting

### Issue: Transaction not being classified by label

**Check:**
1. Is the transaction marked as `is_manually_edited = True`?
2. Does it have a `user_label` entered?
3. Are there similar transactions to match against?

### Issue: Wrong category showing on results page

**Check:**
1. Verify the matched category in the database
2. Check if custom category names match user labels exactly
3. Ensure case and whitespace are trimmed

### Issue: Rules being applied instead of labels

**Check:**
1. Verify transaction is marked as manually edited
2. Confirm user label is not empty
3. Check priority order in `rules_application_results()` function

## Future Enhancements

Potential improvements:

- [ ] Fuzzy matching for labels (handle typos)
- [ ] Confidence scoring in results UI
- [ ] Bulk edit with label learning
- [ ] Label suggestions based on history
- [ ] A/B testing of classification accuracy

## Performance Considerations

The user label engine:
- Queries edited transactions from DB (O(n) where n = edited transactions)
- Performs string matching in Python (case-insensitive)
- Suitable for up to 10,000+ transactions

For optimization:
- Consider indexing `is_manually_edited` and `user_label` fields
- Cache labeled transactions for repeated use
- Implement batch processing for large rule applications

## Related Features

- [Transaction Editing Feature](TRANSACTION_EDITING_FEATURE.md) - Edit categories inline
- [Rules Engine](MASTER_DOCUMENTATION.md#rules-engine) - Define categorization rules
- [Custom Categories](MASTER_DOCUMENTATION.md#custom-categories) - Create custom categories

## Questions & Support

For issues or feature requests related to label classification:
1. Check this documentation
2. Review test files in `test_*.py`
3. Check Django debug logs
4. Verify database integrity
