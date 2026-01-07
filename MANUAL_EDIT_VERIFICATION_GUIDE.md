# Manual Edit Persistence - Verification Guide

## ✅ Quick Test Checklist

Use this guide to verify that manually edited transactions are correctly persisted and displayed in rule application results.

---

## 🧪 Test Case 1: Basic Edit & Persistence

### Steps:
1. **Navigate to Account Details** (e.g., `/analyzer/accounts/2/view/`)
2. **Find a transaction** with description like "STARBUCKS COFFEE"
3. **Click the Category badge** to open the edit modal
4. **Change category** to "FOOD"
5. **Set label** (optional) to "Coffee"
6. **Click "Save Changes"**

### Expected Results:
- ✅ Modal closes without page refresh
- ✅ Category badge updates to "FOOD"
- ✅ Edit icon (✏️) appears next to the category
- ✅ Refresh the page → Changes persist
- ✅ Label displays in the transaction row if set

### Database Check:
```sql
SELECT id, description, category, user_label, is_manually_edited, last_edited_at 
FROM analyzer_transaction 
WHERE id = <transaction_id>;
```

Expected output:
- `is_manually_edited = True`
- `category = "FOOD"`
- `user_label = "Coffee"` (or NULL if not set)
- `last_edited_at` = recent timestamp

---

## 🧪 Test Case 2: Manually Edited + Apply Rules

### Steps:
1. **Complete Test Case 1** (manually edit a transaction)
2. **Navigate to Rules page** (`/analyzer/rules/apply/`)
3. **Select an account** with the edited transaction
4. **Click "Apply Rules"**
5. **Wait for success message**
6. **Click "View Results"** (or navigate to results page)

### Expected Results:
- ✅ Manually edited transaction appears in results table
- ✅ Edit icon (✏️) visible in the new column
- ✅ User label shown alongside edit icon
- ✅ Transaction NOT overridden by rules
- ✅ Original manual category ("FOOD") preserved

### What Should NOT Happen:
- ❌ Transaction should NOT be skipped/hidden
- ❌ Category should NOT change to rule-matched value
- ❌ Edit icon should NOT disappear

---

## 🧪 Test Case 3: Manual Edits + Category Filtering

### Steps:
1. **Complete Test Case 1** (edit a transaction to "FOOD")
2. **Go to Custom Categories page** (create if needed)
3. **Apply Custom Categories** from rules/category page
4. **Go to Results page** with URL like: `/analyzer/rules/apply/results/?category_ids=X`
5. **Select a category filter** (e.g., "DINING")

### Expected Results:
- ✅ Manually edited transactions appear even if they don't match filter
- ✅ Edit icon (✏️) visible in results
- ✅ Original manual category displayed ("FOOD")
- ✅ "DINING" rule might be shown as "Matched Category" but manual stays
- ✅ Can still see both manual category and matched category

---

## 🧪 Test Case 4: Multiple Edited Transactions

### Steps:
1. **Edit 3-5 transactions** with different categories and labels
2. **Apply Rules** from the Rules page
3. **Go to Results** page
4. **Use "show_changed=1" filter** in URL

### Expected Results:
- ✅ All manually edited transactions appear in results
- ✅ Edit icons visible for all edited transactions
- ✅ User labels display correctly
- ✅ No data loss across pages
- ✅ Table shows all edited + newly matched transactions

---

## 🧪 Test Case 5: Visual Indicator Verification

### Steps:
1. **Open a Results page** with some transactions
2. **Look for the ✏️ column** (rightmost column before "Previous Category")
3. **Hover over edit icons** to see tooltips
4. **Check labels** displayed next to edit icons

### Expected Results:
- ✅ Edit icon (✏️) appears in its own column
- ✅ Icon color is orange (#ff9800)
- ✅ Tooltip shows: "Manually edited transaction - Category/Label set by user"
- ✅ User labels visible below or next to icon
- ✅ Non-edited transactions show "-" in that column

---

## 🧪 Test Case 6: Data Consistency Across Pages

### Steps:
1. **Edit a transaction** on Account Details page
2. **Navigate to Results page**
3. **Go back to Account Details**
4. **Check the transaction** again

### Expected Results:
- ✅ Edit persists across all pages
- ✅ Category matches between pages
- ✅ Label matches between pages
- ✅ Edit icon appears consistently
- ✅ No "double editing" needed

---

## 🧪 Test Case 7: Priority Order Verification

### Steps:
1. **Edit transaction 1** to category "FOOD"
2. **Create a rule** that matches transaction 1 to "DINING"
3. **Apply the rule**
4. **View results**

### Expected Results:
- ✅ Transaction shows category "FOOD" (manual edit wins)
- ✅ "Matched Rule" column shows rule matched it to "DINING"
- ✅ But actual category stays "FOOD" (priority correct)
- ✅ Edit icon visible (shows priority order)

---

## 🔍 Browser Console Checks

### Check 1: Category Click Event
1. Open Browser DevTools (F12)
2. Go to Account Details page
3. Click on a Category badge
4. Check Console for: `Category clicked for ID: [number]`

### Check 2: AJAX Success
1. Edit a transaction (modal should appear)
2. Change category and click "Save"
3. Watch Console for JSON response
4. Should see: `{success: true, transaction: {...}}`

### Check 3: Results Page Load
1. Navigate to Results page
2. Check Console for any errors
3. Verify transactions load without issues
4. Check that manually edited transactions are included

---

## 📊 Network Request Verification

### Check 1: Update Category Request
- **URL**: `/analyzer/api/transactions/update-category/`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "transaction_id": 123,
    "category": "FOOD",
    "user_label": "Coffee"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "transaction": {
      "id": 123,
      "category": "FOOD",
      "category_display": "Food",
      "user_label": "Coffee",
      "is_manually_edited": true
    }
  }
  ```

### Check 2: Results Page Request
- **URL**: `/analyzer/rules/apply/results/?show_changed=1`
- **Response includes**: Manually edited transactions with `is_manually_edited: true`

---

## ⚠️ Troubleshooting

### Issue: Edit icon doesn't appear
- **Check**: Is `is_manually_edited = True` in database?
- **Solution**: Verify edit was saved (check update-category response)

### Issue: Category reverts after applying rules
- **Check**: Verify transaction has `is_manually_edited = True`
- **Solution**: Re-edit transaction, ensure modal shows "Save Changes"

### Issue: Transaction missing from results
- **Check**: Filter URL (check if filters are too restrictive)
- **Solution**: Try without filters or add rule_ids/category_ids that match

### Issue: Label doesn't display in results
- **Check**: Is `user_label` field populated in database?
- **Solution**: Edit transaction again and set label explicitly

---

## 📝 Test Data Setup

### Create Test Scenario:
```sql
-- Find a transaction
SELECT id, description, category FROM analyzer_transaction 
WHERE statement__account_id = 2 
LIMIT 1;

-- Manually edit it via UI to category "FOOD"
-- Update should happen automatically

-- Verify in database
SELECT id, category, user_label, is_manually_edited FROM analyzer_transaction 
WHERE id = <id>;
```

---

## ✅ Sign-Off Checklist

Mark each test case as complete:

- [ ] Test Case 1: Basic Edit & Persistence ✅
- [ ] Test Case 2: Manually Edited + Apply Rules ✅
- [ ] Test Case 3: Manual Edits + Category Filtering ✅
- [ ] Test Case 4: Multiple Edited Transactions ✅
- [ ] Test Case 5: Visual Indicator Verification ✅
- [ ] Test Case 6: Data Consistency Across Pages ✅
- [ ] Test Case 7: Priority Order Verification ✅
- [ ] Browser Console Checks ✅
- [ ] Network Request Verification ✅
- [ ] Troubleshooting Scenarios (if any) ✅

---

## 📞 Support

If any test case fails:
1. Check the browser console (F12) for errors
2. Verify database fields are populated
3. Check network requests in DevTools
4. Review [MANUAL_EDIT_PERSISTENCE_FIX.md](MANUAL_EDIT_PERSISTENCE_FIX.md) for detailed info

---

**Last Updated**: January 7, 2026  
**Status**: Ready for Testing  
**Version**: 1.0
