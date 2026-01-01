# Category Edit & Delete - Quick Reference

## 🎯 Quick Start

### Edit a Category
1. Go to **Create Your Own** page
2. Scroll to **My Categories** section
3. Hover over any category card
4. Click **edit icon** (pencil ✎) in top-right
5. Modal opens - modify:
   - Category name
   - Sub-category description
   - Icon (24 emoji options)
   - Color (color picker)
6. Click **Save**
7. ✅ Category updates instantly

### Delete a Category
1. Go to **Create Your Own** page
2. Scroll to **My Categories** section
3. Hover over any category card
4. Click **delete icon** (trash 🗑️) in top-right
5. Confirm deletion
6. ✅ Category removed instantly

---

## 📋 What You Can Edit

| Field | Type | Notes |
|-------|------|-------|
| Name | Text | Required, must be unique |
| Description | Text | Optional, for sub-categorization |
| Icon | Emoji | 24 options to choose from |
| Color | Color | Hex format, use color picker |

---

## ⚠️ Important Notes

- **Deletion is permanent**: Deleting a category also deletes all its rules
- **Confirmation dialog**: Prevents accidental deletion
- **No page reload**: Changes apply instantly
- **Live validation**: Name must be unique across your categories
- **Mobile friendly**: Edit modal works on all devices

---

## 🔄 Apply Custom Category Rules

**Purpose**: Apply category rules to transactions

**URL**: `/analyzer/apply-custom-category-rules/`

**How it works**:
1. User selects categories with rules
2. System scans all transactions
3. Matches transactions against rule conditions
4. Returns list of matching transaction IDs
5. Frontend can then apply categories to matched transactions

**Request**:
```
POST /analyzer/apply-custom-category-rules/
category_ids=1&category_ids=2&category_ids=3
```

**Response**:
```json
{
  "success": true,
  "message": "Applied 3 categories to 15 matching transactions",
  "matched_transaction_ids": [1, 5, 12, 23, ...],
  "category_names": ["Shopping", "Travel", "Food"],
  "category_colors": ["#5a67d8", "#38b2ac", "#ed8936"],
  "applied_count": 15
}
```

---

## 💡 Pro Tips

1. **Organize categories** by color to group similar expenses
2. **Use descriptive names** - "Online Shopping" is better than "Shop"
3. **Keep icons consistent** - Same icon for same category type
4. **Edit regularly** - Update categories as your needs change
5. **Test rules** before applying - Add conditions, then test match

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Edit modal won't open | Refresh page and try again |
| Changes not saving | Check browser console (F12) for errors |
| Duplicate name error | Choose a different name |
| Category won't delete | Confirm you have write permissions |
| Colors look wrong | Try a different hex color value |

---

## 📱 Mobile Tips

- Tap and hold category to see edit/delete icons
- Icons appear at top-right of card
- Modal adapts to screen size
- Use tap keyboard for color input
- Icon grid scrolls horizontally if needed

---

**Need help?** See `CREATE_YOUR_OWN_QUICK_GUIDE.md` for detailed user guide.
