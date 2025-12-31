# Quick Start Guide: Create Your Own

## 🚀 Getting Started (60 seconds)

### Access the Page
1. Log in to BankWatch
2. Click **"Create Your Own"** in the top navigation
3. You're in! 🎉

---

## 📝 Create Your First Rule

### Step 1: Fill Basic Info
```
Rule Name: → "Amazon Shopping"
Category: → Select "Shopping"
Rule Type: → "AND" (all conditions must match)
```

### Step 2: Add Conditions
1. Click **"+ Add Condition"**
2. Choose condition type: **"Keyword in Description"**
3. Match type: **"Contains"**
4. Keyword: **"Amazon"**
5. Click **"+ Add Condition"** again
6. Choose: **"Amount"** → **"Greater Than"** → **"500"**

### Step 3: See Your Preview
```
✓ Rule Preview shows:
  "Amazon Shopping" rule will apply to category: "Shopping"
  When ALL conditions match:
  • Description contains "Amazon"
  • Amount greater than ₹500
```

### Step 4: Save & Done!
Click **"Create Rule"** → ✅ Success notification appears → Rule shows in list below

---

## 🎨 Create Your First Category

### Step 1: Switch to Create Categories Tab
Click the **"Create Categories"** tab

### Step 2: Fill Category Info
```
Category Name: → "Tech Gadgets"
Sub Category: → "Electronics" (optional)
```

### Step 3: Choose Icon
Click any emoji from the grid (✓ it will highlight)

### Step 4: See Preview
```
✓ Preview shows:
  🛒 Tech Gadgets → Electronics
```

### Step 5: Save & Done!
Click **"Create Category"** → ✅ Success notification → Category appears in grid

---

## ⚡ Quick Tips

### Keyboard Shortcuts
- `Tab` - Move to next field
- `Enter` - Submit form (when in form)

### Best Practices
- **Rule Names**: Be specific ("Uber Rides" not "Transport")
- **Conditions**: Use 2-3 conditions for best accuracy
- **Categories**: Use emoji to make them visually distinct

### Common Rules to Create

#### 🛒 Shopping Rule
```
Name: Amazon Purchases
Category: Shopping
Conditions:
  - Keyword contains: "Amazon"
  - Amount > ₹100
```

#### 🍔 Food Rule
```
Name: Restaurant Spending
Category: Food & Dining
Conditions:
  - Keyword contains: "Zomato" OR "Swiggy"
  - Amount > ₹200
```

#### ✈️ Travel Rule
```
Name: Flight Bookings
Category: Travel
Conditions:
  - Keyword contains: "Flights" OR "Booking"
  - Amount > ₹2000
```

---

## 🔧 Managing Rules & Categories

### Edit a Rule
⚠️ Coming soon - For now, delete and recreate

### Delete a Rule
1. Find rule in "Your Rules" list
2. Click trash icon (**🗑️**)
3. Confirm deletion

### Delete a Category
1. Find category in "My Categories" grid
2. Rules inside will be unaffected

---

## ❓ FAQ

**Q: Can I have multiple conditions?**  
A: Yes! Add as many as needed with "+ Add Condition"

**Q: What's the difference between AND and OR?**  
A: AND = ALL conditions must match  
   OR = ANY condition can match

**Q: Can I edit a rule after creating it?**  
A: Currently delete and recreate (edit coming soon)

**Q: Will rules automatically apply to past transactions?**  
A: No. Use "Apply Rules" from the More dropdown to manually apply

**Q: Can I share rules with other users?**  
A: Not yet - rules are private to each user

**Q: How many rules can I create?**  
A: Unlimited!

---

## 📊 Example Workflows

### Workflow 1: Shopping Rules
```
1. Create "Amazon" rule → Shopping
2. Create "Flipkart" rule → Shopping  
3. Create "Swiggy Food" rule → Food & Dining
4. Create "Premium Shopping" custom category
5. Go to "Apply Rules" to categorize transactions
```

### Workflow 2: Budget Tracking
```
1. Create "Salary" rule → Income
2. Create "Bills & EMI" rule → Bills
3. Create "Savings Transfer" rule → Other
4. Create "Entertainment" rule → Entertainment
5. View categorized transactions to track spending
```

### Workflow 3: Custom Categories
```
1. Create category "Subscriptions" with 📺 icon
2. Create category "Investments" with 💰 icon
3. Add rules to each category
4. Monitor your custom categories in dashboard
```

---

## 🎯 Performance Tips

- Keep rule names **short and specific**
- Use **2-3 conditions max** per rule
- **Delete unused rules** to keep interface clean
- Check **rule previews** before creating

---

## 🆘 Troubleshooting

### Rule doesn't appear after creating?
1. Scroll down in "Your Rules" section
2. Try refreshing the page (F5)
3. Check browser console (F12) for errors

### AJAX request failed?
1. Check internet connection
2. Verify you're still logged in
3. Check Django server is running

### Category icon not saving?
1. Make sure icon is selected (should be highlighted)
2. Verify category name is filled
3. Try again

---

## 🎓 Learning Path

**Beginner** (5 min)
- Create 1 simple rule
- Create 1 category

**Intermediate** (15 min)
- Create 3-4 rules with multiple conditions
- Create 2-3 custom categories
- Delete a rule

**Advanced** (30+ min)
- Create complex rule logic (AND/OR)
- Create specialized categories
- Combine rules with Apply functionality

---

## 📞 Need Help?

1. Read [Full Guide](CREATE_YOUR_OWN_GUIDE.md)
2. Check browser console (F12)
3. Review Django error logs

---

**Happy Rule Creating! 🚀**
