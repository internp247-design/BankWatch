"""
Test cases and usage examples for UPI parser
"""

from analyzer.upi_parser import (
    UPIParser, TableFormatUPIParser, PlainTextUPIParser
)


# ============================================================================
# Test Case 1: Standard UPI Description with Time
# ============================================================================
def test_standard_upi_with_time():
    """Test parsing standard UPI descriptions that start with UPI and end with time"""
    
    descriptions = [
        "UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VALUATION//160234",
        "UPI/CR/234567891011/MERCHANT/ICIC/**ABC123@OKSBI/REF//143056",
        "UPI/IMPS/301234567/JOHN.DOE/HDFC/**XYZ@OKHDFCBANK/PAYMENT//152030",
    ]
    
    for desc in descriptions:
        print(f"\nParsing: {desc}")
        
        # Check if it's a UPI description
        is_upi = UPIParser.is_upi_description(desc)
        print(f"  Is UPI: {is_upi}")
        
        # Extract timestamp
        time = UPIParser.extract_time(desc)
        print(f"  Time: {time}")
        
        # Parse fields
        fields = UPIParser.parse_upi_fields(desc)
        print(f"  Type: {fields['transaction_type']}")
        print(f"  Name: {fields['sender_receiver']}")
        print(f"  UPI ID: {fields['upi_id']}")
        print(f"  Remarks: {fields['remarks']}")
        
        # Extract RRN
        rrn = UPIParser.extract_rrn(desc)
        print(f"  RRN: {rrn}")


# ============================================================================
# Test Case 2: Various Time Formats
# ============================================================================
def test_time_format_variants():
    """Test different time format variants"""
    
    test_cases = [
        ("UPI/DR/123/NAME/BANK/ID//160234", "Standard HHMMSS (no colons)"),
        ("UPI/DR/123/NAME/BANK/ID//16:02:34", "ISO HH:MM:SS"),
        ("UPI/DR/123/NAME/BANK/ID//1602", "Short HHMM"),
        ("UPI/DR/123/NAME/BANK/ID//16:02", "Short HH:MM"),
        ("UPI/DR/123/NAME/BANK/ID/ T16:02:34", "ISO with T prefix"),
    ]
    
    for desc, format_desc in test_cases:
        time = UPIParser.extract_time(desc)
        print(f"{format_desc:30} -> {time}")


# ============================================================================
# Test Case 3: Table Format (Multiple Descriptions)
# ============================================================================
def test_table_format():
    """Test parsing descriptions from table-format statements"""
    
    # Simulating a table cell content
    cell_content = "UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VALUATION//160234"
    
    print(f"\nTable cell content: {cell_content}")
    results = TableFormatUPIParser.parse_table_cell(cell_content)
    
    for result in results:
        print(f"  Transaction Type: {result['transaction_type']}")
        print(f"  Reference: {result['reference']}")
        print(f"  Name: {result['sender_receiver']}")


# ============================================================================
# Test Case 4: Plain Text Format (Multiple Lines)
# ============================================================================
def test_plain_text_format():
    """Test parsing descriptions from plain text statements"""
    
    text = """
    Date    Description    Amount
    10-DEC  UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VALUATION//160234    500.00
    11-DEC  UPI/CR/234567891011/MERCHANT/ICIC/**ABC123@OKSBI/REF//143056    1000.00
    """
    
    print(f"\nPlain text extraction:")
    results = PlainTextUPIParser.extract_upi_descriptions(text)
    
    for i, result in enumerate(results, 1):
        print(f"\n  Transaction {i}:")
        print(f"    Type: {result['transaction_type']}")
        print(f"    Name: {result['sender_receiver']}")
        print(f"    Timestamp: {result['timestamp']}")


# ============================================================================
# Test Case 5: Wrapped Descriptions Across Lines
# ============================================================================
def test_wrapped_descriptions():
    """Test parsing descriptions that wrap across multiple lines"""
    
    lines = [
        "10-DEC",
        "UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707",
        "@OKSBI/VALUATION//160234",
        "11-DEC",
        "UPI/CR/234567891011/MERCHANT/ICIC",
        "**ABC123@OKSBI/REF//143056"
    ]
    
    print(f"\nWrapped descriptions:")
    results = PlainTextUPIParser.extract_wrapped_descriptions(lines)
    
    for i, result in enumerate(results, 1):
        print(f"\n  Transaction {i}:")
        print(f"    Timestamp: {result['timestamp']}")
        print(f"    Name: {result['sender_receiver']}")
        print(f"    Full fields: {result['raw_fields']}")


# ============================================================================
# Test Case 6: Multiple UPI Transactions on One Line
# ============================================================================
def test_multiple_upi_on_one_line():
    """Test parsing multiple UPI transactions on a single line"""
    
    text = "UPI/DR/123/NAME1/BANK/ID1//160234 UPI/CR/456/NAME2/BANK/ID2//143056"
    
    print(f"\nMultiple UPI on one line:")
    print(f"  Input: {text}")
    
    transactions = UPIParser.split_multi_upi_transactions(text)
    print(f"  Split into {len(transactions)} transactions:")
    
    for i, txn in enumerate(transactions, 1):
        time = UPIParser.extract_time(txn)
        fields = UPIParser.parse_upi_fields(txn)
        print(f"\n  Transaction {i}:")
        print(f"    Type: {fields['transaction_type']}")
        print(f"    Time: {time}")


# ============================================================================
# Test Case 7: Format Detection
# ============================================================================
def test_format_detection():
    """Test automatic format variant detection"""
    
    test_cases = [
        "UPI/DR/123/NAME/BANK/ID/REMARKS/160234",
        "UPI DR 123",
        "UPI/123/NAME",
        "UNKNOWN FORMAT",
    ]
    
    print(f"\nFormat detection:")
    for desc in test_cases:
        fmt = UPIParser.detect_format_variant(desc)
        print(f"  '{desc[:40]:40}' -> {fmt}")


# ============================================================================
# Test Case 8: Description Normalization
# ============================================================================
def test_normalization():
    """Test description normalization"""
    
    test_cases = [
        "UPI/DR/123/NAME/BANK//ID//160234",
        "UPI / DR / 123 / NAME / BANK / ID // 160234",
        "UPI/DR/123/NAME/BANK/ID  extra  spaces//160234",
    ]
    
    print(f"\nNormalization (without timestamp):")
    for desc in test_cases:
        normalized = UPIParser.normalize_description(desc, keep_timestamp=False)
        print(f"  {normalized}")
    
    print(f"\nNormalization (with timestamp):")
    for desc in test_cases:
        normalized = UPIParser.normalize_description(desc, keep_timestamp=True)
        print(f"  {normalized}")


# ============================================================================
# Test Case 9: UPI ID and RRN Extraction
# ============================================================================
def test_upi_id_and_rrn_extraction():
    """Test extraction of UPI ID and RRN from descriptions"""
    
    descriptions = [
        "UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VALUATION//160234",
        "UPI/CR/234567891011/MERCHANT/**ABC123@OKHDFCBANK/REF//143056",
        "UPI/IMPS/301234567/JOHN.DOE/**XYZ@OKSBI//152030",
    ]
    
    print(f"\nUPI ID and RRN extraction:")
    for desc in descriptions:
        upi_id = UPIParser.extract_upi_id(desc)
        rrn = UPIParser.extract_rrn(desc)
        name = UPIParser.extract_name(desc)
        print(f"\n  {desc[:50]}...")
        print(f"    UPI ID: {upi_id}")
        print(f"    RRN: {rrn}")
        print(f"    Name: {name}")


# ============================================================================
# Test Case 10: Edge Cases
# ============================================================================
def test_edge_cases():
    """Test edge cases and error handling"""
    
    test_cases = [
        ("", "Empty string"),
        (None, "None"),
        ("UPI/", "Incomplete UPI"),
        ("Not a UPI description", "Not UPI"),
        ("UPI/DR/123/NAME/BANK/ID", "No time"),
        ("160234", "Just time"),
    ]
    
    print(f"\nEdge cases:")
    for desc, desc_type in test_cases:
        try:
            is_upi = UPIParser.is_upi_description(desc) if desc else False
            time = UPIParser.extract_time(desc) if desc else None
            print(f"  {desc_type:30} -> is_upi={is_upi}, time={time}")
        except Exception as e:
            print(f"  {desc_type:30} -> ERROR: {e}")


# ============================================================================
# Usage Recommendations
# ============================================================================
"""
USAGE GUIDE:

1. For Standard UPI Descriptions (with time at end):
   - Use UPIParser.is_upi_description() to identify UPI transactions
   - Use UPIParser.extract_time() to get the timestamp
   - Use UPIParser.parse_upi_fields() to get all metadata

2. For Table Format Statements:
   - Use TableFormatUPIParser.parse_table_cell() if description is in a single cell
   - Use TableFormatUPIParser.merge_table_descriptions() if description spans columns

3. For Plain Text Statements:
   - Use PlainTextUPIParser.extract_upi_descriptions() for line-by-line extraction
   - Use PlainTextUPIParser.extract_wrapped_descriptions() if descriptions wrap

4. For Multiple UPI on One Line:
   - Use UPIParser.split_multi_upi_transactions() to split first
   - Then parse each transaction individually

5. For Cleanup/Normalization:
   - Use UPIParser.normalize_description() to clean descriptions
   - Use UPIParser.remove_timestamp() to remove timestamps

INTEGRATION POINTS:

1. In file_parsers.py:
   - Add UPI parsing to PDFParser.extract_transactions()
   - Handle UPI fields in ExcelParser for description columns
   - Use in CSVParser for bank statements with UPI transactions

2. In models.py:
   - Add UPI metadata fields to BankStatement model
   - Store extracted UPI ID, RRN, timestamp

3. In rules_engine.py:
   - Create rules based on UPI fields (name, UPI ID, etc.)
   - Apply rules on parsed UPI metadata

4. In views.py:
   - Display extracted UPI metadata in transaction details
   - Show UPI ID, RRN, timestamp in results
"""


if __name__ == '__main__':
    print("=" * 80)
    print("UPI PARSER TEST SUITE")
    print("=" * 80)
    
    test_standard_upi_with_time()
    test_time_format_variants()
    test_table_format()
    test_plain_text_format()
    test_wrapped_descriptions()
    test_multiple_upi_on_one_line()
    test_format_detection()
    test_normalization()
    test_upi_id_and_rrn_extraction()
    test_edge_cases()
    
    print("\n" + "=" * 80)
    print("All tests completed")
    print("=" * 80)
