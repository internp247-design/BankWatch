"""
Diagnostic script to test PDF parsing and identify issues.
Usage: python manage.py shell < scripts/test_pdf_parsing.py
Or:    python scripts/test_pdf_parsing.py <pdf_file_path>
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n" + "="*60)
    print("CHECKING DEPENDENCIES")
    print("="*60)
    
    dependencies = {
        'pdfplumber': 'PDF text extraction',
        'fitz (PyMuPDF)': 'Scanned PDF OCR support',
        'pytesseract': 'Tesseract OCR wrapper',
        'PIL (Pillow)': 'Image processing',
        'pandas': 'Excel/CSV parsing'
    }
    
    for dep_name, purpose in dependencies.items():
        try:
            if dep_name == 'fitz (PyMuPDF)':
                import fitz
            elif dep_name == 'PIL (Pillow)':
                from PIL import Image
            elif dep_name.lower().replace('_', ' ') == 'pytesseract':
                import pytesseract
            else:
                __import__(dep_name.lower().replace(' ', '_').replace('(', '').replace(')', ''))
            
            print(f"✅ {dep_name:<20} - {purpose}")
        except ImportError as e:
            print(f"❌ {dep_name:<20} - {purpose}")
            print(f"   Error: {e}")
    
    # Check Tesseract installation
    print("\nChecking Tesseract OCR installation...")
    try:
        import pytesseract
        result = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract found: {result}")
    except Exception as e:
        print(f"❌ Tesseract not found or not accessible: {e}")
        print("   Install from: https://github.com/UB-Mannheim/tesseract/wiki")


def analyze_pdf(pdf_path):
    """Analyze a PDF file to understand its structure"""
    print("\n" + "="*60)
    print(f"ANALYZING PDF: {os.path.basename(pdf_path)}")
    print("="*60)
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    try:
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"\nFile: {os.path.basename(pdf_path)}")
            print(f"Total pages: {len(pdf.pages)}")
            print(f"File size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
            
            # Check first page for embedded text
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            print(f"\nEmbedded Text Detection:")
            print(f"  First page has embedded text: {bool(text and text.strip())}")
            
            if text and text.strip():
                print(f"  Text length: {len(text)} characters")
                print(f"  First 200 chars:\n{text[:200]}")
            else:
                print("  ⚠️  No embedded text found - this appears to be a scanned PDF")
            
            # Extract all text
            print(f"\nExtracting text from all pages...")
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            print(f"  Total extracted text: {len(full_text)} characters")
            
            # Detect bank format
            print(f"\nDetecting bank format...")
            text_lower = full_text.lower()
            banks = {
                'SBI': 'State Bank of India',
                'ICICI': 'ICICI Bank',
                'HDFC': 'HDFC Bank',
                'AXIS': 'Axis Bank',
                'CANARA': 'Canara Bank'
            }
            
            detected_bank = None
            for bank_code, bank_name in banks.items():
                if bank_code.lower() in text_lower:
                    detected_bank = bank_code
                    print(f"  ✅ Detected: {bank_name} ({bank_code})")
                    break
            
            if not detected_bank:
                print(f"  ⓘ Bank format: Unknown (will use generic parser)")
            
            # Look for transaction patterns
            print(f"\nSearching for transaction patterns...")
            import re
            
            # SBI-style patterns
            debit_pattern = r'(\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+-\s+-\s+([\d,]+\.?\d+)'
            credit_pattern = r'(\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+-\s+([\d,]+\.?\d+)\s+-'
            
            debit_matches = len(re.findall(debit_pattern, full_text))
            credit_matches = len(re.findall(credit_pattern, full_text))
            
            print(f"  SBI-style DEBIT patterns found: {debit_matches}")
            print(f"  SBI-style CREDIT patterns found: {credit_matches}")
            print(f"  Total potential transactions: {debit_matches + credit_matches}")
            
            # Show sample transaction
            if debit_matches > 0:
                match = re.search(debit_pattern, full_text)
                if match:
                    print(f"\n  Sample DEBIT transaction found:")
                    print(f"    {match.group()[:100]}...")
            
            if credit_matches > 0:
                match = re.search(credit_pattern, full_text)
                if match:
                    print(f"\n  Sample CREDIT transaction found:")
                    print(f"    {match.group()[:100]}...")
        
        # Now test actual parsing
        print("\n" + "-"*60)
        print("TESTING ACTUAL PARSING")
        print("-"*60)
        
        from analyzer.file_parsers import PDFParser
        transactions = PDFParser.extract_transactions(pdf_path)
        
        print(f"\n✅ Parsing completed!")
        print(f"Transactions extracted: {len(transactions)}")
        
        if transactions:
            print(f"\nFirst 3 transactions:")
            for i, trans in enumerate(transactions[:3], 1):
                print(f"\n  {i}. Date: {trans['date']}")
                print(f"     Description: {trans['description'][:50]}...")
                print(f"     Amount: {trans['amount']}")
                print(f"     Type: {trans['transaction_type']}")
        else:
            print(f"\n❌ No transactions extracted!")
            print(f"Check the log output above for parsing errors")
    
    except Exception as e:
        print(f"\n❌ Error analyzing PDF: {e}")
        import traceback
        traceback.print_exc()


def test_all_pdfs_in_directory(directory):
    """Test all PDF files in a directory"""
    pdf_files = list(Path(directory).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return
    
    print(f"\nFound {len(pdf_files)} PDF files to test")
    
    for pdf_file in pdf_files:
        analyze_pdf(str(pdf_file))
        print("\n" + "="*60 + "\n")


def main():
    print("\n" + "🔍 "*30)
    print("PDF PARSING DIAGNOSTIC TOOL")
    print("🔍 "*30)
    
    # Check dependencies first
    check_dependencies()
    
    # If PDF path provided as argument, analyze it
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if os.path.isdir(pdf_path):
            test_all_pdfs_in_directory(pdf_path)
        else:
            analyze_pdf(pdf_path)
    else:
        print("\n" + "="*60)
        print("Usage:")
        print("  In Django shell: python manage.py shell < scripts/test_pdf_parsing.py")
        print("  Direct: python scripts/test_pdf_parsing.py <pdf_file_or_directory>")
        print("="*60)
        print("\nTesting sample PDFs from media/statements/...")
        test_all_pdfs_in_directory("media/statements")


if __name__ == '__main__':
    main()
