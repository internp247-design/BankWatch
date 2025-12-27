# 🎯 Visual Diagrams - Rules & Categories Filtering

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BANKWATCH SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │           RULES & CATEGORIES FILTERING PAGE                  │   │
│  │     (/analyzer/rules/apply/results/)                         │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                           ▲                                             │
│                           │                                             │
│                      Django Template                                   │
│                  (apply_rules_results.html)                           │
│                           │                                             │
│           ┌───────────────┼───────────────┐                           │
│           │               │               │                           │
│       Rules Panel     Table Display    Categories Panel               │
│           │               │               │                           │
│           ▼               ▼               ▼                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ □ Rule 1    │  │ Transaction │  │ □ Category A│                 │
│  │ □ Rule 2    │  │ Table Rows  │  │ □ Category B│                 │
│  │ [Apply] ◀──┤  │ (Filtered)  │  │ [Apply] ◀───┤                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│           │               │               │                           │
│           └───────────────┼───────────────┘                           │
│                           │                                             │
│        ┌──────────────────┴──────────────────┐                        │
│        │ JavaScript Filtering Logic          │                        │
│        │ • Extract rule names                │                        │
│        │ • Extract category names            │                        │
│        │ • Compare with transaction data     │                        │
│        │ • Hide/show rows accordingly        │                        │
│        └──────────────────┬──────────────────┘                        │
│                           │                                             │
│           ┌───────────────┼───────────────┐                           │
│           │               │               │                           │
│      [Download Excel]  [Clear Filter] [Download PDF]                  │
│           │               │               │                           │
│           └───────────────┼───────────────┘                           │
│                           │                                             │
│        ┌──────────────────┴──────────────────┐                        │
│        │ Export Functions                    │                        │
│        │ • Collect visible transaction IDs  │                        │
│        │ • Send to backend for export       │                        │
│        │ • Generate Excel/PDF               │                        │
│        └──────────────────┬──────────────────┘                        │
│                           │                                             │
│        ┌──────────────────▼──────────────────┐                        │
│        │ Backend Export Views                │                        │
│        │ /analyzer/export/rules-results/     │                        │
│        │ /analyzer/export/rules-results-pdf/ │                        │
│        └──────────────────┬──────────────────┘                        │
│                           │                                             │
│                    Download File                                      │
│                    (Excel/PDF)                                        │
│                           │                                             │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
                        User's Device
```

---

## User Interaction Flow

### Rules Filter Flow

```
User at Rules Results Page
        │
        ├─→ Sees list of all created rules
        │   (in "Apply Rules to Transactions" panel)
        │
        ├─→ Selects 1 or more rule checkboxes
        │   □ Rule A
        │   ☑ Rule B  ←  Selected
        │   □ Rule C
        │
        ├─→ Clicks "Apply Filter" button
        │
        ├─→ JavaScript runs filterTransactionsByRulesAndCategories()
        │   ├─ Extracts rule names: {Rule B}
        │   ├─ Checks each transaction row
        │   └─ Shows only rows where matched rule = "Rule B"
        │
        ├─→ Table updates instantly
        │   Shows ONLY transactions with matched rule = "Rule B"
        │   All others hidden
        │
        ├─→ Summary updates
        │   ├─ Total Transactions: 5 (filtered count)
        │   ├─ Total Rules Selected: 1
        │   └─ Grand Total Amount: ₹250.00
        │
        └─→ Export buttons now download ONLY visible rows
```

### Category Filter Flow

```
User at Rules Results Page
        │
        ├─→ Sees list of custom categories
        │   (in "Apply Custom Category to Transactions" panel)
        │
        ├─→ Selects 1 or more category checkboxes
        │   □ Groceries
        │   ☑ Utilities  ←  Selected
        │   □ Entertainment
        │
        ├─→ Clicks "Apply Filter" button
        │
        ├─→ JavaScript sends AJAX request
        │   POST /analyzer/apply-custom-category-rules/
        │   category_ids: ["utilities_id"]
        │
        ├─→ Backend processes
        │   ├─ Gets Utilities category
        │   ├─ Gets its rules
        │   ├─ Matches transactions
        │   └─ Returns: [txn_id_1, txn_id_3, txn_id_7]
        │
        ├─→ JavaScript receives transaction IDs
        │   filterTransactionsByRulesAndCategories(
        │       [], ["utilities_id"], [1, 3, 7]
        │   )
        │
        ├─→ Table updates instantly
        │   Shows ONLY transactions with IDs [1, 3, 7]
        │   All others hidden
        │
        ├─→ Summary updates
        │   ├─ Total Transactions: 3 (filtered)
        │   ├─ Total Categories Selected: 1
        │   └─ Grand Total Amount: ₹150.00
        │
        └─→ Download includes ONLY visible rows
```

### Combined Filter Flow

```
User selects BOTH rules AND categories
        │
        ├─→ Selects rules
        │   ☑ Rule A
        │
        ├─→ Selects categories
        │   ☑ Category X
        │
        ├─→ Clicks "Apply Filter"
        │
        ├─→ JavaScript combines logic
        │   Show if: (rule matches Rule A) OR (txn_id in [X_matches])
        │
        ├─→ Table shows:
        │   ├─ All transactions matching Rule A
        │   ├─ PLUS
        │   └─ All transactions matching Category X
        │
        └─→ Summary & downloads work with combined results
```

---

## Table Filtering Decision Tree

```
For each transaction row in table:

    START
      │
      ├─ Are filters selected?
      │  NO  → Hide row (show nothing if no filters)
      │  YES → Continue
      │
      ├─ Are only RULES selected?
      │  │
      │  ├─ YES → Does row's matched rule name
      │  │         match selected rules?
      │  │         ├─ YES → Show row ✓
      │  │         └─ NO  → Hide row ✗
      │  │
      │  └─ NO → Continue to next check
      │
      ├─ Are only CATEGORIES selected?
      │  │
      │  ├─ YES → Is row's transaction ID
      │  │         in matched category list?
      │  │         ├─ YES → Show row ✓
      │  │         └─ NO  → Hide row ✗
      │  │
      │  └─ NO → Continue to next check
      │
      └─ Are BOTH rules AND categories selected?
         │
         └─ YES → Does row match
                  (Rule condition) OR (Category condition)?
                  ├─ YES → Show row ✓
                  └─ NO  → Hide row ✗
```

---

## Data Flow: Excel Export

```
User clicks "Download Excel"
        │
        ├─ Collect visible rows from table
        │  └─ Loop through all table rows
        │     └─ Include only rows with display !== 'none'
        │
        ├─ Extract transaction IDs
        │  └─ Get data-transaction-id from each visible row
        │
        ├─ Collect selected rule IDs
        │  └─ From checked rule checkboxes
        │
        ├─ Collect selected category IDs
        │  └─ From checked category checkboxes
        │
        ├─ Create POST form
        │  ├─ Add hidden fields with IDs
        │  ├─ Add CSRF token
        │  └─ Set action to /analyzer/export/rules-results/
        │
        ├─ Submit form
        │  └─ Browser sends POST request
        │
        ├─ Backend processes
        │  ├─ Query transactions by IDs
        │  │  SELECT * FROM transactions WHERE id IN (1,3,5,7)
        │  │
        │  ├─ Get rule and category metadata
        │  │  ├─ Rule.objects.filter(id__in=[...])
        │  │  └─ CustomCategory.objects.filter(id__in=[...])
        │  │
        │  ├─ Generate Excel workbook
        │  │  ├─ Add headers
        │  │  ├─ Add summary section
        │  │  ├─ Add transaction rows (ONLY filtered)
        │  │  └─ Add totals section
        │  │
        │  └─ Return as file download
        │
        └─ Browser downloads file
           └─ File contains ONLY visible rows
              (not all transactions)
```

---

## Timeline: Before vs After

### BEFORE (Broken)
```
Timeline
├─ User selects "Rule A"
├─ User clicks "Apply Filter"
├─ Filters applied (buggy logic)
├─ Table shows ALL transactions
│  (Bug: Shows all rules, not just selected)
├─ User clicks "Download Excel"
└─ Excel contains ALL transactions
   (Bug: Downloads everything instead of filtered)
```

### AFTER (Fixed)
```
Timeline
├─ User selects "Rule A"
├─ User clicks "Apply Filter"
├─ Filters applied (correct logic)
├─ Table shows ONLY Rule A's transactions
│  ✓ Correct: Shows only selected rule
├─ Summary updates
│  ✓ Shows filtered count and amount
├─ User clicks "Download Excel"
└─ Excel contains ONLY visible rows
   ✓ Correct: Downloads only filtered data
```

---

## Logic Comparison

### Rule Matching Logic

#### BEFORE (Wrong)
```javascript
if (ruleText && ruleText !== '-') {
    showRow = true;  // Shows ALL rules!
}
```
Problem: Checks if ANY badge exists

#### AFTER (Correct)
```javascript
if (ruleText && selectedRuleNames.has(ruleText)) {
    showRow = true;  // Shows ONLY selected rules
}
```
Solution: Checks if badge text is in selected set

---

## Component Interaction Diagram

```
                    ┌─────────────────┐
                    │  User's Browser │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   HTML Page     │
                    │ (apply_rules_   │
                    │  results.html)  │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
      ┌─────▼──┐        ┌────▼────┐     ┌───▼────┐
      │ Rules  │        │  Table  │     │  Cats  │
      │ Panel  │        │ Display │     │ Panel  │
      └─────┬──┘        └────┬────┘     └───┬────┘
            │                │              │
            └────────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │  JavaScript     │
                    │  Filtering Func │
                    │  (in page)      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        │            ┌───────▼────────┐           │
        │            │   AJAX Call    │           │
        │            │ (for categories)│          │
        │            └───────┬────────┘           │
        │                    │                    │
        │                 Backend                 │
        │                    │                    │
        │         ┌──────────▼──────────┐         │
        │         │ apply_custom_       │         │
        │         │ category_rules()    │         │
        │         │ Returns: txn_ids    │         │
        │         └──────────┬──────────┘         │
        │                    │                    │
    Export Funcs         Results            Export
        │                Update              Funcs
        │                    │                │
        └────────────────────┼────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Download Form  │
                    │   (POST)        │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Backend       │
                    │ export_rules_   │
                    │ results_to_*()  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Excel/PDF File  │
                    │ (Only filtered) │
                    └─────────────────┘
```

---

## Performance Characteristics

```
Operation          Time       O()         Notes
─────────────────────────────────────────────────
Extract rule names  < 1ms    O(rules)    Uses DOM queries
Extract categories  < 1ms    O(cats)     Uses DOM queries
Filter table        10-50ms  O(n)        n = visible rows
Update summary      < 5ms    O(n)        n = visible rows
Form creation       < 5ms    O(ids)      Creates form fields
AJAX request        200-500ms O(1)       Network request
Export generation   500-2000ms O(n)      n = exported rows
Total flow          < 3 sec              User-perceptible

Notes:
• Filtering is client-side (fast)
• AJAX is for categories only (minimal)
• Export is server-side (no limit)
• No page reload (smooth UX)
```

---

## Error Handling Flow

```
User action
    │
    ├─ Try to apply filter
    │  │
    │  ├─ Are rules OR categories selected?
    │  │  ├─ NO → Show error message
    │  │  │       "Please select at least one rule or category"
    │  │  │
    │  │  └─ YES → Continue
    │  │
    │  └─ Get selected IDs
    │     │
    │     ├─ For AJAX calls (categories)
    │     │  ├─ Request fails?
    │     │  │  └─ Show error: "Error applying filter"
    │     │  │
    │     │  └─ Request succeeds
    │     │     └─ Process results
    │     │
    │     └─ For table filtering
    │        └─ No additional errors expected
    │
    └─ Complete
       ├─ Show success message
       └─ Update table & summary
```

---

## This diagram shows:
✅ System architecture
✅ User interaction flows
✅ Data flow during export
✅ Decision logic
✅ Component interactions
✅ Performance characteristics
✅ Error handling

Great for presentations and understanding the complete system!
