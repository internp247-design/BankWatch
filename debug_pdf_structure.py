#!/usr/bin/env python3
"""Debug script to analyze PDF structure and identify parsing issues"""

import re
import sys
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed")
    sys.exit(1)

def debug_pdf(pdf_path):
    """Analyze PDF structure and test regex patterns"""
    
    print(f"Opening: {pdf_path}\n")
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )
    
    print("=" * 80)
    print("FULL PDF TEXT (first 3000 chars):")
    print("=" * 80)
    print(full_text[:3000])
    print("\n" + "=" * 80)
    
    # Test 1: Current strict pattern
    print("\n[TEST 1] CURRENT STRICT PATTERN:")
    pattern1 = re.compile(
        r'(\d{2}-\d{2}-\d{2})\s+'
        r'(.+?)\s+-\s+-\s+'
        r'([\d,]+\.\d{2})\s+'
        r'([\d,]+\.\d{2})'
    )
    matches1 = list(pattern1.finditer(full_text))
    print(f"Matches: {len(matches1)}")
    if matches1:
        print("First 3 matches:")
        for i, m in enumerate(matches1[:3]):
            print(f"  {i+1}. {m.group(0)}")
    
    # Test 2: Flexible pattern (various date formats)
    print("\n[TEST 2] FLEXIBLE DATE PATTERN:")
    pattern2 = re.compile(
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+'
        r'(.+?)\s+'
        r'([\d,]+\.?\d*)\s+'
        r'([\d,]+\.?\d*)'
    )
    matches2 = list(pattern2.finditer(full_text))
    print(f"Matches: {len(matches2)}")
    if matches2:
        print("First 5 matches:")
        for i, m in enumerate(matches2[:5]):
            print(f"  {i+1}. {m.group(0)}")
    
    # Test 3: Look for lines with transaction-like content
    print("\n[TEST 3] LINES WITH NUMBERS (potential transaction lines):")
    lines = full_text.split('\n')
    transaction_like_lines = []
    for line in lines:
        # Check if line has date-like pattern and amounts
        if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line) and re.search(r'[\d,]+\.?\d+', line):
            transaction_like_lines.append(line)
    
    print(f"Found {len(transaction_like_lines)} transaction-like lines")
    print("First 10 lines:")
    for i, line in enumerate(transaction_like_lines[:10]):
        print(f"  {i+1}. {repr(line)}")
    
    # Test 4: Look for specific keywords
    print("\n[TEST 4] KEYWORD SEARCH:")
    keywords = ['/DR/', '/CR/', 'UPI', 'IMPS', 'NEFT', 'INTEREST', 'SALARY', 'DEPOSIT', 'CHQ']
    for kw in keywords:
        count = full_text.count(kw)
        if count > 0:
            print(f"  '{kw}': {count} occurrences")
            # Show first occurrence
            idx = full_text.find(kw)
            start = max(0, idx - 100)
            end = min(len(full_text), idx + 150)
            print(f"    Context: ...{repr(full_text[start:end])}...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_pdf_structure.py <pdf_file>")
        print("\nExample:")
        print("  python debug_pdf_structure.py media/statements/my_statement.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    debug_pdf(pdf_path)
