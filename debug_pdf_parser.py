#!/usr/bin/env python3
"""
Enhanced PDF Parser with detailed debugging
Drop-in replacement for testing
"""

import re
from datetime import datetime
import os

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

class PDFParserDebug:
    """Parse transactions from SBI-style PDF bank statements with debug output"""

    @staticmethod
    def extract_transactions(pdf_path, debug=True):
        """Extract transactions with detailed debugging"""
        transactions = []

        if not PDFPLUMBER_AVAILABLE:
            if debug:
                print("[ERROR] pdfplumber not available")
            return []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if debug:
                    print(f"[PDF] Opened: {pdf_path}")
                    print(f"[PDF] Pages: {len(pdf.pages)}")
                
                full_text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
                
                if debug:
                    print(f"[PDF] Total text length: {len(full_text)} characters")
                    print(f"[PDF] First 500 chars:\n{full_text[:500]}\n")

            # SBI Transaction Line Pattern - More flexible to handle variations
            pattern = re.compile(
                r'(\d{2}-\d{2}-\d{2})\s+'           # Date: DD-MM-YY
                r'(.+?)\s+' +                       # Description
                r'(?:[-\s]+)?'                      # Optional dashes/spaces
                r'([\d,]+\.?\d*)'                   # Amount
                r'(?:\s+[-\s]+\s+)?'                # Optional separator
                r'([\d,]+\.?\d*)'                   # Balance
                , re.DOTALL
            )

            all_matches = list(pattern.finditer(full_text))
            if debug:
                print(f"[REGEX] Matched {len(all_matches)} potential transactions")

            for idx, match in enumerate(all_matches):
                try:
                    date_str, description, amount_str, balance_str = match.groups()

                    if debug and idx < 3:
                        print(f"[MATCH {idx+1}]")
                        print(f"  Raw groups: {match.groups()}")

                    # Parse date
                    try:
                        date = datetime.strptime(date_str, '%d-%m-%y').date()
                    except ValueError as e:
                        if debug:
                            print(f"  ❌ Date parse failed: {date_str} - {e}")
                        continue

                    description = description.strip()
                    if not description:
                        if debug:
                            print(f"  ❌ Empty description")
                        continue

                    # Detect transaction type
                    desc_upper = description.upper()
                    
                    if '/DR/' in description:
                        transaction_type = 'DEBIT'
                    elif '/CR/' in description:
                        transaction_type = 'CREDIT'
                    elif any(keyword in desc_upper for keyword in ['INTEREST CREDIT', 'SALARY', 'TRANSFER CR', 'DEPOSIT', 'REFUND', 'CREDIT']):
                        transaction_type = 'CREDIT'
                    elif any(keyword in desc_upper for keyword in ['IMPS', 'NEFT', 'RTGS', 'UPI', 'CHQ', 'DEBIT', 'PAYMENT', 'WITHDRAWAL']):
                        transaction_type = 'DEBIT'
                    else:
                        transaction_type = 'DEBIT'

                    # Parse amount
                    try:
                        amount = float(amount_str.replace(',', ''))
                        if amount <= 0:
                            if debug and idx < 3:
                                print(f"  ❌ Amount <= 0: {amount}")
                            continue
                    except ValueError as e:
                        if debug and idx < 3:
                            print(f"  ❌ Amount parse failed: {amount_str} - {e}")
                        continue

                    if debug and idx < 3:
                        print(f"  ✅ Date: {date}, Type: {transaction_type}, Amount: {amount}")
                        print(f"     Desc: {description[:60]}")

                    transactions.append({
                        'date': date,
                        'description': description,
                        'amount': amount,
                        'transaction_type': transaction_type
                    })

                except Exception as e:
                    if debug and idx < 3:
                        print(f"  ❌ Error processing: {e}")
                    continue

            if debug:
                print(f"\n[RESULT] Successfully extracted {len(transactions)} transactions")
                if transactions:
                    debits = sum(1 for t in transactions if t['transaction_type'] == 'DEBIT')
                    credits = sum(1 for t in transactions if t['transaction_type'] == 'CREDIT')
                    print(f"  Debits: {debits}, Credits: {credits}")

        except Exception as e:
            if debug:
                print(f"[ERROR] PDF parsing failed: {e}")
            import traceback
            traceback.print_exc()

        return transactions


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python debug_pdf_parser.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    print(f"Analyzing: {pdf_path}\n")
    transactions = PDFParserDebug.extract_transactions(pdf_path, debug=True)
    
    print("\n" + "="*60)
    print("PARSED TRANSACTIONS:")
    print("="*60)
    for t in transactions[:10]:  # Show first 10
        print(f"{t['date']} | {t['transaction_type']:6} | ₹{t['amount']:10.2f} | {t['description'][:40]}")
