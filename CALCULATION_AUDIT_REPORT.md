# Calculation Audit Report - BankWatch

## Executive Summary
A comprehensive audit of the BankWatch project's financial calculations has been completed. **One critical calculation error was identified and fixed**, plus enhancements made for negative savings handling.

---

## ✅ Calculations Verified as CORRECT

### 1. **Total Income Calculation**
- **Location:** Multiple views (dashboard, account_details, analysis_results)
- **Method:** `Transaction.objects.filter(transaction_type='CREDIT').aggregate(total=models.Sum('amount'))`
- **Status:** ✅ CORRECT
- **Note:** Uses Django ORM aggregation which is database-level and accurate

### 2. **Total Expenses Calculation**
- **Location:** Multiple views (dashboard, account_details, analysis_results)
- **Method:** `Transaction.objects.filter(transaction_type='DEBIT').aggregate(total=models.Sum('amount'))`
- **Status:** ✅ CORRECT
- **Note:** Uses Django ORM aggregation which is database-level and accurate

### 3. **Net Savings Calculation**
- **Formula:** `net_savings = total_income - total_expenses`
- **Status:** ✅ CORRECT
- **Note:** Mathematically correct. Can be negative if expenses exceed income.

### 4. **Category Percentage Calculation**
- **Location:** Dashboard and account_details views
- **Formula:** `(category_amount / total_expenses) * 100`
- **Status:** ✅ CORRECT
- **Note:** Correctly shows what percentage each expense category represents of total expenses

### 5. **Financial Health Score (Positive Savings)**
- **Formula:** `savings_rate = (net_savings / total_income) * 100`
- **Status:** ✅ CORRECT
- **Note:** Correctly calculates what percentage of income is saved

---

## ❌ CRITICAL ERROR FOUND AND FIXED

### **Income/Expense Percentage Calculation in `get_financial_overview_data()`**

#### **Location:**
- `analyzer/views.py` (lines 1522-1527)
- `analyzer/financial_overview_function.py` (lines 31-37)

#### **The Problem (WRONG):**
```python
# BEFORE - INCORRECT
total_all = total_income + total_expenses
income_percentage = (total_income / total_all * 100) if total_all > 0 else 0
expense_percentage = (total_expenses / total_all * 100) if total_all > 0 else 0
```

**Example of the error:**
- Income: ₹10,000
- Expenses: ₹6,000
- **Calculated as:** Income = 62.5%, Expenses = 37.5% (of combined ₹16,000)
- **This is meaningless** because it treats income and expenses as parts of a whole, when they're independent metrics

#### **The Fix (CORRECT):**
```python
# AFTER - CORRECT
# Savings rate: percentage of income that is saved
if total_income > 0:
    savings_rate = (net_savings / total_income) * 100
else:
    savings_rate = 0 if net_savings == 0 else -100

# For percentage displays: show what percentage of income was spent
expense_percentage = (total_expenses / total_income * 100) if total_income > 0 else 0
income_percentage = 100  # Income is always 100% of itself
```

**Same example with fix:**
- Income: ₹10,000 (100%)
- Expenses: ₹6,000 (60% of income)
- Savings: ₹4,000 (40% of income)
- **This is meaningful** and shows the actual spending behavior

---

## ⚠️ ENHANCEMENT: Negative Savings Handling

### **Issue Identified:**
The previous financial health scoring didn't properly handle situations where expenses exceed income (negative savings rate).

### **Before:**
Only 3 health levels:
- Excellent (≥ 20% savings)
- Good (≥ 10% savings)
- Needs Attention (< 10% savings)

❌ **Problem:** A user spending 150% of income (deficit) had the same score as a user saving 5%

### **After - Enhanced Scoring:**
```python
if total_income > 0:
    if savings_rate >= 20:
        health_status = 'Excellent'      # Savings >= 20% of income
        health_score = 85
    elif savings_rate >= 10:
        health_status = 'Good'           # Savings 10-20% of income
        health_score = 70
    elif savings_rate >= 0:
        health_status = 'Needs Attention' # Spending all income, no savings
        health_score = 50
    elif savings_rate >= -20:
        health_status = 'Poor'           # Small deficit (overspending 0-20%)
        health_score = 30
    else:
        health_status = 'Critical'       # Large deficit (overspending > 20%)
        health_score = 10
else:
    health_status = 'No Data'
    health_score = 0
```

**Example scenarios with new scoring:**
- Income ₹10,000, Expense ₹8,000 → Savings Rate 20% → **Excellent** (85)
- Income ₹10,000, Expense ₹9,000 → Savings Rate 10% → **Good** (70)
- Income ₹10,000, Expense ₹10,000 → Savings Rate 0% → **Needs Attention** (50)
- Income ₹10,000, Expense ₹12,000 → Savings Rate -20% → **Poor** (30)
- Income ₹10,000, Expense ₹15,000 → Savings Rate -50% → **Critical** (10)

---

## 📊 All Calculation Locations Reviewed

### Views.py Calculations:
1. ✅ **dashboard()** - Lines 62-121
2. ✅ **analysis_results()** - Lines 298-340
3. ✅ **view_account_details()** - Lines 1016-1074
4. ⚠️ **get_financial_overview_data()** - Lines 1513-1552 **(FIXED)**

### Financial Overview Function:
5. ⚠️ **get_financial_overview_data()** - Lines 1-80 **(FIXED)**

### File Parsers:
6. ✅ **StatementParser.parse_file()** - Uses database aggregation, no calculation logic

### Models:
7. ✅ **BankAccount.get_balance()** - Lines 18-27 (Correct calculation)
8. ✅ **AnalysisSummary** - Stores totals correctly

---

## 🔍 Testing Recommendations

### Test Cases to Verify Fix:
```
Test 1: Positive Savings
- Income: ₹50,000
- Expenses: ₹30,000
- Expected: Savings Rate 40%, Excellent status

Test 2: Small Savings
- Income: ₹50,000
- Expenses: ₹45,000
- Expected: Savings Rate 10%, Good status

Test 3: Break Even
- Income: ₹50,000
- Expenses: ₹50,000
- Expected: Savings Rate 0%, Needs Attention status

Test 4: Small Deficit
- Income: ₹50,000
- Expenses: ₹55,000
- Expected: Savings Rate -10%, Poor status

Test 5: Large Deficit
- Income: ₹50,000
- Expenses: ₹75,000
- Expected: Savings Rate -50%, Critical status

Test 6: No Income
- Income: ₹0
- Expenses: ₹10,000
- Expected: Savings Rate -100%, No Data status
```

---

## Summary of Changes

| Component | Issue | Status | Impact |
|-----------|-------|--------|--------|
| Income/Expense % | Mathematically incorrect formula | ✅ FIXED | HIGH - Affected financial overview display |
| Negative Savings Handling | No distinction for different deficit levels | ✅ ENHANCED | MEDIUM - Improved user experience |
| All Other Calculations | Verified correct | ✅ VERIFIED | - |

---

## Files Modified
1. `analyzer/views.py` (get_financial_overview_data function)
2. `analyzer/financial_overview_function.py` (get_financial_overview_data function)

## Files Reviewed (No Changes Needed)
- `analyzer/models.py`
- `analyzer/file_parsers.py`
- `templates/analyzer/dashboard.html`
- `templates/analyzer/account_details.html`
- `templates/analyzer/results.html`
- `analyzer/rules_engine.py`

---

**Audit Date:** January 16, 2026
**Status:** ✅ COMPLETE AND FIXED
