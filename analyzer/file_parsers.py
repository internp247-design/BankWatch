import re
from datetime import datetime
import os
import warnings
import logging
warnings.filterwarnings('ignore')

# Configure logging for PDF parsing
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Try to import optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not installed. Excel/CSV support limited.")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not installed. PDF support limited.")

# Try to import PyMuPDF for OCR fallback
try:
    import fitz
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("PyMuPDF/Tesseract not available. Scanned PDF support limited.")

# File type constants
PDF = 'PDF'
EXCEL = 'EXCEL'
CSV = 'CSV'

class StatementParser:
    """Parser for different types of bank statement files"""
    
    @staticmethod
    def parse_file(file_path, file_type):
        """Parse file based on type with error handling"""
        logger.info(f"Starting to parse file: {file_path} (type: {file_type})")
        
        try:
            if file_type == PDF:
                return PDFParser.extract_transactions(file_path)
            elif file_type == EXCEL:
                return ExcelParser.extract_transactions(file_path)
            elif file_type == CSV:
                return CSVParser.extract_transactions(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Parse file failed for {file_path}: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_file_type(filename):
        """Determine file type from filename"""
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.pdf':
            return PDF
        elif ext in ['.xlsx', '.xls']:
            return EXCEL
        elif ext == '.csv':
            return CSV
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
    
    @staticmethod
    def _create_sample_transactions():
        """Create sample transactions for testing"""
        return [
            {
                'date': datetime.now().date(),
                'description': 'Salary Deposit',
                'amount': 50000.00,
                'transaction_type': 'CREDIT'
            },
            {
                'date': datetime.now().date(),
                'description': 'Grocery Shopping at Big Bazaar',
                'amount': 2500.50,
                'transaction_type': 'DEBIT'
            },
            {
                'date': datetime.now().date(),
                'description': 'Internet Bill Payment - Airtel',
                'amount': 899.00,
                'transaction_type': 'DEBIT'
            }
        ]

class PDFParser:
    """Parse transactions from various PDF bank statements with fallback support"""

    @staticmethod
    def extract_transactions(pdf_path):
        """Extract transactions from PDF, with bank detection and fallback strategies"""
        transactions = []
        logger.info(f"Starting PDF parsing for: {os.path.basename(pdf_path)}")

        if not PDFPLUMBER_AVAILABLE:
            logger.error("pdfplumber not available, cannot parse PDF")
            return []

        try:
            # First try: Extract transactions from tables (table-based bank statements)
            logger.info("Attempting to extract transactions from tables...")
            transactions = PDFParser._extract_from_tables(pdf_path)
            
            if transactions:
                logger.info(f"Successfully extracted {len(transactions)} transactions from tables")
                transactions.sort(key=lambda x: x['date'] if x['date'] else datetime.now().date())
                return transactions
            
            # Fallback: Extract with pdfplumber (embedded text)
            logger.info("No tables found, attempting text extraction...")
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
            
            if not full_text.strip():
                logger.warning(f"No embedded text found in PDF, attempting OCR fallback")
                if OCR_AVAILABLE:
                    transactions = PDFParser._extract_via_ocr(pdf_path)
                else:
                    logger.error("OCR not available for scanned PDF")
                    return []
            else:
                logger.info(f"PDF has embedded text ({len(full_text)} chars), detecting bank format...")
                # Detect bank format and use appropriate parser
                bank_type = PDFParser._detect_bank_format(full_text)
                logger.info(f"Detected bank format: {bank_type}")
                
                if bank_type == 'SBI':
                    transactions = PDFParser._parse_sbi_format(full_text)
                elif bank_type == 'GENERIC':
                    transactions = PDFParser._parse_generic_format(full_text)
                else:
                    transactions = PDFParser._parse_generic_format(full_text)
        
        except Exception as e:
            logger.error(f"PDF parsing error: {e}", exc_info=True)
            # Try OCR fallback on any error
            if OCR_AVAILABLE:
                try:
                    logger.info("Attempting OCR fallback after parsing error...")
                    transactions = PDFParser._extract_via_ocr(pdf_path)
                except Exception as ocr_error:
                    logger.error(f"OCR fallback failed: {ocr_error}")
            return []
        
        # Sort by date and validate
        if transactions:
            transactions.sort(key=lambda x: x['date'] if x['date'] else datetime.now().date())
            logger.info(f"Successfully extracted {len(transactions)} transactions")
            return transactions
        else:
            logger.warning("No transactions extracted from PDF")
            return []

    @staticmethod
    def _extract_from_tables(pdf_path):
        """Extract transactions from PDF tables (table-based bank statements).
        
        Supports both:
        1. Separate DEBIT and CREDIT columns (reads from appropriate column)
        2. Single AMOUNT column with +/- signs (uses minus sign detection)
        """
        transactions = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    
                    if not tables:
                        logger.debug(f"No tables found on page {page_num + 1}")
                        continue
                    
                    logger.info(f"Found {len(tables)} table(s) on page {page_num + 1}")
                    
                    for table_idx, table in enumerate(tables):
                        if not table or len(table) < 2:
                            continue
                        
                        # Log header for debugging
                        header = table[0]
                        logger.debug(f"Table {table_idx} header: {header}")
                        
                        # Identify column indices
                        date_col, desc_col, debit_col, credit_col, amount_col = PDFParser._identify_table_columns(header)
                        logger.info(f"Table {table_idx} - Date:[{date_col}] Desc:[{desc_col}] Debit:[{debit_col}] Credit:[{credit_col}] Amount:[{amount_col}]")
                        
                        # Process data rows (skip header)
                        for row_idx, row in enumerate(table[1:], 1):
                            if not row or len(row) < 3:
                                continue
                            
                            try:
                                # Parse table row
                                date_str = row[date_col].strip() if date_col < len(row) and row[date_col] else ""
                                description = row[desc_col].strip() if desc_col < len(row) and row[desc_col] else ""
                                
                                if not date_str or not description:
                                    logger.debug(f"Row {row_idx}: Skipping - missing date or description")
                                    continue
                                
                                # Parse date from format like "24\nJAN" or "24 JAN"
                                date_obj = PDFParser._parse_table_date(date_str)
                                if not date_obj:
                                    logger.debug(f"Row {row_idx}: Could not parse date: {date_str}")
                                    continue
                                
                                # Determine transaction type and amount
                                amount = None
                                trans_type = None
                                
                                # Strategy 1: Try separate DEBIT and CREDIT columns first
                                if debit_col is not None and credit_col is not None:
                                    debit_str = row[debit_col].strip() if debit_col < len(row) and row[debit_col] else ""
                                    credit_str = row[credit_col].strip() if credit_col < len(row) and row[credit_col] else ""
                                    
                                    # Remove common empty placeholders
                                    debit_empty = not debit_str or debit_str.upper() in ['', 'NONE', '-', '0', '0.00']
                                    credit_empty = not credit_str or credit_str.upper() in ['', 'NONE', '-', '0', '0.00']
                                    
                                    # Prefer non-empty column
                                    if not debit_empty and credit_empty:
                                        # Debit has value, credit is empty
                                        amount, _ = PDFParser._parse_table_amount(debit_str)
                                        trans_type = 'DEBIT'
                                        logger.debug(f"Row {row_idx}: Found in DEBIT column[{debit_col}]: {debit_str}")
                                    elif debit_empty and not credit_empty:
                                        # Credit has value, debit is empty
                                        amount, _ = PDFParser._parse_table_amount(credit_str)
                                        trans_type = 'CREDIT'
                                        logger.debug(f"Row {row_idx}: Found in CREDIT column[{credit_col}]: {credit_str}")
                                    elif not debit_empty and not credit_empty:
                                        # Both have values - use the one that's not zero
                                        debit_amount, _ = PDFParser._parse_table_amount(debit_str)
                                        credit_amount, _ = PDFParser._parse_table_amount(credit_str)
                                        
                                        if debit_amount and (not credit_amount or debit_amount > 0):
                                            amount = debit_amount
                                            trans_type = 'DEBIT'
                                            logger.debug(f"Row {row_idx}: Both columns non-empty, using DEBIT: {debit_str}")
                                        elif credit_amount:
                                            amount = credit_amount
                                            trans_type = 'CREDIT'
                                            logger.debug(f"Row {row_idx}: Both columns non-empty, using CREDIT: {credit_str}")
                                
                                # Strategy 2: Fallback to single amount column if separate columns didn't work
                                if amount is None and amount_col is not None:
                                    amount_str = row[amount_col].strip() if amount_col < len(row) and row[amount_col] else ""
                                    if amount_str:
                                        amount, trans_type = PDFParser._parse_table_amount(amount_str)
                                        logger.debug(f"Row {row_idx}: Using fallback AMOUNT column[{amount_col}]: {amount_str}")
                                
                                if amount is None or trans_type is None:
                                    logger.debug(f"Row {row_idx}: Could not parse amount or determine transaction type")
                                    continue
                                
                                transaction = {
                                    'date': date_obj,
                                    'description': description[:500],
                                    'amount': amount,
                                    'transaction_type': trans_type
                                }
                                transactions.append(transaction)
                                logger.info(f"Row {row_idx}: Extracted | {date_obj} | {description[:30]}... | ₹{amount} ({trans_type})")
                            
                            except Exception as e:
                                logger.debug(f"Row {row_idx}: Error processing - {e}")
                                continue
            
            logger.info(f"Total transactions extracted from tables: {len(transactions)}")
            return transactions
        
        except Exception as e:
            logger.error(f"Table extraction failed: {e}", exc_info=True)
            return []

    @staticmethod
    def _extract_amount_and_type(amount_str):
        """Extract amount and transaction type from string, using minus sign as source of truth.
        
        Minus sign indicates DEBIT. No minus sign (or plus sign) indicates CREDIT.
        Returns: (absolute_amount, transaction_type) or (None, None) on error
        """
        if not amount_str:
            return None, None
        
        # Remove whitespace and newlines
        amount_str = amount_str.replace('\n', '').strip()
        
        # Check for minus sign as the primary indicator of DEBIT
        has_minus = '-' in amount_str
        
        # Determine transaction type: minus = DEBIT, no minus = CREDIT
        trans_type = 'DEBIT' if has_minus else 'CREDIT'
        
        # Extract numeric value (remove currency symbol, commas, +/- signs)
        match = re.search(r'[\d,]+\.?\d*', amount_str)
        if not match:
            return None, None
        
        try:
            amount = float(match.group().replace(',', ''))
            if amount <= 0:
                return None, None
            return amount, trans_type
        except (ValueError, AttributeError):
            return None, None

    @staticmethod
    def _parse_table_amount(amount_str):
        """Parse amount from string like '₹50000.00' or '-₹2500.50' or '+₹50000.00'
        
        Uses minus sign as the primary indicator for transaction type.
        """
        return PDFParser._extract_amount_and_type(amount_str)

    @staticmethod
    def _parse_table_date(date_str):
        """Parse date from string like '24\\nJAN' or '24 JAN' or '24-01-2025'"""
        if not date_str:
            return None
        
        # Clean up whitespace and newlines
        date_str = date_str.replace('\n', ' ').strip()
        
        # Try multiple date formats
        formats = [
            '%d %b',        # "24 JAN"
            '%d %B',        # "24 January"
            '%d-%m-%Y',     # "24-01-2025"
            '%d/%m/%Y',     # "24/01/2025"
            '%d %b %Y',     # "24 JAN 2025"
            '%d %B %Y',     # "24 January 2025"
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # If year not provided, use current year (2026)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=2026)
                return parsed.date()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse table date with any format: {date_str}")
        return None

    @staticmethod
    def _identify_table_columns(header):
        """Identify column indices for date, description, debit, credit, and amount columns.
        
        Analyzes table header to find:
        - Date column (transaction date, tran date, posted, etc.)
        - Description column (description, narration, particulars, trans desc, etc.)
        - Debit column (debit, withdrawal, dr, debit amt, etc.)
        - Credit column (credit, deposit, cr, credit amt, etc.)
        - Amount column (fallback for single amount column with +/- signs)
        
        Returns: (date_col, desc_col, debit_col, credit_col, amount_col)
        """
        if not header:
            return 0, 1, None, None, 3
        
        date_col = None
        desc_col = None
        debit_col = None
        credit_col = None
        amount_col = None
        
        # Convert header to lowercase for comparison
        header_lower = [str(h).lower() if h else "" for h in header]
        
        # Find columns by keyword matching
        for idx, col_name in enumerate(header_lower):
            if not col_name:
                continue
            
            if any(kw in col_name for kw in ['date', 'transaction date', 'tran date', 'posted']):
                date_col = idx
            elif any(kw in col_name for kw in ['description', 'narration', 'particulars', 'details', 'trans desc']):
                desc_col = idx
            elif any(kw in col_name for kw in ['debit', 'withdrawal', 'dr', 'debit amt']):
                debit_col = idx
            elif any(kw in col_name for kw in ['credit', 'deposit', 'cr', 'credit amt']):
                credit_col = idx
            elif any(kw in col_name for kw in ['amount', 'value']):
                amount_col = idx
        
        # Use defaults if not found
        if date_col is None:
            date_col = 0
        if desc_col is None:
            desc_col = 1
        if amount_col is None:
            amount_col = 3
        
        logger.debug(f"Table columns identified - Date: {date_col}, Desc: {desc_col}, Debit: {debit_col}, Credit: {credit_col}, Amount: {amount_col}")
        
        return date_col, desc_col, debit_col, credit_col, amount_col

    @staticmethod
    def _detect_bank_format(text):
        """Detect which bank format the PDF contains"""
        text_lower = text.lower()
        
        if 'sbi' in text_lower or 'state bank' in text_lower:
            return 'SBI'
        elif 'canara' in text_lower:
            return 'CANARA'
        elif 'icici' in text_lower:
            return 'ICICI'
        elif 'hdfc' in text_lower:
            return 'HDFC'
        elif 'axis' in text_lower:
            return 'AXIS'
        else:
            return 'GENERIC'

    @staticmethod
    def _parse_sbi_format(text):
        """Parse SBI-style statements with flexible regex patterns"""
        transactions = []
        logger.debug("Parsing with SBI format rules")
        
        # Pattern 1: DEBIT transactions (- - amount balance)
        debit_pattern = re.compile(
            r'(\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\s+'     # Date: DD-MM-YY or DD/MM/YYYY
            r'(.+?)\s+'
            r'-\s+-\s+'
            r'([\d,]+\.?\d+)\s+'
            r'([\d,]+\.?\d+)'
        )
        
        # Pattern 2: CREDIT transactions (- amount - balance)
        credit_pattern = re.compile(
            r'(\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\s+'
            r'(.+?)\s+'
            r'-\s+'
            r'([\d,]+\.?\d+)\s+'
            r'-\s+'
            r'([\d,]+\.?\d+)'
        )
        
        # Extract DEBIT transactions
        for match in debit_pattern.finditer(text):
            date_str, description, amount_str, _balance = match.groups()
            transaction = PDFParser._parse_transaction(date_str, description, amount_str, 'DEBIT')
            if transaction:
                transactions.append(transaction)
        
        # Extract CREDIT transactions
        for match in credit_pattern.finditer(text):
            date_str, description, amount_str, _balance = match.groups()
            transaction = PDFParser._parse_transaction(date_str, description, amount_str, 'CREDIT')
            if transaction:
                transactions.append(transaction)
        
        logger.debug(f"SBI format: extracted {len(transactions)} transactions")
        return transactions

    @staticmethod
    def _parse_generic_format(text):
        """Parse generic bank statement formats"""
        transactions = []
        logger.debug("Parsing with generic format rules")
        
        # More flexible patterns for various bank formats
        # Pattern: date description amount type balance
        generic_pattern = re.compile(
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+'
            r'([A-Za-z0-9\s/.,:-]+?)\s+'
            r'(DR|CR|D|C|DEBIT|CREDIT)\s+'
            r'([\d,]+\.?\d+)'
        )
        
        for match in generic_pattern.finditer(text):
            date_str, description, trans_type, amount_str = match.groups()
            trans_type_mapped = 'DEBIT' if trans_type.upper() in ['DR', 'D', 'DEBIT'] else 'CREDIT'
            transaction = PDFParser._parse_transaction(date_str, description, amount_str, trans_type_mapped)
            if transaction:
                transactions.append(transaction)
        
        logger.debug(f"Generic format: extracted {len(transactions)} transactions")
        return transactions

    @staticmethod
    def _extract_via_ocr(pdf_path):
        """Extract transactions from scanned PDF using OCR"""
        logger.info("Extracting via OCR for scanned PDF...")
        transactions = []
        
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            
            for page_num, page in enumerate(doc):
                logger.debug(f"OCR processing page {page_num + 1}")
                pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img)
                full_text += ocr_text + "\n"
            
            doc.close()
            
            if full_text.strip():
                # Try to parse the OCR'd text
                transactions = PDFParser._parse_generic_format(full_text)
                logger.info(f"OCR extraction: {len(transactions)} transactions found")
            else:
                logger.warning("OCR produced no text")
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}", exc_info=True)
        
        return transactions

    @staticmethod
    def _parse_transaction(date_str, description, amount_str, trans_type=None):
        """Helper method to parse individual transaction with flexible date parsing.
        
        If trans_type is not provided, it will be extracted from the amount_str using minus sign detection.
        """
        try:
            date = PDFParser._parse_date(date_str)
            
            if date is None:
                logger.warning(f"Could not parse date: {date_str}")
                return None
            
            description = description.strip()[:500]  # Limit description length
            
            # If trans_type provided, use standard parsing; otherwise extract from amount
            if trans_type:
                amount = float(amount_str.replace(',', ''))
                if amount <= 0:
                    logger.debug(f"Skipping zero/negative amount: {amount}")
                    return None
                final_trans_type = trans_type
            else:
                # Use minus sign detection for automatic type determination
                amount, final_trans_type = PDFParser._extract_amount_and_type(amount_str)
                if amount is None:
                    logger.debug(f"Could not parse amount: {amount_str}")
                    return None
            
            transaction = {
                'date': date,
                'description': description,
                'amount': amount,
                'transaction_type': final_trans_type
            }
            logger.debug(f"Parsed transaction: {date} {description[:30]}... {amount} {final_trans_type}")
            return transaction
        
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse transaction - Date: {date_str}, Amount: {amount_str}, Error: {e}")
            return None

    @staticmethod
    def _parse_date(date_str):
        """Parse date string with multiple format support"""
        try:
            if not date_str or (isinstance(date_str, float) and pd.isna(date_str)):
                return None
            
            date = None
            date_formats = [
                '%d/%m/%Y',      # DD/MM/YYYY (your PLANET format)
                '%d/%m/%y',      # DD/MM/YY
                '%d-%m-%Y',      # DD-MM-YYYY
                '%d-%m-%y',      # DD-MM-YY
                '%Y-%m-%d',      # YYYY-MM-DD
                '%d%m%Y',        # DDMMYYYY
                '%d %b %Y',      # DD MON YYYY (e.g., 01 Jan 2025)
                '%d %B %Y',      # DD MONTH YYYY (e.g., 01 January 2025)
                '%m/%d/%Y',      # MM/DD/YYYY (US format)
                '%m-%d-%Y',      # MM-DD-YYYY (US format)
            ]
            
            date_str_clean = str(date_str).strip()
            
            for fmt in date_formats:
                try:
                    date = datetime.strptime(date_str_clean, fmt).date()
                    logger.debug(f"Parsed date '{date_str}' with format '{fmt}' -> {date}")
                    return date
                except ValueError:
                    continue
            
            logger.debug(f"Could not parse date with any format: {date_str}")
            return None
        except Exception as e:
            logger.debug(f"Error parsing date: {date_str}, {e}")
            return None

class ExcelParser:
    """Parse transactions from Excel bank statements"""
    
    # Bank format registry - maps bank/format names to column patterns
    BANK_FORMATS = {
        'PLANET': {
            'date_patterns': ['transactiondate', 'transaction_date', 'transaction date'],
            'description_patterns': ['description', 'narration', 'particulars'],
            'amount_patterns': ['amountinaccount', 'amount_in_account', 'amount in account', 'amount'],
            'debit_credit_flag': ['creditdebitflag', 'credit_debit_flag', 'debit_credit_flag', 'dr_cr'],
            'value_date_patterns': ['valuedate', 'value_date', 'value date'],
        },
        'GENERIC': {
            'date_patterns': ['date', 'transaction date', 'tran date', 'posted date'],
            'description_patterns': ['description', 'narration', 'particulars', 'details', 'memo'],
            'amount_patterns': ['amount', 'value', 'transaction amount'],
            'debit_patterns': ['debit', 'withdrawal', 'dr', 'debit amt'],
            'credit_patterns': ['credit', 'deposit', 'cr', 'credit amt'],
        },
        'ICICI': {
            'date_patterns': ['date', 'transaction date', 'tran date'],
            'description_patterns': ['description', 'narration', 'particulars'],
            'amount_patterns': ['amount', 'debit', 'credit'],
            'debit_credit_flag': ['debit/credit', 'debit_or_credit', 'dr_cr'],
        },
        'HDFC': {
            'date_patterns': ['date', 'transaction date'],
            'description_patterns': ['description', 'narration'],
            'amount_patterns': ['amount', 'debit amt', 'credit amt'],
        },
    }
    
    @staticmethod
    def extract_transactions(excel_path):
        """Extract transactions from Excel file"""
        if not PANDAS_AVAILABLE:
            logger.error("Excel parsing not available. Install pandas.")
            raise ImportError("pandas not installed. Excel/CSV support requires: pip install pandas openpyxl xlrd")
        
        transactions = []
        logger.info(f"Starting to parse Excel file: {excel_path}")
        
        # First, check if this is an HTML file disguised as Excel
        try:
            with open(excel_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_bytes = f.read(100)
                if '<html' in first_bytes.lower() or '<table' in first_bytes.lower():
                    logger.info("Detected HTML format in Excel file, attempting HTML parsing...")
                    try:
                        from bs4 import BeautifulSoup
                        with open(excel_path, 'r', encoding='utf-8') as html_file:
                            html_content = html_file.read()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        rows = soup.find_all('tr')
                        
                        for idx, row in enumerate(rows[1:]):  # Skip header
                            cells = row.find_all('td')
                            if len(cells) < 5:
                                continue
                            
                            try:
                                cell_values = [cell.get_text(strip=True).replace('\u200b', '').strip() for cell in cells]
                                
                                if cell_values[0] == 'TransactionDate':
                                    continue
                                
                                date_str = cell_values[0]
                                description = cell_values[2]
                                debit_credit = cell_values[3]
                                amount_str = cell_values[4]
                                
                                if not date_str or not amount_str or not description:
                                    continue
                                
                                try:
                                    date = datetime.strptime(date_str, '%d/%m/%Y').date()
                                except ValueError:
                                    continue
                                
                                try:
                                    amount = float(amount_str.replace(',', ''))
                                except ValueError:
                                    continue
                                
                                transaction_type = 'DEBIT' if debit_credit.upper() == 'D' else 'CREDIT'
                                
                                transactions.append({
                                    'date': date,
                                    'description': description,
                                    'amount': amount,
                                    'transaction_type': transaction_type
                                })
                            except (IndexError, ValueError):
                                continue
                        
                        if transactions:
                            logger.info(f"Successfully extracted {len(transactions)} transactions from HTML format")
                            return transactions
                    except Exception as e:
                        logger.warning(f"Failed to parse as HTML: {e}")
        except Exception as e:
            logger.debug(f"Could not check for HTML format: {e}")
        
        try:
            # Try different engines for Excel files
            df = None
            engines = ['openpyxl', 'xlrd', None]
            
            for engine in engines:
                try:
                    df = pd.read_excel(excel_path, engine=engine)
                    logger.info(f"Successfully read Excel file with engine: {engine}")
                    break
                except Exception as e:
                    logger.debug(f"Engine {engine} failed: {e}")
                    continue
            
            if df is None:
                error_msg = "Could not read Excel file with any available engine (openpyxl, xlrd, default)"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            original_columns = df.columns.tolist()
            logger.info(f"Excel file loaded with columns: {original_columns}")
            
            # Clean column names for matching
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            logger.info(f"Cleaned column names: {df.columns.tolist()}")
            
            # Try to detect format and find columns
            date_col, desc_col, amount_col, debit_col, credit_col, debit_credit_flag_col = \
                ExcelParser._find_columns(df.columns.tolist(), original_columns)
            
            if not date_col:
                # If no format detected, provide detailed diagnostic
                col_list = ", ".join(original_columns)
                error_msg = f"Could not find DATE column in Excel file. Found columns: {col_list}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"Column mapping - Date:{date_col}, Description:{desc_col}, Amount:{amount_col}, "
                       f"Debit:{debit_col}, Credit:{credit_col}, DebitCreditFlag:{debit_credit_flag_col}")
            
            # Process each row
            skipped_rows = {'no_date': 0, 'invalid_date': 0, 'no_amount': 0, 'zero_amount': 0, 'no_desc': 0, 'other': 0}
            
            for index, row in df.iterrows():
                try:
                    # Get date
                    date_val = row[date_col] if date_col in row.index else None
                    date = ExcelParser._parse_excel_date(date_val)
                    if not date:
                        logger.debug(f"Row {index}: Skipping - could not parse date: {date_val}")
                        skipped_rows['invalid_date'] += 1
                        continue
                    
                    # Get description
                    if desc_col and desc_col in row.index and pd.notna(row[desc_col]):
                        description = str(row[desc_col]).strip()
                    else:
                        logger.debug(f"Row {index}: Skipping - no description")
                        skipped_rows['no_desc'] += 1
                        continue
                    
                    # Truncate description to 500 chars
                    description = description[:500]
                    
                    # Get amount and transaction type
                    amount = 0
                    transaction_type = 'DEBIT'
                    
                    # Strategy 1: Use debit/credit flag column if available (most reliable)
                    if debit_credit_flag_col and debit_credit_flag_col in row.index:
                        flag_value = str(row[debit_credit_flag_col]).strip().upper() if pd.notna(row[debit_credit_flag_col]) else ""
                        
                        # Get amount from amount column
                        if amount_col and amount_col in row.index and pd.notna(row[amount_col]):
                            try:
                                amount_val = float(str(row[amount_col]).replace(',', ''))
                                amount = abs(amount_val)
                            except (ValueError, TypeError):
                                logger.debug(f"Row {index}: Could not parse amount: {row[amount_col]}")
                                skipped_rows['no_amount'] += 1
                                continue
                        else:
                            logger.debug(f"Row {index}: No amount value found")
                            skipped_rows['no_amount'] += 1
                            continue
                        
                        # Determine type from flag
                        if flag_value in ['D', 'DEBIT', 'DR']:
                            transaction_type = 'DEBIT'
                        elif flag_value in ['C', 'CREDIT', 'CR']:
                            transaction_type = 'CREDIT'
                        else:
                            logger.debug(f"Row {index}: Unknown flag value: {flag_value}, defaulting to DEBIT")
                            transaction_type = 'DEBIT'
                    
                    # Strategy 2: Use separate debit/credit columns
                    elif debit_col and credit_col:
                        debit_val = row[debit_col] if debit_col in row.index and pd.notna(row[debit_col]) else None
                        credit_val = row[credit_col] if credit_col in row.index and pd.notna(row[credit_col]) else None
                        
                        try:
                            debit_amount = float(str(debit_val).replace(',', '')) if debit_val else 0
                            credit_amount = float(str(credit_val).replace(',', '')) if credit_val else 0
                        except (ValueError, TypeError):
                            logger.debug(f"Row {index}: Could not parse debit/credit amounts")
                            skipped_rows['no_amount'] += 1
                            continue
                        
                        if debit_amount > 0 and credit_amount == 0:
                            amount = debit_amount
                            transaction_type = 'DEBIT'
                        elif credit_amount > 0 and debit_amount == 0:
                            amount = credit_amount
                            transaction_type = 'CREDIT'
                        elif debit_amount > 0 and credit_amount > 0:
                            # Both non-zero, use non-zero preference
                            amount = max(debit_amount, credit_amount)
                            transaction_type = 'DEBIT' if debit_amount > credit_amount else 'CREDIT'
                        else:
                            logger.debug(f"Row {index}: No debit or credit amount")
                            skipped_rows['no_amount'] += 1
                            continue
                    
                    # Strategy 3: Use single amount column with minus sign detection
                    elif amount_col and amount_col in row.index:
                        if pd.notna(row[amount_col]):
                            amount_str = str(row[amount_col])
                            extracted_amount, extracted_type = PDFParser._extract_amount_and_type(amount_str)
                            if extracted_amount is not None:
                                amount = extracted_amount
                                transaction_type = extracted_type
                            else:
                                logger.debug(f"Row {index}: Could not extract amount from: {amount_str}")
                                skipped_rows['no_amount'] += 1
                                continue
                        else:
                            logger.debug(f"Row {index}: Amount column is empty")
                            skipped_rows['no_amount'] += 1
                            continue
                    else:
                        logger.debug(f"Row {index}: No amount column found")
                        skipped_rows['no_amount'] += 1
                        continue
                    
                    # Check for zero amount
                    if amount <= 0:
                        logger.debug(f"Row {index}: Skipping zero/negative amount: {amount}")
                        skipped_rows['zero_amount'] += 1
                        continue
                    
                    # Add transaction
                    transactions.append({
                        'date': date,
                        'description': description,
                        'amount': amount,
                        'transaction_type': transaction_type
                    })
                    logger.debug(f"Row {index}: ✓ Extracted | {date} | {description[:40]}... | ₹{amount} ({transaction_type})")
                    
                except Exception as e:
                    logger.debug(f"Row {index}: Unexpected error - {e}")
                    skipped_rows['other'] += 1
                    continue
            
            logger.info(f"Excel parsing complete: {len(transactions)} transactions extracted")
            logger.info(f"Skipped rows - no_date: {skipped_rows['no_date']}, invalid_date: {skipped_rows['invalid_date']}, "
                       f"no_amount: {skipped_rows['no_amount']}, zero_amount: {skipped_rows['zero_amount']}, "
                       f"no_desc: {skipped_rows['no_desc']}, other: {skipped_rows['other']}")
            
            if not transactions:
                col_list = ", ".join(original_columns)
                error_msg = f"No transactions could be extracted from Excel file. Columns found: {col_list}. " \
                           f"Skipped: {sum(skipped_rows.values())} rows total."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _find_columns(cleaned_cols, original_cols):
        """Find relevant columns using multiple strategies
        
        Returns: (date_col, desc_col, amount_col, debit_col, credit_col, debit_credit_flag_col)
        """
        date_col = None
        desc_col = None
        amount_col = None
        debit_col = None
        credit_col = None
        debit_credit_flag_col = None
        
        logger.debug(f"Finding columns from: {cleaned_cols}")
        
        # Strategy 1: Exact match with bank format registry
        for bank_name, format_spec in ExcelParser.BANK_FORMATS.items():
            # Try date patterns
            if 'date_patterns' in format_spec and not date_col:
                for pattern in format_spec['date_patterns']:
                    if pattern in cleaned_cols:
                        date_col = pattern
                        logger.info(f"Bank format {bank_name}: Found date column via exact match: {pattern}")
                        break
            
            # Try description patterns
            if 'description_patterns' in format_spec and not desc_col:
                for pattern in format_spec['description_patterns']:
                    if pattern in cleaned_cols:
                        desc_col = pattern
                        logger.info(f"Bank format {bank_name}: Found description column via exact match: {pattern}")
                        break
            
            # Try amount patterns
            if 'amount_patterns' in format_spec and not amount_col:
                for pattern in format_spec['amount_patterns']:
                    if pattern in cleaned_cols:
                        amount_col = pattern
                        logger.info(f"Bank format {bank_name}: Found amount column via exact match: {pattern}")
                        break
            
            # Try debit/credit flag
            if 'debit_credit_flag' in format_spec and not debit_credit_flag_col:
                for pattern in format_spec['debit_credit_flag']:
                    if pattern in cleaned_cols:
                        debit_credit_flag_col = pattern
                        logger.info(f"Bank format {bank_name}: Found debit/credit flag column: {pattern}")
                        break
            
            # Try separate debit/credit columns
            if 'debit_patterns' in format_spec and not debit_col:
                for pattern in format_spec['debit_patterns']:
                    if pattern in cleaned_cols:
                        debit_col = pattern
                        logger.info(f"Bank format {bank_name}: Found debit column: {pattern}")
                        break
            
            if 'credit_patterns' in format_spec and not credit_col:
                for pattern in format_spec['credit_patterns']:
                    if pattern in cleaned_cols:
                        credit_col = pattern
                        logger.info(f"Bank format {bank_name}: Found credit column: {pattern}")
                        break
        
        # Strategy 2: Fallback to keyword matching (current logic)
        if not date_col:
            for col in cleaned_cols:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['date', 'transaction', 'tran_date']):
                    date_col = col
                    logger.info(f"Found date column via keyword match: {col}")
                    break
        
        if not desc_col:
            for col in cleaned_cols:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['description', 'narration', 'particulars', 'details', 'memo']):
                    desc_col = col
                    logger.info(f"Found description column via keyword match: {col}")
                    break
        
        if not amount_col:
            for col in cleaned_cols:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['amount', 'value', 'debit', 'credit', 'withdrawal', 'deposit']):
                    amount_col = col
                    logger.info(f"Found amount column via keyword match: {col}")
                    break
        
        return date_col, desc_col, amount_col, debit_col, credit_col, debit_credit_flag_col
    
    @staticmethod
    def _parse_excel_date(date_val):
        """Parse date from Excel value"""
        try:
            if pd.isna(date_val):
                return None
            
            if isinstance(date_val, (datetime, pd.Timestamp)):
                return date_val.date()
            
            date_str = str(date_val)
            return PDFParser._parse_date(date_str)
            
        except Exception:
            return None

class CSVParser:
    """Parse transactions from CSV bank statements"""
    
    @staticmethod
    def extract_transactions(csv_path):
        """Extract transactions from CSV file"""
        if not PANDAS_AVAILABLE:
            logger.error("CSV parsing not available. Install pandas.")
            raise ImportError("pandas not installed. CSV support requires: pip install pandas")
        
        logger.info(f"Starting to parse CSV file: {csv_path}")
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            df = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    used_encoding = encoding
                    logger.info(f"CSV file loaded with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    logger.debug(f"Encoding {encoding} failed")
                    continue
            
            if df is None:
                error_msg = "Could not read CSV file with any supported encoding (utf-8, latin-1, iso-8859-1, cp1252)"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            original_columns = df.columns.tolist()
            logger.info(f"CSV file loaded with columns: {original_columns}")
            
            # Clean column names for matching
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Use same parsing logic as Excel (which now has improved error handling)
            return ExcelParser.extract_transactions(csv_path)
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}", exc_info=True)
            raise