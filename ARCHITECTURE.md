# Implementation Architecture

## High-Level Flow

```
User Uploads File
    ↓
┌─────────────────────────────────────┐
│  StatementParser.parse_file()       │
├─────────────────────────────────────┤
│ Determine file type:                │
│  - PDF → PDFParser                  │
│  - EXCEL → ExcelParser (NEW)        │
│  - CSV → CSVParser (NEW)            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  ExcelParser.extract_transactions() │
├─────────────────────────────────────┤
│ NEW: Multi-strategy approach        │
│  1. HTML format detection           │
│  2. Read Excel with multiple engines│
│  3. Smart column detection          │
│  4. Parse rows with validation      │
│  5. Return transactions or error    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  ExcelParser._find_columns()        │
├─────────────────────────────────────┤
│ NEW: Intelligent column mapping     │
│                                     │
│ Strategy 1: Exact Match            │
│  ├─ Check BANK_FORMATS registry     │
│  ├─ Try each bank's patterns        │
│  └─ Return match if found           │
│                                     │
│ Strategy 2: Fuzzy Match            │
│  ├─ Handle case variations          │
│  ├─ Handle underscore/space         │
│  └─ Return match if found           │
│                                     │
│ Strategy 3: Keywords               │
│  ├─ Look for 'date', 'amount'       │
│  ├─ Fallback patterns               │
│  └─ Return match if found           │
│                                     │
│ Strategy 4: Error                  │
│  └─ Throw error with columns found  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Row Processing                     │
├─────────────────────────────────────┤
│ For each row:                       │
│  1. Parse date (10+ formats)        │
│  2. Get description                 │
│  3. Get amount and type:            │
│     - Strategy 1: D/C flag column   │
│     - Strategy 2: Separate D/C cols │
│     - Strategy 3: Single amt + sign │
│  4. Validate (no zeros, no nulls)   │
│  5. Add to transactions or skip     │
│                                     │
│ Log: Why each row was skipped       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Return Results                     │
├─────────────────────────────────────┤
│ ✅ If transactions found:           │
│    Return list of transactions      │
│                                     │
│ ❌ If no transactions found:        │
│    Throw error with details:        │
│    - Columns found                  │
│    - Rows skipped and why           │
│    - Total count                    │
└─────────────────────────────────────┘
    ↓
View processes results & creates DB records
```

---

## Bank Format Registry

```
ExcelParser.BANK_FORMATS = {
    'PLANET': {
        'date_patterns': ['transactiondate', 'transaction_date', ...],
        'description_patterns': ['description', 'narration', ...],
        'amount_patterns': ['amountinaccount', 'amount_in_account', ...],
        'debit_credit_flag': ['creditdebitflag', 'credit_debit_flag', ...],
    },
    'GENERIC': {
        'date_patterns': ['date', 'transaction date', ...],
        'description_patterns': ['description', 'narration', ...],
        'amount_patterns': ['amount', 'value', ...],
        'debit_patterns': ['debit', 'withdrawal', ...],
        'credit_patterns': ['credit', 'deposit', ...],
    },
    'ICICI': { ... },
    'HDFC': { ... },
    # More banks...
}
```

---

## Column Detection Priority

```
For each bank format in BANK_FORMATS:
  For each pattern in format[category]:
    If pattern matches column name exactly:
      ✅ Return this column (highest confidence)

If not found via exact match:
  For each column in file:
    If column contains keyword from patterns:
      ✅ Return this column (medium confidence)

If still not found:
  ❌ Throw error with:
      - Actual columns found in file
      - What we were looking for
      - Human-readable error message
```

---

## Date Parsing Priority

```
Supported formats (tried in order):
1. %d/%m/%Y    (01/10/2025) ← PLANET format
2. %d/%m/%y    (01/10/25)
3. %d-%m-%Y    (01-10-2025)
4. %d-%m-%y    (01-10-25)
5. %Y-%m-%d    (2025-10-01)
6. %d%m%Y      (01102025)
7. %d %b %Y    (01 Oct 2025)
8. %d %B %Y    (01 October 2025)
9. %m/%d/%Y    (10/01/2025) US format
10. %m-%d-%Y   (10-01-2025) US format

If date_value is already datetime object:
  ✅ Return as-is (pandas auto-parsing)

If no format matches:
  ❌ Skip row and log reason
```

---

## Transaction Type Detection Priority

```
Priority 1: Debit/Credit Flag Column
  ├─ Check if column exists (CreditDebitFlag)
  ├─ Read value: D/C, DEBIT/CREDIT, DR/CR
  └─ Set transaction_type = DEBIT or CREDIT
  
If flag column not found:
  
Priority 2: Separate Debit/Credit Columns
  ├─ Check for separate debit & credit columns
  ├─ If debit only → DEBIT
  ├─ If credit only → CREDIT
  └─ If both → use larger value
  
If separate columns not found:
  
Priority 3: Single Amount Column with Sign
  ├─ Check for minus sign (-)
  ├─ If present → DEBIT
  └─ If absent → CREDIT
```

---

## Error Messages

### User sees detailed errors like:

```
ERROR: Could not find DATE column in Excel file.
Found columns: UnknownCol1, UnknownCol2, UnknownCol3

ACTION: Check your file has a Date column with one of these names:
- Date, TransactionDate, Transaction Date, Tran Date, Posted Date
```

---

## Logging Output

### Console/Log shows:

```
INFO: Starting to parse Excel file: .../sample.xlsx
INFO: Successfully read Excel file with engine: openpyxl
INFO: Excel file loaded with columns: ['TransactionDate', 'Description', ...]
INFO: Cleaned column names: ['transactiondate', 'description', ...]
DEBUG: Finding columns from: ['transactiondate', 'description', ...]
INFO: Bank format PLANET: Found date column via exact match: transactiondate
INFO: Bank format PLANET: Found amount column via exact match: amountinaccount
INFO: Column mapping - Date:transactiondate, Amount:amountinaccount, ...
DEBUG: Parsed date '01/10/2025' with format '%d/%m/%Y' -> 2025-10-01
DEBUG: Row 0: ✓ Extracted | 2025-10-01 | UPI/DR/... | ₹1481.0 (DEBIT)
...
INFO: Excel parsing complete: 206 transactions extracted
INFO: Skipped rows - invalid_date: 1, no_amount: 2, zero_amount: 0
```

---

## Before vs After Code

### BEFORE: Silent Failure
```python
if not date_col:
    print("Could not find date column")
    return StatementParser._create_sample_transactions()  # ← Returns 3 dummy!
```

### AFTER: Detailed Error
```python
if not date_col:
    col_list = ", ".join(original_columns)
    error_msg = f"Could not find DATE column in Excel file. " \
                f"Found columns: {col_list}"
    logger.error(error_msg)
    raise ValueError(error_msg)  # ← User sees what's wrong!
```

---

## Extensibility

### Adding a New Bank Format

```python
BANK_FORMATS = {
    'YOUR_BANK': {
        'date_patterns': ['column1', 'column2', ...],
        'description_patterns': ['desc_col1', 'desc_col2', ...],
        'amount_patterns': ['amount1', 'amount2', ...],
        'debit_credit_flag': ['flag_col'],  # OR
        'debit_patterns': ['debit_col'],
        'credit_patterns': ['credit_col'],
    }
}
```

That's it! The `_find_columns()` method will automatically:
1. Detect your bank format
2. Find matching columns
3. Parse transactions correctly

---

## Testing Architecture

```
test_parser.py
  └─ Tests your actual 206-transaction file
     ├─ File format detection
     ├─ Column matching
     ├─ Date parsing  
     └─ Transaction extraction (expects 206)

test_parser_edge_cases.py
  ├─ Test 1: No recognizable columns
  │   └─ Expects: ValueError with columns listed
  ├─ Test 2: Valid columns with bad data
  │   └─ Expects: Extract valid, skip invalid
  └─ Test 3: PLANET format manually created
      └─ Expects: All rows extract correctly
```

---

**Architecture**: Robust | **Extensible**: Yes | **Status**: ✅ Production Ready
