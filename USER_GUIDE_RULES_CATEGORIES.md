# BankWatch - How to Create & Apply Rules and Categories

## Complete Guide for Users

---

## 📋 Table of Contents
1. [Creating Rules](#creating-rules)
2. [Creating Categories](#creating-categories)
3. [Applying Rules to Statements](#applying-rules)
4. [Viewing Results](#viewing-results)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 Creating Rules

### What are Rules?
Rules automatically categorize your bank transactions based on keywords, amounts, dates, or payment sources.

### How to Create a Rule

1. **Navigate to Create Your Own Page**
   - Go to: `https://bankwatch-production.up.railway.app/analyzer/create-your-own/`
   - Click on the "Create Your Own" menu option

2. **Fill in Rule Details**
   - **Rule Name**: Give your rule a descriptive name (e.g., "Amazon Purchases")
   - **Category**: Select the category to apply (Shopping, Food & Dining, Bills, etc.)
   - **Rule Logic Type**:
     - **Match ALL conditions (AND)**: Transaction must match EVERY condition
     - **Match ANY condition (OR)**: Transaction must match AT LEAST ONE condition

3. **Add Conditions**
   - Click "Add Condition" button
   - Choose condition type:
     - **Keyword**: Match text in description (Contains, Starts With, Ends With, Exact)
     - **Amount**: Match based on transaction amount (>, <, =, Between, etc.)
     - **Date**: Match transactions in a date range
     - **Source**: Match based on payment method (UPI, Debit Card, Credit Card, etc.)

4. **Create the Rule**
   - Click "Create Rule" button
   - You'll see a success message
   - The rule appears in the "Active Rules" list

### Example: Create a "Food Delivery" Rule
```
Name: Food Delivery Apps
Category: Food & Dining
Logic Type: Match ANY condition (OR)
Conditions:
  1. Keyword contains "swiggy"
  2. Keyword contains "zomato"
  3. Keyword contains "dunzo"
```
When applied, any transaction with Swiggy, Zomato, or Dunzo in its description will be categorized as "Food & Dining".

---

## 🏷️ Creating Custom Categories

### What are Custom Categories?
Custom categories let you create your own transaction categories beyond the standard options.

### How to Create a Custom Category

1. **Go to Create Your Own Page**
   - Navigate to: `https://bankwatch-production.up.railway.app/analyzer/create-your-own/`

2. **Switch to "Categories" Tab**
   - Click on the "Categories" tab at the top

3. **Fill in Category Details**
   - **Category Name**: e.g., "Subscriptions & Memberships"
   - **Description**: Optional, e.g., "Monthly subscription services"
   - **Select Icon**: Choose an emoji/icon for visual identification
   - **Select Color**: Choose a color for the category

4. **Add Conditions (Optional)**
   - Click "Add Condition" to set rules for this category
   - If no conditions added, category won't auto-apply (manual only)
   - Same condition types as rules (Keyword, Amount, Date, Source)

5. **Create the Category**
   - Click "Create Category" button
   - Category appears in "Active Categories" list

### Example: Create "Monthly Subscriptions" Category
```
Name: Monthly Subscriptions
Icon: 🎬 (Movie icon)
Color: Purple (#7c3aed)
Conditions:
  - Keyword contains "subscription"
  - Keyword contains "membership"
  - Keyword contains "premium"
```

---

## ⚡ Applying Rules to Statements

### How to Apply Your Rules

1. **Go to Apply Rules Page**
   - Option A: Click the "Apply Rules" button in the stats section on Create Your Own page
   - Option B: Navigate to: `https://bankwatch-production.up.railway.app/analyzer/rules/apply/`

2. **Select Account (Optional)**
   - Leave empty to apply rules to ALL accounts
   - Or select a specific account

3. **Click "Apply Rules" Button**
   - System will:
     - Scan all transactions
     - Match against your rules
     - Auto-categorize matching transactions

4. **Wait for Confirmation**
   - You'll see a success message showing:
     - ✓ **Matched**: Total transactions that matched your rules
     - **Newly Categorized**: Transactions that changed category
   - Automatic redirect to results page (2 seconds)

---

## 📊 Viewing Results

### Results Page: `rules/apply/results/?show_changed=1`

#### What You'll See

1. **Filter Sidebar (Left)**
   - **Rules Filter**: Select which rules to view results for
   - **Categories Filter**: Select which categories to view
   - Checkboxes to enable/disable rules and categories

2. **Main Results Table**
   - **Date**: Transaction date
   - **Description**: Bank transaction description
   - **Amount**: Transaction amount
   - **Category**: Auto-assigned category
   - **Previous Category**: What it was before (if changed)
   - **Rule Applied**: Which rule matched

3. **Analytics Chart**
   - Visual breakdown of transactions by rule/category
   - Shows number and total amount for each filter

4. **Action Buttons** (Top Right)
   - **Export PDF**: Download results as PDF
   - **Export Excel**: Download results as Excel spreadsheet

### Filtering Results

1. **Select Rules/Categories**
   - Check boxes for rules/categories you want to view
   - OR click the rule/category name directly

2. **Apply Filter**
   - Click "Filter" button to update results
   - Results update instantly (AJAX)

3. **Clear Filters**
   - Click "Clear Filters" button to see all results

---

## 🐛 Troubleshooting

### Issue: Rules Not Showing Results

**Problem**: Applied rules but no transactions appear

**Solutions**:
1. ✓ Check that rules are **ACTIVE** (green status)
2. ✓ Verify rule conditions are correct
3. ✓ Ensure transactions match the keywords (case-insensitive)
4. ✓ Check the amount range if using amount conditions
5. ✓ Navigate directly to rule and check "Total Matched"

### Issue: "No Transactions Found"

**Problem**: After applying rules, results page is empty

**Solutions**:
1. ✓ Make sure you have uploaded statements first
2. ✓ Apply rules to the correct account
3. ✓ Check if rules have no matching transactions
4. ✓ Verify rule conditions are not too restrictive

### Issue: Rule Created But Not Available

**Problem**: Rule doesn't appear in filter list

**Solutions**:
1. ✓ Rule must be **ACTIVE** (not disabled)
2. ✓ Refresh the page
3. ✓ Check spelling of rule name
4. ✓ Rules must have at least one condition

### Issue: Rules Not Applying to Transactions

**Problem**: Click "Apply Rules" but transactions not categorized

**Solutions**:
1. ✓ Check that rules are active
2. ✓ Verify rule has valid conditions
3. ✓ Ensure transactions exist in the system
4. ✓ Check that rule logic (AND vs OR) is correct
5. ✓ Look at success message - it shows how many matched

---

## 📈 Best Practices

### Creating Effective Rules

1. **Use OR Logic for Variations**
   - Example: "Amazon OR Flipkart OR Myntra" = Shopping
   - More flexible, catches more transactions

2. **Use AND Logic for Specific Cases**
   - Example: "UPI AND 100-500 amount AND contains 'bill'"
   - More restrictive, precise matching

3. **Keep Keywords Simple**
   - Use partial keywords: "amazon" (not "Amazon Purchases from...")
   - System does case-insensitive matching

4. **Test with Few Transactions First**
   - Create a rule
   - Apply it
   - Check if results look correct
   - Refine if needed

### Organizing Categories

1. **Create Categories for Personal Needs**
   - Examples: "Health & Wellness", "Learning", "Hobbies"
   - Use icons and colors for quick visual recognition

2. **Link Rules to Custom Categories**
   - Add conditions to auto-apply the category
   - Or apply manually later

3. **Use Consistent Naming**
   - "Monthly Bills" vs "Bills & Utilities" - pick one style
   - Helps with reports and analysis

---

## 💡 Tips & Tricks

### Quick Rule Creation
```
Most common rules needed:
- Online Shopping (Amazon, Flipkart, Myntra, etc.)
- Food Delivery (Swiggy, Zomato, Dunzo)
- Ride Sharing (Uber, Ola, Lyft)
- Subscriptions (Netflix, Spotify, Prime, etc.)
- Medical (Pharmacy, 1mg, Netmeds)
- Entertainment (Movie tickets, gaming)
```

### Using Multiple Conditions
- **AND Rule**: "Keyword = 'amazon' AND Amount > 1000" (expensive Amazon purchases)
- **OR Rule**: "Source = 'UPI' OR Source = 'Debit Card'" (digital payments)

### Reviewing Results
- After applying rules, check the "Previous Category" column
- This shows what was auto-categorized
- Review for accuracy before exporting reports

---

## 📞 Support

If you encounter any issues:
1. Check the Troubleshooting section above
2. Verify rule conditions and keywords
3. Ensure transactions are in the system
4. Try refreshing the page
5. Check browser console for error messages (F12)

---

**Happy organizing! 🎯**
