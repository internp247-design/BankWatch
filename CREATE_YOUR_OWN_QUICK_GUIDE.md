# Create Your Own - Quick Reference Guide

## 🚀 Quick Start

### Access the Unified Page:
```
URL: http://localhost:8000/analyzer/create-your-own/
Navigation: Click "Create Your Own" in the navbar
```

---

## 📋 Create Rules (Tab 1)

### Step-by-Step:
1. **Rule Name**: Enter a unique rule name (e.g., "Amazon Purchases")
2. **Category**: Select target category from dropdown
3. **Logic Type**: Choose:
   - **AND**: All conditions must match
   - **OR**: Any condition matches
4. **Add Conditions**:
   - Click "+ Add Condition" button
   - Select condition type:
     - **Keyword**: Search in description
     - **Amount**: Transaction amount filters
     - **Date**: Date range filters
     - **Source**: Payment channel filters
   - Fill in condition details
   - Click "Add" to confirm
5. **View Preview**: See formatted rule description
6. **Create Rule**: Click "Create Rule" button
7. ✅ **Result**: Rule appears in the "Active Rules" list below

### Condition Types Details:

#### Keyword Conditions:
- Match Type: Contains | Starts With | Ends With | Exact Match
- Example: Contains "Amazon"

#### Amount Conditions:
- Operators: Greater Than | Less Than | Equals | Between
- Between allows two amounts (From - To)
- Example: Between 500 and 5000

#### Date Conditions:
- Start Date and End Date pickers
- Example: From 01/01/2024 to 31/12/2024

#### Source Conditions:
- Options: UPI | Card | Bank | Cheque | Cash | etc.
- Example: Source = UPI

---

## 🗂️ Create Categories (Tab 2)

### Step-by-Step:
1. **Category Name**: Enter name (e.g., "Online Shopping")
2. **Sub-Category** (Optional): Add description/subcategory
3. **Select Icon**: Click on emoji icon from grid
4. **Choose Color**: Use color picker (optional)
5. **View Preview**: See how category looks
6. **Create Category**: Click button
7. ✅ **Result**: Category appears in "My Categories" grid below

### Icon Selection:
- 24 emoji icons available in visual grid
- Click to select (shows checkmark)
- Updates preview in real-time

### Color Options:
- Default: #5a67d8 (blue)
- Click color picker to customize
- Hex color format

---

## ✏️ Managing Items

### Delete a Rule:
1. Find rule in "Active Rules" list
2. Click trash icon <i class="fas fa-trash"></i>
3. Confirm deletion
4. ✅ Rule removed instantly (no page reload)

### Delete a Category:
1. Find category in "My Categories" grid
2. Click trash icon in category card
3. Confirm deletion
4. ✅ Category removed instantly

### View Rules in Category:
- Rules appear nested under each category
- Each rule shows its conditions
- Use edit/delete icons on rules

---

## 🎯 Common Use Cases

### Use Case 1: Automate Amazon Purchases
```
Name: Amazon Shopping
Category: Shopping
Logic: AND
Conditions:
  1. Keyword contains "Amazon"
  2. Amount > ₹500
Result: Auto-tags all Amazon purchases over ₹500
```

### Use Case 2: Track Travel Expenses
```
Name: Uber Rides
Category: Travel
Logic: OR
Conditions:
  1. Keyword contains "Uber"
  2. Keyword contains "Ola"
  3. Source = UPI
Result: Auto-tags all Uber/Ola payments
```

### Use Case 3: Custom Category
```
Name: Gym Membership
Icon: 💪 (fitness)
Color: #27ae60 (green)
Result: Track fitness expenses with custom category
```

---

## ⚙️ Logic Types Explained

### AND Logic:
- **Meaning**: ALL conditions must match
- **Use**: When you want specific matching
- **Example**: 
  - Keyword = "Amazon" AND Amount > 500
  - Matches: Amazon purchase over ₹500
  - Doesn't match: Amazon purchase for ₹100 OR any amount without "Amazon"

### OR Logic:
- **Meaning**: ANY condition matches
- **Use**: When any condition should trigger
- **Example**:
  - Keyword = "Uber" OR Keyword = "Ola"
  - Matches: Any "Uber" transaction OR any "Ola" transaction
  - Doesn't match: Neither Uber nor Ola

---

## 🔍 Error Messages & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Rule name is required" | Empty rule name field | Enter a rule name |
| "Category is required" | No category selected | Choose a category from dropdown |
| "At least one condition required" | No conditions added | Click "+ Add Condition" button |
| "Please select a condition type" | Condition type not chosen | Select type from dropdown in modal |
| "Please enter a keyword" | Keyword field is empty | Type the keyword to search |
| "Please enter a valid amount" | Invalid number in amount | Enter a number (e.g., 500) |
| "Please enter both dates" | Date fields incomplete | Select both from and to dates |
| "Category with this name already exists" | Duplicate category name | Use a different category name |

---

## 💡 Tips & Tricks

1. **Preview is Your Friend**
   - Always check the preview before creating
   - Shows exactly how the rule will work

2. **Use Specific Keywords**
   - "Amazon" is more specific than "Amaz"
   - Reduces false matches

3. **Test Logic Types**
   - AND: Use for precise matching
   - OR: Use for grouping similar transactions

4. **Icon Meanings**
   - 🛒 Shopping
   - 🚕 Travel
   - 🍔 Food
   - 💡 Utilities
   - 🎬 Entertainment

5. **Color Coding**
   - Use colors to visually group categories
   - Red (#f56565) for expenses
   - Green (#48bb78) for income/savings

---

## 📱 Mobile Usage

On mobile devices:
- Tap "Create Your Own" in menu
- Form stacks vertically
- Buttons full width
- Icon grid responsive (4 columns on mobile)
- Condition modal optimized for touch

---

## 🎨 UI Elements

### Buttons:
- **Blue Gradient**: Primary action buttons (create, add, submit)
- **White Border**: Secondary actions (cancel, clear)
- **Red**: Dangerous actions (delete) - requires confirmation

### Status Indicators:
- **Header Stats**: Live counts of rules and categories
- **Badges**: Counts next to section titles
- **Empty States**: Helpful messages when no items exist

### Notifications:
- **Green**: Success messages (appears top-right, auto-closes)
- **Red**: Error messages
- **Yellow**: Warning messages
- **Blue**: Info messages

---

## 🔐 Security Notes

- ✅ Your rules are personal - only you see them
- ✅ CSRF token protects all operations
- ✅ Must be logged in to create rules
- ✅ Data encrypted in transit
- ✅ Server validates all inputs

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Tab | Move to next field |
| Enter | Submit form (when focused) |
| Esc | Close condition modal |

---

## 🐛 Troubleshooting

### Rule not appearing after creation?
- Check if page needs refresh (shouldn't be needed)
- Verify category was selected
- Check browser console for errors (F12)

### Conditions not showing?
- Click "+ Add Condition" again
- Verify condition type is selected
- Check if modal is displaying

### Rules not applying to transactions?
- This is a separate feature - use "Apply Rules" in menu
- Rules created here need to be applied to transactions

### Category color not changing?
- Ensure valid hex color (#RRGGBB format)
- Try default color, then customize

---

## 📞 Getting Help

If you encounter issues:

1. **Check the Implementation Guide**
   - File: `CREATE_YOUR_OWN_IMPLEMENTATION.md`
   - Contains technical details and architecture

2. **Verify Browser Compatibility**
   - Works in Chrome, Firefox, Safari, Edge
   - Requires JavaScript enabled

3. **Check Network Tab**
   - Press F12 to open developer tools
   - Click Network tab
   - Reload page and check for 404 or 500 errors

4. **Review Server Logs**
   - Check Django console for error messages
   - Look for validation errors

---

## 🎓 Advanced Tips

### Pattern Matching:
- **Keyword**: Can use partial words
- **Amount**: Supports decimal values
- **Date**: Use standard date format

### Multiple Conditions Strategy:
- Start with 1-2 conditions per rule
- Add more if needed for precision
- Too many conditions = no matches

### Category Organization:
- Create parent categories for broad types
- Create sub-categories for specific types
- Use consistent naming (e.g., "Online Shopping" vs "Shopping Online")

---

## 📊 Best Practices

1. **Rule Naming**: Use clear, descriptive names
   - ✅ "Amazon Online Shopping"
   - ❌ "Rule 1"

2. **Condition Accuracy**: Be specific
   - ✅ "Contains 'amazon.com'" (more specific)
   - ❌ "Contains 'a'" (too broad)

3. **Category Creation**: Think long-term
   - Create categories you'll use repeatedly
   - Don't create one-off categories

4. **Testing**: Test rules before applying
   - Create rule first
   - Apply to a small set of transactions
   - Verify matches are correct

---

**Version**: 1.0
**Last Updated**: January 1, 2026
**Status**: Ready to Use ✅
