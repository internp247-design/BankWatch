# FIX PLAN - Rules, Categories, and UI Issues

## Issue 1: Rules & Categories Not Working Properly on Transactions

### Root Causes:
1. Many rules are INACTIVE (is_active = False)
2. Rules are not being applied when transactions are imported
3. Custom categories are not being applied

### Solution:
1. Ensure rules are ACTIVE by default when created
2. Add automatic rule application to transaction import logic
3. Add button to manually apply rules to all transactions
4. Fix matching logic if needed

### Files to Modify:
- analyzer/views.py (add auto-apply logic in upload handler)
- analyzer/views.py (ensure apply_rules sets is_active=True)
- templates/analyzer/create_your_own.html (add manual apply button)

---

## Issue 2: Edit Form UI - Conditions Should Be Inside Form

### Current Problem:
- Edit Rule form opens
- "Add Condition" button shows condition builder as SEPARATE MODAL
- Conditions appear outside/below the edit form
- This is confusing UX

### Desired Solution:
- Edit form should have Add Condition INSIDE the form
- Condition builder should be INLINE (not a modal)
- Existing conditions should show in form
- Add/Edit/Delete actions all happen within the form

### Solution Approach:
1. Move condition builder HTML from modal to inline inside edit form
2. Show/hide condition builder inline when "Add Condition" clicked
3. Render existing conditions inside form with edit/delete options
4. Same for category edit form

### Files to Modify:
- templates/analyzer/create_your_own.html (restructure modals and forms)
- JavaScript functions (openConditionBuilder, closeConditionBuilder, etc)

---

## Issue 3: Pie Chart Must Use Rule/Category Colors

### Current Problem:
- Pie chart uses hardcoded default colors
- Rule/category custom colors are ignored
- Color in settings != Color in chart

### Solution:
1. Pass rule/category colors from backend to frontend
2. Update pie chart color generation to use custom colors
3. Map colors based on rule/category name

### Files to Modify:
- analyzer/views.py (pass colors in template context)
- templates/analyzer/apply_rules_results.html (update color generation)

---

## Implementation Order:
1. Fix Edit Form UI (most visible issue)
2. Pass colors to template
3. Update pie chart colors
4. Fix rule activation and application
5. Test all changes
