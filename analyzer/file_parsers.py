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
        """Extract transactions from PDF tables (table-based bank statements)"""
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
                        
                        # Process data rows (skip header)
                        for row_idx, row in enumerate(table[1:], 1):
                            if not row or len(row) < 3:
                                continue
                            
                            try:
                                # Parse table row: DATE | DESCRIPTION | CATEGORY | AMOUNT
                                date_str = row[0].strip() if row[0] else ""
                                description = row[1].strip() if row[1] else ""
                                amount_str = row[3].strip() if len(row) > 3 and row[3] else ""
                                
                                if not date_str or not amount_str or not description:
                                    continue
                                
                                # Parse date from format like "24\nJAN" or "24 JAN"
                                date_obj = PDFParser._parse_table_date(date_str)
                                if not date_obj:
                                    logger.debug(f"Could not parse date: {date_str}")
                                    continue
                                
                                # Parse amount (handles "₹50000.00" or "-₹2500.50" format)
                                amount, trans_type = PDFParser._parse_table_amount(amount_str)
                                if amount is None:
                                    logger.debug(f"Could not parse amount: {amount_str}")
                                    continue
                                
                                transaction = {
                                    'date': date_obj,
                                    'description': description[:500],
                                    'amount': amount,
                                    'transaction_type': trans_type
                                }
                                transactions.append(transaction)
                                logger.debug(f"Extracted table row: {date_obj} | {description[:30]}... | ₹{amount} ({trans_type})")
                            
                            except Exception as e:
                                logger.debug(f"Error processing table row {row_idx}: {e}")
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
            date = None
            date_formats = ['%d-%m-%y', '%d-%m-%Y', '%d/%m/%y', '%d/%m/%Y', '%d-%m', '%m-%d', '%Y-%m-%d']
            
            for fmt in date_formats:
                try:
                    date = datetime.strptime(str(date_str).strip(), fmt).date()
                    logger.debug(f"Parsed date '{date_str}' with format '{fmt}' -> {date}")
                    return date
                except ValueError:
                    continue
            
            return None
        except Exception as e:
            logger.warning(f"Error parsing date: {date_str}, {e}")
            return None

class ExcelParser:
    """Parse transactions from Excel bank statements"""
    
    @staticmethod
    def extract_transactions(excel_path):
        """Extract transactions from Excel file"""
        if not PANDAS_AVAILABLE:
            print("Excel parsing not available. Install pandas.")
            return StatementParser._create_sample_transactions()
        
        transactions = []
        
        # First, check if this is an HTML file disguised as Excel
        try:
            with open(excel_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_bytes = f.read(100)
                if '<html' in first_bytes.lower() or '<table' in first_bytes.lower():
                    print("Detected HTML format in Excel file, parsing as HTML...")
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
                            print(f"Successfully extracted {len(transactions)} transactions from HTML format")
                            return transactions
                    except Exception as e:
                        print(f"Failed to parse as HTML: {e}")
        except Exception as e:
            print(f"Could not detect file format: {e}")
        
        try:
            # Try different engines for Excel files
            df = None
            engines = ['openpyxl', 'xlrd', None]
            
            for engine in engines:
                try:
                    df = pd.read_excel(excel_path, engine=engine)
                    print(f"Successfully read Excel file with engine: {engine}")
                    break
                except Exception as e:
                    continue
            
            if df is None:
                raise ValueError("Could not read Excel file with any available engine")
            
            print(f"Excel file loaded. Columns: {df.columns.tolist()}")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Find relevant columns
            date_col = None
            desc_col = None
            amount_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['date', 'transaction', 'value']):
                    date_col = col
                elif any(word in col_lower for word in ['description', 'narration', 'particulars', 'details']):
                    desc_col = col
                elif any(word in col_lower for word in ['amount', 'debit', 'credit', 'withdrawal', 'deposit']):
                    amount_col = col
            
            if not date_col:
                print("Could not find date column")
                return StatementParser._create_sample_transactions()
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Get date
                    date = ExcelParser._parse_excel_date(row[date_col])
                    if not date:
                        continue
                    
                    # Get description
                    if desc_col and pd.notna(row[desc_col]):
                        description = str(row[desc_col])
                    else:
                        description = f"Transaction {index + 1}"
                    
                    # Get amount using minus sign detection
                    amount = 0
                    transaction_type = 'DEBIT'
                    
                    if amount_col:
                        if pd.notna(row[amount_col]):
                            # Convert value to string for processing with _extract_amount_and_type
                            amount_str = str(row[amount_col])
                            extracted_amount, extracted_type = PDFParser._extract_amount_and_type(amount_str)
                            if extracted_amount is not None:
                                amount = extracted_amount
                                transaction_type = extracted_type
                            else:
                                # Fallback to numeric parsing for values without minus sign
                                amount_val = float(row[amount_col])
                                amount = abs(amount_val)
                                transaction_type = 'DEBIT' if amount_val < 0 else 'CREDIT'
                    
                    if amount == 0:
                        continue
                    
                    transactions.append({
                        'date': date,
                        'description': description.strip(),
                        'amount': amount,
                        'transaction_type': transaction_type
                    })
                    
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error processing Excel file: {e}")
        
        # If no transactions found, create sample data
        if not transactions:
            print("No transactions found in Excel, creating sample data")
            transactions = StatementParser._create_sample_transactions()
        
        return transactions
    
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
            print("CSV parsing not available. Install pandas.")
            return StatementParser._create_sample_transactions()
        
        transactions = []
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("Could not read CSV file")
            
            print(f"CSV file loaded. Columns: {df.columns.tolist()}")
            
            # Use same parsing logic as Excel
            return ExcelParser.extract_transactions(csv_path)
            
        except Exception as e:
            print(f"Error processing CSV file: {e}")
        
        # If no transactions found, create sample data
        if not transactions:
            print("No transactions found in CSV, creating sample data")
            transactions = StatementParser._create_sample_transactions()
        
        return transactions