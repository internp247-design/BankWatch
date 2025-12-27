# Quick Reference: Rules & Categories Filtering

## What Changed

### Before
- ❌ Selected 1 rule → showed ALL rules' transactions
- ❌ Selected 1 category → showed ALL categories' transactions  
- ❌ Excel/PDF downloads included all transactions regardless of filter

### After
- ✅ Selected 1 rule → shows ONLY that rule's transactions
- ✅ Selected 1 category → shows ONLY that category's transactions
- ✅ Excel/PDF downloads include ONLY visible (filtered) transactions
- ✅ Summary metrics update based on filtered results

---

## Step-by-Step User Guide

### Apply Rules Filter:
1. On `/analyzer/rules/apply/results/` page
2. Click "Apply Rules to Transactions" button (blue)
3. Check the checkboxes next to the rules you want
4. Click "Apply Filter" button
5. Table updates to show ONLY transactions matching those rules
6. Summary shows filtered count, amount, etc.

### Apply Category Filter:
1. Click "Apply Custom Category to Transactions" button (green)
2. Check the checkboxes next to the categories you want
3. Click "Apply Filter" button
4. Table updates to show ONLY transactions matching those categories
5. Summary shows filtered count, amount, etc.

### Apply Both Rules AND Categories:
1. Check boxes in BOTH panels
2. Click either filter button
3. Table shows transactions matching **EITHER** rules **OR** categories
4. Download buttons work with this combined filter

### Download Filtered Data:
1. After applying filters, click "Download Excel" or "Download PDF"
2. Downloaded file contains **ONLY** the visible filtered rows
3. Summary sections show selected rules/categories context

### Clear Filters:
- Click "Clear Filter" button
- OR uncheck all boxes and click again
- Table returns to showing ALL transactions

---

## Implementation Summary

| Component | Change |
|-----------|--------|
| Rule Filtering Logic | Extracts rule names from checkboxes and matches exactly |
| Category Filtering | Uses AJAX to get matching transactions, filters by ID |
| Export Excel | Collects visible rows, passes as transaction_ids |
| Export PDF | Collects visible rows, passes as transaction_ids |
| Summary Updates | Recalculates based on visible rows only |
| Filter Clearing | Unchecks all boxes and shows all transactions |

---

## Files Changed

- `templates/analyzer/apply_rules_results.html` - Main filtering and export logic
  - Lines 750-870: `filterTransactionsByRulesAndCategories()` 
  - Lines 585-680: `downloadRulesExcel()`
  - Lines 524-580: `downloadRulesPDF()`

---

## Testing The Fix

### Test 1: Single Rule Filter
1. Go to results page with transactions
2. Select 1 rule checkbox
3. Click "Apply Filter"
4. ✓ Verify only transactions with that rule name in "Matched Rule" column are shown
5. Download Excel
6. ✓ Verify Excel contains only those rows

### Test 2: Multiple Rules
1. Select 2+ rule checkboxes
2. Click "Apply Filter"
3. ✓ Verify transactions matching ANY of selected rules are shown
4. ✓ Summary shows correct transaction count

### Test 3: Category Filter
1. Select 1+ category checkboxes
2. Click "Apply Filter"
3. ✓ Verify only transactions matching category are shown
4. Download PDF
5. ✓ Verify PDF contains only filtered rows

### Test 4: Combined Filters
1. Select rules AND categories
2. Click either filter button
3. ✓ Verify OR logic: shows if matches rule OR category
4. Download both formats
5. ✓ Both include only visible rows

### Test 5: Clear Filters
1. Apply filters to reduce table
2. Click "Clear Filter"
3. ✓ Verify all transactions reappear
4. ✓ Summary resets to total count

---

## Key Technical Notes

- **Rule Matching**: Name-based (text in badge)
- **Category Matching**: ID-based (AJAX returns list of IDs)
- **Filter Combination**: OR logic (matches rule OR category)
- **Export Strategy**: Collect transaction IDs from visible rows, send to backend
- **Summary**: Updates dynamically using `updateSummary()` function

---

## Rollback (if needed)

The changes are CSS/JavaScript only in the template. To rollback:
1. Restore original `apply_rules_results.html` from git
2. No database changes required
3. No backend changes required
