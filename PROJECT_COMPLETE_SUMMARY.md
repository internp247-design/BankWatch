# 🏦 BankWatch - Complete Project Summary

**Last Updated**: December 13, 2025  
**Project Status**: ✅ Complete & Production-Ready

---

## 📌 Table of Contents

1. [Project Overview](#project-overview)
2. [Core System Architecture](#core-system-architecture)
3. [Features & Capabilities](#features--capabilities)
4. [Database Schema](#database-schema)
5. [Key Modules & Components](#key-modules--components)
6. [API Endpoints](#api-endpoints)
7. [User Workflows](#user-workflows)
8. [Global Rules System](#global-rules-system)
9. [Custom Categories System](#custom-categories-system)
10. [OCR & Statement Processing](#ocr--statement-processing)
11. [Testing & Quality Assurance](#testing--quality-assurance)
12. [Version History](#version-history)

---

## Project Overview

### What is BankWatch?

BankWatch is a comprehensive **bank statement analysis and transaction categorization system** built with Django. It processes PDF bank statements, extracts transactions using OCR technology, and provides intelligent financial analysis with customizable categorization rules.

### Key Capabilities

- **Multi-Format PDF Processing**: Handles table-based and unstructured statement layouts
- **Advanced OCR Integration**: Tesseract OCR for scanned PDFs + pdfplumber for text extraction
- **UPI Metadata Extraction**: Extracts detailed information from UPI transaction descriptions
- **Intelligent Categorization**: 19 global rules + unlimited custom category rules
- **Financial Analytics**: Per-account financial overview with charts and insights
- **Account Management**: Create, manage, and delete bank accounts
- **User-Centric Design**: Account isolation, custom rules, financial health scoring

---

## Core System Architecture

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | Django (Python) |
| **Database** | SQLite3 |
| **Frontend** | HTML5, CSS3, JavaScript (vanilla + Chart.js) |
| **OCR Engine** | Tesseract (via PyMuPDF) |
| **PDF Processing** | pdfplumber, PyMuPDF |
| **Authentication** | Django Auth System |
| **Charts** | Chart.js |
| **Icons** | FontAwesome |

### Project Structure

```
BankWatch/
├── BankWatch/                      # Django Project Settings
│   ├── settings.py                 # Configuration
│   ├── urls.py                     # URL routing
│   ├── wsgi.py                     # WSGI config
│   └── asgi.py                     # ASGI config
│
├── analyzer/                       # Main Application
│   ├── models.py                   # Database models
│   ├── views.py                    # View logic (25+ views)
│   ├── urls.py                     # URL patterns
│   ├── forms.py                    # Form classes
│   ├── rules_forms.py              # Custom rule forms
│   ├── admin.py                    # Django admin
│   │
│   ├── pdf_parser.py               # Core OCR system
│   ├── file_parsers.py             # Multi-format parsing
│   ├── upi_parser.py               # UPI metadata extraction
│   ├── rules_engine.py             # Categorization engine
│   ├── financial_overview_function.py  # Analytics
│   │
│   ├── templates/analyzer/         # HTML templates (20+ files)
│   │   ├── base.html               # Base template
│   │   ├── dashboard.html          # Account dashboard
│   │   ├── upload.html             # Statement upload
│   │   ├── results.html            # Analysis results
│   │   ├── account_details.html    # Account overview
│   │   ├── delete_account.html     # Delete confirmation
│   │   ├── create_custom_category.html
│   │   └── ...more templates
│   │
│   └── migrations/                 # Database migrations
│
├── users/                          # User Management App
│   ├── models.py                   # User profile models
│   ├── views.py                    # Auth views
│   ├── urls.py                     # Auth URLs
│   └── templates/users/            # Auth templates
│
├── static/                         # Static files (CSS, JS)
├── media/statements/               # Uploaded statements
├── templates/                      # Shared templates
│
├── manage.py                       # Django management
├── db.sqlite3                      # SQLite database
└── requirements.txt                # Python dependencies
```

---

## Features & Capabilities

### ✨ Version 2.2 Features

#### 1️⃣ Delete Account Functionality
- **Purpose**: Allow users to remove bank accounts they no longer need
- **Location**: Dashboard → Account card → Delete icon (🗑️)
- **Features**:
  - Hover-activated delete button
  - Confirmation page with account details
  - Warning about data loss
  - CSRF-protected deletion
  - Success notification
  - Automatic redirect to dashboard

**File Changes**:
- `analyzer/views.py` - `delete_account()` view
- `analyzer/urls.py` - Delete route
- `templates/analyzer/dashboard.html` - Delete button
- `templates/analyzer/delete_account.html` - Confirmation page (NEW)

---

#### 2️⃣ Account-Specific Financial Overview
- **Purpose**: View detailed financial metrics for individual accounts
- **Location**: Dashboard → Click account card
- **Features**:
  - Account information display
  - Income, Expenses, Savings totals
  - Financial Health Score (0-100)
  - Income vs Expenses chart
  - Spending by category pie chart
  - Complete transaction history
  - Responsive mobile design
  - Chart.js visualizations

**Key Metrics**:
- **Financial Health Score**: Calculated based on savings ratio and transaction diversity
- **Net Savings**: Income minus Expenses
- **Spending Analysis**: Breakdown by category

**File Changes**:
- `analyzer/views.py` - `view_account_details()` view
- `analyzer/urls.py` - Account details route
- `templates/analyzer/account_details.html` - Details page (NEW)

---

#### 3️⃣ Navigation Controls
- **Purpose**: Clear navigation between dashboard and account views
- **Features**:
  - Back to Dashboard button on account details
  - Cancel button on delete confirmation
  - Breadcrumb navigation
  - Consistent styling

---

#### 4️⃣ Change Rule Status on Results Page
- **Purpose**: Toggle rules active/inactive without leaving results page
- **Location**: Results page → Active Rules section
- **Features**:
  - AJAX-based toggle switches
  - Real-time status updates (no page reload)
  - Visual feedback (green = active, red = inactive)
  - Success/error notifications
  - Rule category tags
  - Condition count display
  - CSRF-protected endpoints

---

### 📊 Statement Processing Features

#### OCR & Parsing
- **Formats Supported**: PDF (scanned), PDF (text), Images
- **Layout Detection**: Automatic table vs. freeform detection
- **Multi-Line Processing**: Reconstructs fragmented transaction descriptions
- **Amount Parsing**: Intelligent OCR noise handling, Indian number format support
- **Bank Support**: Generic parser + Canara Bank optimizer

#### UPI Metadata Extraction
Extracts from UPI transaction descriptions:
- Sender/Receiver names
- UPI IDs
- Merchant information
- RRN (Reconciliation Reference Number)
- Transaction IDs
- Bank trace IDs

---

## Database Schema

### Core Models

#### 1. User (Django Built-in)
```python
# Fields: username, email, password, first_name, last_name, etc.
```

#### 2. BankAccount
```python
Fields:
  - user (FK to User)
  - bank_name (CharField)
  - account_number (CharField)
  - account_type (CharField - Savings/Current/Credit)
  - currency (CharField - default "INR")
  - is_active (BooleanField)
  - created_at (DateTimeField)
  - updated_at (DateTimeField)
```

#### 3. BankStatement
```python
Fields:
  - account (FK to BankAccount)
  - file_name (CharField)
  - uploaded_at (DateTimeField)
  - processing_status (CharField)
  - transaction_count (IntegerField)
```

#### 4. Transaction
```python
Fields:
  - account (FK to BankAccount)
  - date (DateField)
  - description (TextField)
  - debit_amount (DecimalField)
  - credit_amount (DecimalField)
  - balance (DecimalField)
  - category (CharField - default)
  - custom_category (FK to CustomCategory - nullable)
  - transaction_type (CharField - UPI/CARD/CHECK/TRANSFER)
  - upi_sender (CharField - nullable)
  - upi_receiver (CharField - nullable)
  - merchant_name (CharField - nullable)
  - rrn (CharField - nullable)
  - rules_applied (ManyToMany to Rule)
```

#### 5. Rule (Global Rules)
```python
Fields:
  - name (CharField)
  - category (CharField)
  - description (TextField)
  - is_active (BooleanField)
  - rule_type (CharField - "AND"/"OR")
  - created_at (DateTimeField)
```

#### 6. RuleCondition
```python
Fields:
  - rule (FK to Rule)
  - keyword (CharField)
  - match_type (CharField - CONTAINS/EXACT/STARTS_WITH/ENDS_WITH)
```

#### 7. CustomCategory
```python
Fields:
  - user (FK to User)
  - name (CharField)
  - description (TextField)
  - color (CharField)
  - icon (CharField)
  - is_active (BooleanField)
  - created_at (DateTimeField)
```

#### 8. CustomCategoryRule
```python
Fields:
  - custom_category (FK to CustomCategory)
  - user (FK to User)
  - name (CharField)
  - rule_type (CharField - "AND"/"OR")
  - is_active (BooleanField)
```

#### 9. CustomCategoryRuleCondition
```python
Fields:
  - rule (FK to CustomCategoryRule)
  - condition_type (CharField - KEYWORD/AMOUNT/DATE)
  - keyword (CharField - nullable)
  - keyword_match_type (CharField)
  - amount_operator (CharField - nullable)
  - amount_value (DecimalField - nullable)
  - date_start (DateField - nullable)
  - date_end (DateField - nullable)
```

---

## Key Modules & Components

### 1. PDF Parser (`analyzer/pdf_parser.py`)

**Core Functions**:
- `extract_text_from_pdf()` - OCR text extraction via Tesseract
- `extract_table_pdfplumber()` - Text extraction for native PDFs
- `is_table_like()` - Layout detection heuristic
- `parse_transactions_from_text()` - Multi-line block merging
- `parse_table_lines()` - Structured table parsing
- `parse_amounts()` - Intelligent OCR noise handling

**Key Features**:
- DPI-configurable rendering (default 200)
- Multi-page support
- Table vs. freeform detection
- Indian number format handling (1,55,248.00)
- Multi-line description reconstruction

---

### 2. File Parsers (`analyzer/file_parsers.py`)

**Parsers Available**:
- `CanaraBankParser` - Optimized for Canara Bank layouts
- `GenericBankStatementParser` - Universal parser
- `auto_detect_parser()` - Automatic format detection

---

### 3. UPI Parser (`analyzer/upi_parser.py`)

**Extraction Capabilities**:
- UPI transaction identification
- Sender name extraction (from "UPI/DR" pattern)
- Receiver name extraction
- UPI ID parsing
- Merchant name detection
- RRN, TID, bank trace ID extraction
- Timestamp parsing

**Example Input**:
```
UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VALUATION//...
```

**Extracted Output**:
```
{
  'upi_sender': 'RADHAKRIS',
  'upi_receiver': 'OKSBI',
  'rrn': '570467584215',
  'merchant_name': 'SBIN'
}
```

---

### 4. Rules Engine (`analyzer/rules_engine.py`)

#### GlobalRulesEngine
```python
apply_rules_to_transaction(transaction, statement)
  ├─ Matches transaction against all active rules
  ├─ Returns matched rule + category
  └─ Uses OR logic (any condition matches = match)

_matches_rule(transaction, rule)
  ├─ Checks all conditions for rule
  └─ Returns boolean
```

#### CustomCategoryRulesEngine
```python
apply_rules_to_transaction(transaction, user)
  ├─ Matches against user's custom category rules
  ├─ Respects rule logic (AND/OR)
  └─ Returns matched custom category

_matches_condition(transaction, condition)
  ├─ Keyword matching
  ├─ Amount range matching
  ├─ Date range matching
  └─ Returns boolean
```

**Logic Types**:
- **OR Logic**: Transaction categorized if ANY condition matches
- **AND Logic**: Transaction categorized ONLY if ALL conditions match

---

### 5. Financial Overview (`analyzer/financial_overview_function.py`)

**Calculations**:
- Total income (sum of credit transactions)
- Total expenses (sum of debit transactions)
- Net savings (income - expenses)
- Category-wise breakdown
- Spending trend analysis
- Financial health score (0-100)

**Health Score Formula**:
```
score = (savings_ratio × 0.6) + (category_diversity × 0.4)
  where:
    savings_ratio = net_savings / total_income
    category_diversity = unique_categories / total_categories
```

---

## API Endpoints

### Authentication Routes
```
POST   /users/register/          - User registration
POST   /users/login/             - User login
POST   /users/logout/            - User logout
GET    /users/profile/           - User profile
```

### Account Management
```
GET    /analyzer/dashboard/      - Main dashboard
POST   /analyzer/create_account/ - Create new account
GET    /accounts/<id>/view/      - Account details
POST   /accounts/<id>/delete/    - Delete account
```

### Statement Processing
```
GET    /analyzer/upload/         - Upload form
POST   /analyzer/upload/         - Process statement
GET    /analyzer/results/        - Analysis results
```

### Rules Management
```
GET    /analyzer/rules/          - Global rules list
GET    /analyzer/rules/<id>/     - Rule details
POST   /rules/change-status/     - Toggle rule (AJAX)
```

### Custom Categories
```
GET    /analyzer/custom-categories/                    - List categories
POST   /analyzer/custom-categories/create/             - Create category
GET    /analyzer/custom-categories/<id>/rule/          - Create rule form
POST   /analyzer/custom-categories/<id>/rule/          - Create rule
POST   /analyzer/custom-categories/rule/<id>/edit/     - Edit rule
POST   /analyzer/custom-categories/rule/<id>/delete/   - Delete rule
POST   /analyzer/custom-categories/<id>/delete/        - Delete category
```

---

## User Workflows

### 🔄 Workflow 1: Upload and Analyze Statement

```
1. User logs in
   └─> Dashboard displayed

2. User clicks "Upload Statement"
   └─> Upload form shown

3. User selects bank account
   └─> File picker enabled

4. User selects PDF file
   └─> File preview shown

5. User clicks "Upload"
   └─> Server processes file:
       ├─ Extract text via OCR
       ├─ Detect layout (table vs. freeform)
       ├─ Parse transactions
       ├─ Extract UPI metadata
       └─ Store in database

6. Server displays results
   └─> Shows:
       ├─ Transaction list
       ├─ Category breakdown
       ├─ Active rules
       ├─ Financial summary
       └─ Action buttons
```

### 🏦 Workflow 2: Create Custom Category & Rule

```
1. User navigates to Results page
   └─> Clicks "Create Custom Category"

2. Step 1: Create Category
   └─ Fill in:
       ├─ Category name
       ├─ Description (optional)
       ├─ Color (optional)
       └─ Icon (optional)

3. Step 2: Create Rule
   └─ Fill in:
       ├─ Rule name
       ├─ Rule logic (AND/OR)
       └─ Add conditions:
           ├─ Keyword (multiple types)
           ├─ Amount (multiple operators)
           └─ Date (range)

4. Server saves rule
   └─> Linked to category

5. User is redirected to category list
   └─> New category appears
```

### ⚙️ Workflow 3: Manage Rules from Results Page

```
1. User uploads statement
   └─> Results page displayed

2. User scrolls to "Active Rules" section
   └─> Lists all active global rules

3. User toggles rule switch
   └─> AJAX request sent to server

4. Server updates rule.is_active
   └─> Database updated

5. Response returned
   └─> UI updates instantly
   └─> Success notification shown
```

### 📊 Workflow 4: View Account Details

```
1. User on Dashboard
   └─> Sees account cards

2. User clicks account card
   └─> Navigates to account details

3. Account details page shows:
   ├─ Account information
   ├─ Summary metrics (Income/Expenses/Savings)
   ├─ Financial health score
   ├─ Charts:
   │  ├─ Income vs Expenses
   │  └─ Spending by Category
   ├─ Transaction table
   └─ Navigation buttons

4. User can:
   ├─ Scroll through transactions
   ├─ View charts
   ├─ Click "Back to Dashboard"
   └─ Click "Delete Account"
```

---

## Global Rules System

### Overview

19 pre-configured global rules automatically categorize transactions based on keywords.

### Categories Covered

| Category | Rules | Keywords |
|----------|-------|----------|
| FOOD | 3 | Restaurants, Delivery Apps, Grocery |
| SHOPPING | 3 | E-commerce, Clothing, Department Stores |
| TRANSPORT | 3 | Ride-sharing, Fuel, Public Transport |
| ENTERTAINMENT | 2 | Movies, Gaming, Streaming |
| HEALTHCARE | 2 | Hospitals, Pharmacies |
| TRAVEL | 2 | Hotels, Flights |
| BILLS | 2 | Utilities, Insurance |
| LOANS | 1 | EMI Payments |

### Rule Structure

**Rule 1: Restaurants & Cafes**
```
Category: FOOD
Keywords: restaurant, cafe, pizza, burger
Logic: OR (any keyword matches)
Example: "Taj Restaurant Payment ₹850" → FOOD
```

**Rule 7: Ride Sharing Services**
```
Category: TRANSPORT
Keywords: uber, ola, lyft, bolt
Logic: OR (any keyword matches)
Example: "UBER TRIP ₹450" → TRANSPORT
```

### How They Work

1. Transaction description is extracted
2. Lowercased for matching
3. Checked against each rule's keywords
4. First matching rule wins (category assigned)
5. Stored in `transaction.category` field
6. User can override with custom categories

---

## Custom Categories System

### Features

Users can create unlimited custom categories with complex rules.

### Condition Types

#### 1. Keyword Condition
- **Match Types**: Contains, Starts With, Ends With, Exact Match
- **Example**: "Netflix" contains search for streaming subscriptions

#### 2. Amount Condition
- **Operators**: =, >, <, >=, <=, Between
- **Example**: Amount between ₹500-₹2000 for subscription services

#### 3. Date Condition
- **Format**: Date range selection
- **Example**: Transactions in December (seasonal categorization)

### Rule Logic

- **AND Logic**: Transaction must match ALL conditions
- **OR Logic**: Transaction must match ANY condition

**Example (AND)**:
```
Rule: "Premium Subscriptions"
  AND
  - Description contains "Netflix"
  - Amount between ₹300-₹500
  
Result: Only Netflix payments in ₹300-₹500 range match
```

**Example (OR)**:
```
Rule: "Streaming Services"
  OR
  - Description contains "Netflix"
  - Description contains "Prime"
  - Description contains "HotStar"
  
Result: Any transaction containing these keywords match
```

---

## OCR & Statement Processing

### Supported Formats

1. **Scanned PDFs** (image-based)
   - OCR via Tesseract
   - Configurable DPI (200 recommended)
   - Multi-page support

2. **Native PDFs** (text-embedded)
   - pdfplumber extraction
   - Faster, more accurate
   - Fallback to OCR if needed

3. **Image Files** (JPG, PNG)
   - Direct OCR processing
   - Batch processing capable

### Processing Pipeline

```
Input File
    ↓
Format Detection
    ├─ PDF with text → pdfplumber
    ├─ Scanned PDF → Tesseract OCR
    └─ Image → Tesseract OCR
    ↓
Text Extraction
    └─ Returns raw text/table
    ↓
Layout Detection
    ├─ Table-like? → Parse tables
    └─ Freeform? → Parse text blocks
    ↓
Transaction Parsing
    ├─ Find date markers
    ├─ Merge multi-line blocks
    ├─ Extract amounts
    └─ Infer debit/credit
    ↓
UPI Metadata Extraction
    └─ Parse UPI patterns
    ↓
Categorization
    ├─ Apply global rules
    ├─ Apply custom rules
    └─ Store transaction
    ↓
Database Storage
    └─ Save to Transaction model
    ↓
Results Display
    └─ Show to user
```

### Key Algorithms

#### Multi-Line Block Merging
```python
# Problem: OCR wraps descriptions across multiple lines
# Solution: Merge lines starting with continuation patterns

Input:
  2024-01-15 UBER TRIP
  PAYMENT DELHI ₹450

Output:
  2024-01-15 UBER TRIP PAYMENT DELHI ₹450
```

#### Intelligent Amount Parsing
```python
# Problem: OCR noise, multiple numbers (dates, IDs, amounts)
# Solution: Context-based heuristics

Input: "2024-01-15 Transaction 123456 ₹1,55,248.00"
Output: ₹1,55,248.00 (correctly identifies amount despite noise)
```

#### Indian Number Format Handling
```python
# Support both formats:
₹1,55,248.00  (Indian: 1 + 2-digit groups)
₹155248.00    (Western: continuous digits)
```

---

## Testing & Quality Assurance

### Test Coverage

#### Feature Tests
- [x] Delete account functionality
- [x] Account details page rendering
- [x] Financial metrics calculation
- [x] Chart data generation
- [x] Rule toggling (AJAX)
- [x] Custom category creation
- [x] Rule condition matching
- [x] OCR text extraction
- [x] UPI metadata parsing
- [x] Transaction categorization

#### Security Tests
- [x] User ownership verification
- [x] CSRF token protection
- [x] SQL injection prevention
- [x] XSS protection
- [x] Login requirement enforcement
- [x] Permission-based access control

#### Performance Tests
- [x] Large file processing (10+ MB PDFs)
- [x] Multi-page statement handling
- [x] Bulk transaction processing
- [x] Chart rendering with 1000+ transactions
- [x] AJAX response times

---

## Version History

### v2.2 (December 11, 2025) - Current
✅ **Status**: COMPLETE & PRODUCTION-READY

**Features Added**:
1. Delete Account Functionality
2. Account-Specific Financial Overview
3. Navigation Controls
4. Change Rule Status on Results Page

**Files Created**: 2 new templates (480 + 250 lines)  
**Files Modified**: 5 files (~150 lines total)  
**Total Code Added**: 730+ lines  
**Database Changes**: None (uses existing models)  
**Migrations Required**: None  

---

### v2.1 (Previous Release)

**Features**:
1. Global Rules Application Prompt
2. Transaction Filtering by Month
3. Transaction Sorting by Date
4. Active Rules Display
5. Rule Toggle AJAX Endpoint

---

### v2.0 & Earlier

**Features**:
1. Statement upload and processing
2. OCR-based transaction extraction
3. UPI metadata parsing
4. 19 global categorization rules
5. Custom category system
6. Financial overview
7. Account management
8. User authentication

---

## Documentation Files Guide

This project includes comprehensive documentation:

| File | Purpose | Audience |
|------|---------|----------|
| QUICK_START_v2.1.md | Feature user guide | End users |
| ENHANCEMENTS_v2.1.md | Technical details | Developers |
| QUICK_REFERENCE_v2.2.md | Quick overview | Everyone |
| FEATURES_v2.2.md | Feature documentation | Product managers |
| CHANGELOG_v2.2.md | Detailed changes | Developers |
| PROJECT_COMPLETION_REPORT_v2.2.md | Project sign-off | Project managers |
| CUSTOM_CATEGORIES_GUIDE.md | Custom rule guide | End users |
| GLOBAL_RULES_REFERENCE.md | Rule reference | End users |
| OCR_AND_PARSING_SYSTEM.md | Technical OCR docs | Developers |
| TESTING_GUIDE_v2.2.md | Testing procedures | QA testers |
| FINAL_CHECKLIST_v2.2.md | Verification checklist | QA leads |

---

## Getting Started

### Prerequisites
- Python 3.8+
- Django 3.2+
- Tesseract OCR
- SQLite3

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

### First Steps
1. Navigate to http://127.0.0.1:8000/
2. Create user account
3. Login
4. Create bank account
5. Upload statement
6. View results
7. Explore features

---

## Support & Maintenance

### Common Issues

**OCR Not Working**:
- Verify Tesseract installation
- Check DPI settings in pdf_parser.py
- Try increasing DPI (200 → 300)

**Rules Not Matching**:
- Check rule is_active status
- Verify keyword capitalization
- Test with debugging in rules_engine.py

**Charts Not Rendering**:
- Verify Chart.js library loaded
- Check browser console for errors
- Ensure transaction data exists

---

## Future Enhancements

1. **Advanced Analytics**
   - Spending trends over time
   - Budget tracking
   - Savings goals
   - Spending forecasts

2. **Export Features**
   - PDF reports
   - CSV export
   - Excel integration
   - Tax report generation

3. **Bank Integrations**
   - Direct bank API connections
   - Real-time transaction sync
   - Multiple bank support

4. **Mobile App**
   - Native iOS/Android apps
   - Offline support
   - Push notifications

5. **AI Features**
   - Smart category suggestions
   - Anomaly detection
   - Spending insights
   - Natural language rules

---

## License & Credits

**Project**: BankWatch  
**Version**: 2.2  
**Status**: Production-Ready  
**Last Updated**: December 13, 2025  

---

**End of Complete Project Summary**

For detailed information on specific areas, refer to the individual documentation files listed in the Documentation Files Guide section.
