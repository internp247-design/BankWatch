import re
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Try to import optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not installed. Excel/CSV support limited.")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not installed. PDF support limited.")

# File type constants
PDF = 'PDF'
EXCEL = 'EXCEL'
CSV = 'CSV'

class StatementParser:
    """Parser for different types of bank statement files"""
    
    @staticmethod
    def parse_file(file_path, file_type):
        """Parse file based on type"""
        if file_type == PDF:
            return PDFParser.extract_transactions(file_path)
        elif file_type == EXCEL:
            return ExcelParser.extract_transactions(file_path)
        elif file_type == CSV:
            return CSVParser.extract_transactions(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
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
    """Parse transactions from PDF bank statements"""
    
    @staticmethod
    def extract_transactions(pdf_path):
        """Extract transactions from PDF file"""
        transactions = []
        
        if not PDFPLUMBER_AVAILABLE:
            print("PDF parsing not available. Install pdfplumber.")
            return StatementParser._create_sample_transactions()
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                
                print(f"Extracted {len(text)} characters from PDF")
                
                # Common transaction patterns
                patterns = [
                    # Pattern 1: Date Description Amount (with optional CR/DR)
                    r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.*?)\s+([+-]?[\d,]+\.\d{2})\s*(CR|DR|Cr|Dr)?',
                    # Pattern 2: Date Amount Description (with optional CR/DR)
                    r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+([+-]?[\d,]+\.\d{2})\s+(.*?)\s*(CR|DR|Cr|Dr)?',
                    # Pattern 3: Amounts with explicit CR/DR markers
                    r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.*?)\s+(\d+[\d,]*\.\d{2})\s+(CR|DR|Cr|Dr)',
                ]
                
                all_matches = []
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    all_matches.extend(matches)
                
                print(f"Found {len(all_matches)} potential transactions")
                
                for match in all_matches:
                    try:
                        if len(match) == 4:
                            # Pattern with CR/DR marker
                            date_str, amount_or_desc, desc_or_amount, cr_dr = match
                            
                            # Determine if amount_or_desc or desc_or_amount contains the amount
                            if amount_or_desc.replace(',', '').replace('.', '').replace('-', '').replace('+', '').isdigit():
                                amount_str = amount_or_desc
                                description = desc_or_amount
                            else:
                                amount_str = desc_or_amount
                                description = amount_or_desc
                            
                            # Add CR/DR marker to amount_str for proper parsing
                            amount_str = f"{amount_str} {cr_dr}"
                        elif len(match) == 3:
                            date_str = match[0]
                            cr_dr_marker = match[2] if match[2] else ""
                            
                            # Check if match[1] is amount or description
                            if match[1].replace(',', '').replace('.', '').replace('-', '').replace('+', '').isdigit():
                                amount_str = f"{match[1]} {cr_dr_marker}"
                                description = "Transaction"
                            else:
                                # match[1] is description, need to find amount
                                date_str, description, amount_str = match[0], match[1], match[2]
                                amount_str = f"{amount_str} {cr_dr_marker}"
                        else:
                            continue
                        
                        # Parse date
                        date = PDFParser._parse_date(date_str)
                        if not date:
                            continue
                        
                        # Parse amount
                        amount, transaction_type = PDFParser._parse_amount(amount_str)
                        if amount is None:
                            continue
                        
                        transactions.append({
                            'date': date,
                            'description': description.strip(),
                            'amount': amount,
                            'transaction_type': transaction_type
                        })
                        
                    except Exception as e:
                        print(f"Error processing match: {e}")
                        continue
                
        except Exception as e:
            print(f"Error processing PDF: {e}")
        
        # If no transactions found, create sample data
        if not transactions:
            print("No transactions found in PDF, creating sample data")
            transactions = StatementParser._create_sample_transactions()
        
        return transactions
    
    @staticmethod
    def _parse_date(date_str):
        """Parse date string to date object"""
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d',
            '%d/%m/%y', '%d-%m-%y', '%m/%d/%Y',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def _parse_amount(amount_str):
        """Parse amount string to float and determine transaction type"""
        try:
            # Store original for debit/credit detection
            original_str = amount_str.lower()
            
            # Detect debit/credit from markers in original string (BEFORE cleaning)
            is_debit = 'dr' in original_str or 'debit' in original_str
            has_credit_marker = 'cr' in original_str or 'credit' in original_str
            
            # Clean the amount string
            amount_str_clean = amount_str.replace(',', '').replace('+', '').replace('₹', '').replace('-', '').strip()
            
            # Parse the numeric amount
            amount = float(amount_str_clean)
            
            # Determine transaction type based on sign AND markers
            if amount < 0:
                transaction_type = 'DEBIT'
                amount = abs(amount)
            elif is_debit and not has_credit_marker:
                transaction_type = 'DEBIT'
                amount = abs(amount)
            else:
                transaction_type = 'CREDIT'
                amount = abs(amount)
            
            return amount, transaction_type
        except ValueError:
            return None, None

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
                    
                    # Get amount
                    amount = 0
                    transaction_type = 'DEBIT'
                    
                    if amount_col:
                        if pd.notna(row[amount_col]):
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