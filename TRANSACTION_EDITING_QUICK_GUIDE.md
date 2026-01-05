# Quick Reference: Transaction Editing Feature

## 🎯 User Guide - How to Use

### Step 1: View All Transactions
1. Go to Dashboard
2. Click on an account in "Your Accounts" section
3. Scroll to "Transaction History" table
4. **You will see ALL transactions** (50 per page)

### Step 2: Filter by Time Period
1. Above the Transaction History table, find the **time filter dropdown**
2. Select one of:
   - All Time (default)
   - Last 5 Days
   - Last 1 Week
   - Last 15 Days
   - Last 30 Days
   - Last 90 Days
3. Table updates automatically with filtered transactions

### Step 3: Edit Transaction Category & Label
1. Find the transaction you want to edit
2. **Click on the Category badge** (e.g., "Shopping", "Food & Dining")
3. A modal dialog appears with:
   - Transaction details (date, description, amount)
   - Category dropdown selector
   - Label/subcategory text field
4. Make your changes:
   - Select a different category if needed
   - Add a custom label (e.g., "Books", "Groceries", "Gym subscription")
5. Click **"Save Changes"** button
6. ✅ Changes save instantly without page refresh

### Step 4: Verify Your Changes
- The transaction row updates immediately
- Category badge shows new category
- Label column displays your custom label
- A small **edit icon** (✏️) appears on edited transactions

### Step 5: Apply Rules (Respects Your Edits!)
1. Go to **Rules** page
2. Click **"Apply Rules"**
3. Rules are applied to transactions you HAVEN'T edited manually
4. Your manually edited categories are preserved!
5. See final results on the Results page

---

## 📊 Table Columns Explained

| Column | Description |
|--------|-------------|
| **Date** | Transaction date |
| **Description** | Bank statement description |
| **Category** | Transaction category (clickable!) |
| **Label** | Your custom label/subcategory |
| **Type** | Credit (incoming) or Debit (outgoing) |
| **Amount** | Transaction amount in rupees |

---

## 🎨 Visual Indicators

| Indicator | Meaning |
|-----------|---------|
| **Clickable category badge** | Click to edit |
| **✏️ Edit icon** | Transaction was manually edited |
| **"—" in label** | No custom label assigned |

---

## ⏱️ Available Time Periods

| Period | Shows |
|--------|-------|
| All Time | All transactions (no limit) |
| Last 5 Days | Transactions from last 5 days |
| Last 1 Week | Transactions from last 7 days |
| Last 15 Days | Transactions from last 15 days |
| Last 30 Days | Transactions from last 30 days |
| Last 90 Days | Transactions from last 90 days |

---

## 🏷️ Category Options

- **Income** - Money coming in
- **Food & Dining** - Restaurant, groceries, cafe
- **Shopping** - Retail, clothing, electronics
- **Bills & Utilities** - Electricity, water, internet
- **Transportation** - Fuel, auto, taxi, public transport
- **Entertainment** - Movies, games, subscriptions
- **Healthcare** - Medical, pharmacy, doctor
- **Loan & EMI** - Loan payments, credit card payments
- **Travel** - Flights, hotels, vacation
- **Other** - Anything not in above categories

---

## 🔍 Example Scenarios

### Scenario 1: Organizing Groceries
```
Transaction: HDFC Bank - Grocery Mart - ₹3,500
Current Category: Shopping
Problem: It's actually groceries, not general shopping

Solution:
1. Click "Shopping" badge
2. Change category to "Food & Dining"
3. Add label: "Groceries"
4. Click "Save Changes"

Result: Now appears as "Food & Dining" with "Groceries" label
```

### Scenario 2: Finding Last Week's Coffee Spending
```
Want to see: All coffee purchases from last week

Solution:
1. Filter by "Last 1 Week"
2. Manually edit coffee-related transactions
3. Add label "Coffee" to each
4. Can easily identify spending pattern

Result: See all coffee expenses with custom label
```

### Scenario 3: Keeping Manual Edits When Applying Rules
```
Situation: You manually edited 5 transactions, then want to apply rules

What happens:
1. You apply rules
2. Rules engine automatically skips your 5 edited transactions
3. Only non-edited transactions get categorized by rules
4. Your manual edits are preserved!

Result: Your preferences win over automatic rules
```

---

## ⚠️ Important Notes

- ✅ All changes are **saved instantly** (no manual save needed)
- ✅ Changes are **persistent** (they won't disappear)
- ✅ **No page refresh needed** (smooth user experience)
- ✅ **Edits override rules** (your manual categorization takes precedence)
- ✅ **Each edit is tracked** (system knows who edited what and when)

---

## 🐛 Troubleshooting

### Issue: Modal won't open when clicking category
**Solution**: Make sure you're clicking directly on the category badge text, not elsewhere in the cell.

### Issue: Changes aren't saving
**Solution**: 
- Check internet connection
- Try clearing browser cache
- Refresh page and try again

### Issue: Time filter shows wrong data
**Solution**: 
- The filter is based on transaction date
- Older statements may not have all transactions
- Try "All Time" to see everything

### Issue: Edit icon doesn't appear
**Solution**: 
- Refresh the page
- The icon should appear after successful save
- Check browser console for errors (F12)

---

## 📱 Mobile Usage

This feature works on mobile devices! 
- Tap category badge instead of click
- Modal appears full-screen on mobile
- All functions work the same way

---

## 🔐 Privacy & Security

- Only you can see and edit your transactions
- No one else can see your account or edits
- All data stored securely in database
- Every edit is logged with user ID and timestamp

---

## 💡 Tips & Tricks

1. **Create consistent labels**: Use same labels for similar transactions (e.g., always "Coffee" for cafe purchases)
2. **Use clear descriptions**: Labels like "Gym" or "Netflix" are clearer than "Monthly payment"
3. **Filter before bulk editing**: Use time filters to focus on specific periods
4. **Check final results**: After applying rules, view the Results page to see all categorizations

---

## 📞 Need Help?

- Check the main [TRANSACTION_EDITING_FEATURE.md](TRANSACTION_EDITING_FEATURE.md) for technical details
- Review API documentation for developers
- Contact support if issues persist

---

**Feature Status**: ✅ Production Ready
**Last Updated**: January 5, 2026
**Version**: 1.0
