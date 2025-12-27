# Technical Architecture: Rules & Categories Filtering System

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Results Page (/rules/apply/results/)         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐        ┌──────────────────────────┐  │
│  │  Rules Filter Panel  │        │ Categories Filter Panel  │  │
│  ├──────────────────────┤        ├──────────────────────────┤  │
│  │ □ Rule 1            │        │ □ Category A             │  │
│  │ □ Rule 2            │        │ □ Category B             │  │
│  │ □ Rule 3            │        │ □ Category C             │  │
│  │ [Apply Filter] btn   │        │ [Apply Filter] btn       │  │
│  └──────────────────────┘        └──────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Transaction Table                                      │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Date | Account | Desc | Amount | Category | Rule | Cat │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ 2024 │ Account │ ...  │ 500    │ ...      │Rule1│Cat-A│   │
│  │ 2024 │ Account │ ...  │ 200    │ ...      │ -   │Cat-B│   │
│  │ ...  │         │      │        │          │     │     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ [Download Excel] [Download PDF] [Clear Filter]           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Scenario 1: Apply Rules Filter

```
User checks "Rule 1" checkbox
         ↓
User clicks "Apply Filter"
         ↓
JavaScript: applyRulesFilter()
         ↓
JavaScript: filterTransactionsByRulesAndCategories([rule_id], [])
         ↓
For each transaction row in table:
  - Get "Matched Rule" cell value (e.g., "Rule 1")
  - Get selected rule names from checkboxes (Set: {"Rule 1"})
  - If matched rule name in selected set: show row
  - Else: hide row
         ↓
updateSummary() recalculates visible row count
         ↓
Table displays only matching transactions
```

### Scenario 2: Apply Categories Filter

```
User checks "Category A" checkbox
         ↓
User clicks "Apply Filter"
         ↓
JavaScript: applyRulesCustomCategoryFilter()
         ↓
AJAX POST: /analyzer/apply-custom-category-rules/
         ↓
Backend returns: {
  "matched_transaction_ids": [1, 3, 5, 7],
  "success": true
}
         ↓
JavaScript: filterTransactionsByRulesAndCategories([], [cat_id], [1,3,5,7])
         ↓
For each transaction row:
  - Get transaction ID
  - Check if ID in matched_transaction_ids list
  - If yes: show row
  - Else: hide row
         ↓
updateSummary() recalculates
         ↓
Table displays only matching transactions
```

### Scenario 3: Download Filtered Excel

```
User applies rules filter (rows visible: 1,2,4,5)
         ↓
User clicks "Download Excel"
         ↓
JavaScript: downloadRulesExcel()
         ↓
Collect visible transaction IDs: [1, 2, 4, 5]
Collect rule IDs: [rule_id_1]
Collect category IDs: []
         ↓
POST Form to /analyzer/export/rules-results/
Parameters:
  - transaction_ids: [1, 2, 4, 5]
  - rule_ids: [rule_id_1]
  - category_ids: []
         ↓
Backend: export_rules_results_to_excel()
         ↓
Query: Transaction.objects.filter(id__in=[1,2,4,5])
         ↓
Generate Excel with only those 4 transactions
         ↓
Add summary showing:
  - Selected Rules: Rule 1
  - Selected Categories: NULL
  - Total Transactions: 4
         ↓
Return Excel file to browser
```

## Code Flow: Filter Application

### Entry Point
```javascript
// User clicks "Apply Filter" button
applyRulesFilter()
  ├─ Collect checked rule IDs: ruleIds
  ├─ Collect checked category IDs: categoryIds
  ├─ Call: filterTransactionsByRulesAndCategories(ruleIds, categoryIds)
  └─ updateSummary()
```

### Core Filtering Logic
```javascript
filterTransactionsByRulesAndCategories(ruleIds, categoryIds, matchedCategoryIds)
  ├─ Extract rule names from checkboxes → selectedRuleNames (Set)
  ├─ Extract category names from checkboxes → selectedCategoryNames (Set)
  │
  ├─ For each transaction row in table:
  │   ├─ Get matched rule name from "Matched Rule" column
  │   ├─ Get matched category name from "Matched Category" column
  │   │
  │   ├─ Decision logic:
  │   │  ├─ If no filters: hide row
  │   │  ├─ If only rules: show if matchedRuleName in selectedRuleNames
  │   │  ├─ If only categories: show if transactionID in matchedCategoryIds OR matched category matches
  │   │  ├─ If both: show if matched rule OR matched category matches (OR logic)
  │   │
  │   └─ Apply display style: '' (show) or 'none' (hide)
  │
  └─ updateAppliedFiltersDisplay()
```

## Data Structures

### Rule Filter Selection
```javascript
ruleIds = ['1', '3', '5']  // from checkboxes

selectedRuleNames = new Set()
// Extract from: label → badge → textContent + nextSibling
selectedRuleNames = {"Rule A", "Rule C", "Rule E"}
```

### Category Filter Selection
```javascript
categoryIds = ['2', '4']  // from checkboxes

selectedCategoryNames = new Set()
// Extract from: label → textContent (full text)
selectedCategoryNames = {"Category X", "Category Y"}

// From AJAX response:
matchedCategoryTransactionIds = [10, 15, 23, 45]  // transaction IDs
```

### Table Row Matching
```javascript
// For each row:
row.getAttribute('data-transaction-id')  // e.g., "10"
cells[6].querySelector('.badge')?.textContent  // e.g., "Rule A"
cells[7].querySelector('.badge')?.textContent  // e.g., "Category X"
```

## Export Process

### Excel Export
```javascript
downloadRulesExcel()
  ├─ Get visible table rows (where display !== 'none')
  ├─ Collect transaction IDs: [1, 2, 4, 5]
  ├─ Get selected rule IDs and category IDs
  │
  ├─ Create POST form with:
  │   ├─ transaction_ids (query params)
  │   ├─ rule_ids (hidden fields)
  │   ├─ category_ids (hidden fields)
  │   └─ csrfmiddlewaretoken
  │
  └─ Submit form to /analyzer/export/rules-results/
```

### PDF Export
```javascript
downloadRulesPDF()
  ├─ Get visible table rows
  ├─ Collect transaction IDs
  ├─ Get selected rule/category IDs
  │
  ├─ Create POST form with same parameters
  │
  └─ Submit form to /analyzer/export/rules-results-pdf/
```

## Backend Processing

### Export Function Flow
```python
# views.py: export_rules_results_to_excel(request)

def export_rules_results_to_excel(request):
    # Get parameters
    transaction_ids = request.GET.getlist('transaction_ids')  # [1, 2, 4, 5]
    selected_rule_ids = request.POST.getlist('rule_ids')      # [rule_id]
    selected_category_ids = request.POST.getlist('category_ids')
    
    # Fetch only requested transactions
    all_transactions = Transaction.objects.filter(
        id__in=transaction_ids,
        statement__account__user=request.user
    )
    
    # Fetch metadata about selected rules/categories
    selected_rules = Rule.objects.filter(
        id__in=selected_rule_ids,
        user=request.user
    )
    
    # Build Excel workbook
    wb = Workbook()
    
    # Add headers, summary, and transaction data
    for transaction in all_transactions:
        # Add row to sheet
        
    # Set metadata showing selected rules/categories
    
    # Return Excel file
```

## State Management

### Session State
- `last_rules_applied_ids`: List of transaction IDs updated by last apply
- `last_rules_applied_prev`: Map of transaction ID → previous category
- `last_rules_applied_rule`: Map of transaction ID → matched rule name

### DOM State
- Checkbox states (checked/unchecked)
- Table row visibility (display style)
- Panel visibility (hidden/shown)
- Summary numbers (updated in real-time)

## Browser Compatibility

- Uses modern JavaScript (ES6+)
- DOM Query API (querySelectorAll, etc.)
- FormData and POST requests
- Set data structure for deduplication
- Template literals for URL building

## Performance Considerations

- Filtering is client-side only (no server calls for rules)
- Categories require AJAX call (once per filter)
- Summary updates are O(n) where n = visible rows
- Export collects transaction IDs in O(n) time
- No pagination used (assumes <5000 transactions per page)

## Error Handling

- Checks for empty selections before filtering
- Validates checkbox elements before extracting names
- Graceful fallback if row has no transaction ID
- Alert messages for user feedback
- Console logging for debugging

## Security

- CSRF token included in all POST requests
- Server-side permission checks (user=request.user)
- Transaction IDs sanitized on backend
- No sensitive data in JavaScript

---

## Future Improvements

1. Add pagination for large result sets
2. Cache rule name mappings to reduce DOM queries
3. Debounce filter updates for better UX
4. Add filter persistence in localStorage
5. Implement client-side search within filtered results
6. Add bulk actions (select/deselect all)
