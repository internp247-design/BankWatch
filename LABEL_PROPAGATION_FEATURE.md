# Label Propagation Feature Implementation

## Overview

The label propagation feature is a key part of the BankWatch classification system that automatically applies labels (user-entered subcategories) to newly classified transactions. This creates a learning mechanism where users only need to manually label transactions once - subsequent similar transactions automatically inherit the label.

## Feature Flow

### 1. User Labels Manually Edited Transactions

When a user edits a transaction's category and optionally adds a label:
- The transaction is marked with `is_manually_edited = True`
- The label is stored in `transaction.user_label`
- The category is stored in `transaction.category`

Example:
```
Transaction: "SuperMarket Fresh Foods"
Category: Food & Dining
User Label: Groceries
```

### 2. Classification with Label Propagation

When rules are applied to new transactions, the system now:

1. **Priority 1: User Label-Based Matching**
   - Checks if new transaction's description contains any user label text
   - Looks through all manually edited transactions for label matches
   - If a match is found, applies both the category AND the label

2. **Priority 2: Custom Category Rules**
   - If no user label match, applies custom category rules
   - Returns the matched category name as the label
   - This labels the transaction with the custom category name

3. **Priority 3: Standard Rules**
   - If no custom category matched, applies standard rules
   - Returns the rule's category as the label

### 3. Label Application

When a classification is applied, the system now:
- Sets the `transaction.category` to the matched category
- Sets the `transaction.user_label` to the propagated label
- Does NOT mark transaction as manually edited (preserves auto-apply behavior)

## Code Changes

### 1. UserLabelClassificationEngine (`analyzer/user_label_engine.py`)

Enhanced to return matched label:

```python
def find_matching_category_by_label(self, transaction_data):
    """
    Find a matching category for a transaction based on user labels.
    Returns dict with:
    - matched_custom_category: CustomCategory object
    - matched_custom_category_id: Integer ID
    - matched_custom_category_name: String name
    - matched_label: String label to propagate
    - source: String indicating match type
    """
```

### 2. RulesEngine Update (`analyzer/views.py` - `apply_rules()`)

Updated to use priority-based classification with label propagation:

```python
# PRIORITY 1: Check for user label-based matches
if transaction.user_label and transaction.user_label.strip():
    label_match = user_label_engine.find_matching_category_by_label(tx_data)
    if label_match:
        matched_custom_category = label_match.get('matched_custom_category')
        propagated_label = label_match.get('matched_label')

# PRIORITY 2: Check custom category rules
if not category:
    matched_custom_category = custom_category_engine.apply_rules_to_transaction(tx_data)
    if matched_custom_category:
        propagated_label = matched_custom_category.name

# PRIORITY 3: Check standard rules
if not category:
    matched_rule = engine.find_matching_rule(tx_data)
    if matched_rule:
        propagated_label = matched_rule.category

# Apply category and propagated label
if category and category != transaction.category:
    transaction.category = category
    if propagated_label:
        transaction.user_label = propagated_label
    transaction.save()
```

### 3. Classification Results (`analyzer/views.py` - `rules_application_results()`)

Added `propagated_label` to results dictionary:

```python
results.append({
    'transaction_id': tx.id,
    'category': matched_custom_category_name,
    'propagated_label': propagated_label,  # NEW FIELD
    # ... other fields
})
```

## Database Schema

No new database fields were required. The feature uses existing fields:

- `Transaction.user_label` (CharField, nullable) - Stores the propagated label
- `Transaction.category` (CharField) - Stores the category
- `Transaction.is_manually_edited` (BooleanField) - Marks manual edits to prevent overwriting
- `CustomCategory.name` (CharField) - Used as label when custom category matched
- `Rule.category` (CharField) - Used as label when rule matched

## User Experience

### Before (Manual Process)

1. User receives 10 transactions for grocery stores
2. User manually edits each one to:
   - Category: Food & Dining
   - Label: Groceries
3. Each transaction requires individual editing

### After (With Label Propagation)

1. User manually labels first grocery transaction with "Groceries"
2. User applies rules
3. Next 9 grocery transactions are:
   - Automatically categorized as "Food & Dining"
   - Automatically labeled as "Groceries"
4. User can further refine with custom rules or more labeled examples

## Classification Priority Example

```
Transaction: "Whole Foods Downtown"

Priority 1: Check user labels
  - Look for labeled transactions with "Whole Foods" or "Foods" in description
  - If found: Use that transaction's category and label

Priority 2: Check custom categories
  - Apply custom category rules (e.g., keywords: grocery, whole foods)
  - If matched: Use category name as label

Priority 3: Check standard rules
  - Apply user-defined rules
  - If matched: Use rule's category as label

Result: Category = "Food & Dining", Label = "Groceries" (propagated)
```

## Testing

Run the test suite:

```bash
python test_label_propagation.py
```

Expected results:
- ✓ Custom category rules matching works
- ✓ Label propagation applies category name
- ✓ Priority-based classification respects order
- ✓ Labels are correctly stored in database

## API Reference

### UserLabelClassificationEngine

**Initialization:**
```python
from analyzer.user_label_engine import UserLabelClassificationEngine
engine = UserLabelClassificationEngine(user)
```

**Main Method:**
```python
match = engine.find_matching_category_by_label(transaction_data)
# transaction_data must have keys: date, description, amount, transaction_type, user_label

if match:
    category = match['matched_custom_category']  # CustomCategory object
    label = match['matched_label']  # String to propagate
    source = match['source']  # 'user_label_category_match' or 'custom_category_name_match'
```

**Confidence Scoring:**
```python
confidence = engine.get_transaction_label_confidence(label_text, description)
# Returns 0.0 (no match) to 1.0 (perfect match)
```

## Benefits

1. **Reduced Manual Work**: Users label once, system applies automatically
2. **Consistent Labeling**: Similar transactions get consistent labels
3. **Learning System**: System learns from user edits and applies patterns
4. **Flexibility**: Works with custom categories, rules, and user labels
5. **Priority-Based**: Respects priority order to prevent rule conflicts

## Future Enhancements

1. **ML-Based Matching**: Use similarity scoring beyond keyword matching
2. **Confidence Scoring**: Display confidence of auto-applied labels
3. **Batch Label Management**: Apply labels to multiple transactions at once
4. **Label Suggestions**: Suggest labels based on transaction patterns
5. **Label History**: Track how labels were propagated for audit trail

## Troubleshooting

### Labels Not Being Propagated

**Issue**: Transactions are categorized but labels aren't applied

**Solution**: 
- Check if source transactions have `is_manually_edited = True`
- Verify `user_label` field is populated on source transactions
- Ensure custom categories exist for label matching

### Custom Category Matching Not Working

**Issue**: Custom category rules aren't matching transactions

**Solution**:
- Verify custom category has active rules
- Check rule conditions match transaction data
- Enable debug logging in CustomCategoryRulesEngine

### Manually Edited Transactions Being Overwritten

**Issue**: User edits are being overwritten by rules

**Solution**:
- Apply rules BEFORE manually editing transactions
- Check `is_manually_edited` flag is True on edited transactions
- Note: apply_rules() skips transactions with `is_manually_edited = True`

## Integration with Existing Features

### Transaction Editing (`update_transaction_category` AJAX)
- When user edits transaction via UI, label can be set
- Marks transaction with `is_manually_edited = True`
- Subsequent rule application skips this transaction

### Rules Application (`apply_rules` view)
- Now integrates with all three engines in priority order
- Applies both category and propagated label
- Preserves manually edited transactions

### Results Display (`rules_application_results` view)
- Shows which transactions were matched
- Displays the category that would be applied
- Includes propagated label in results

### PDF/Excel Export
- Export includes propagated labels in results
- Labels visible in confirmation pages
- Can be used for audit trails

## Configuration

The feature uses sensible defaults:

```python
# Priority order (cannot be changed without code modification)
PRIORITY_1 = 'User Label-Based Matching'
PRIORITY_2 = 'Custom Category Rules'
PRIORITY_3 = 'Standard Rules'

# Minimum label match length (customizable in get_transaction_label_confidence)
MIN_LABEL_LENGTH = 2  # characters

# Label matching is case-insensitive
# Whitespace is trimmed automatically
```

To customize, modify `UserLabelClassificationEngine.__init__()` and the classification logic in `apply_rules()`.
