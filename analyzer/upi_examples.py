"""
Practical Examples: Using the UPI Parser with Real Bank Statements

This module demonstrates practical usage of the UPI parser with actual
bank statement examples from different Indian banks.
"""

from analyzer.upi_parser import (
    UPIParser, TableFormatUPIParser, PlainTextUPIParser
)


# ============================================================================
# EXAMPLE 1: SBIN (State Bank) e-Statement Format
# ============================================================================

class SBINExample:
    """Example processing of State Bank of India e-statements"""
    
    # Sample SBIN statement transactions
    SAMPLE_SBIN_TRANSACTIONS = [
        {
            'date': '10-12-2025',
            'description': 'UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VALUATION//160234',
            'debit': 5000.00,
            'credit': 0.00,
            'balance': 50000.00
        },
        {
            'date': '11-12-2025',
            'description': 'UPI/CR/234567891011/MERCHANT/ICIC/**ABC123@OKSBI/REF//143056',
            'debit': 0.00,
            'credit': 10000.00,
            'balance': 60000.00
        },
    ]
    
    @staticmethod
    def process_sbin_statement(transactions):
        """Process SBIN statement transactions"""
        print("\n" + "="*70)
        print("PROCESSING SBIN STATEMENT")
        print("="*70)
        
        processed = []
        
        for txn in transactions:
            print(f"\nTransaction Date: {txn['date']}")
            print(f"Raw Description: {txn['description'][:60]}...")
            
            desc = txn['description']
            
            # Extract UPI information
            if UPIParser.is_upi_description(desc):
                # Get all metadata
                timestamp = UPIParser.extract_time(desc)
                fields = UPIParser.parse_upi_fields(desc)
                upi_id = UPIParser.extract_upi_id(desc)
                rrn = UPIParser.extract_rrn(desc)
                
                print(f"✓ UPI Transaction")
                print(f"  Timestamp: {timestamp}")
                print(f"  Type: {fields['transaction_type']}")
                print(f"  Name: {fields['sender_receiver']}")
                print(f"  UPI ID: {upi_id}")
                print(f"  RRN: {rrn}")
                
                # Categorize based on name
                name = fields.get('sender_receiver', '').upper()
                category = SBINExample.categorize_by_upi_name(name)
                print(f"  Suggested Category: {category}")
                
                # Normalize for storage
                clean_desc = UPIParser.normalize_description(
                    desc, 
                    keep_timestamp=True
                )
                
                processed.append({
                    'date': txn['date'],
                    'description': clean_desc,
                    'amount': txn['debit'] or txn['credit'],
                    'transaction_type': 'DEBIT' if txn['debit'] > 0 else 'CREDIT',
                    'category': category,
                    'upi_timestamp': timestamp,
                    'upi_sender_receiver': fields.get('sender_receiver'),
                    'upi_id': upi_id,
                    'upi_rrn': rrn,
                })
        
        return processed
    
    @staticmethod
    def categorize_by_upi_name(name):
        """Categorize transaction based on UPI sender/receiver name"""
        keywords = {
            'FOOD': ['ZOMATO', 'SWIGGY', 'DOMINOS', 'RESTAURANT', 'CAFE'],
            'SHOPPING': ['AMAZON', 'FLIPKART', 'MYNTRA', 'MALL'],
            'BILLS': ['ELECTRICITY', 'WATER', 'INTERNET', 'AIRTEL'],
            'TRANSPORT': ['UBER', 'OLA', 'RAPIDO'],
            'ENTERTAINMENT': ['NETFLIX', 'HOTSTAR', 'BOOKMYSHOW'],
        }
        
        for category, keywords_list in keywords.items():
            if any(kw in name for kw in keywords_list):
                return category
        
        return 'OTHER'


# ============================================================================
# EXAMPLE 2: HDFC Table Format
# ============================================================================

class HDFCExample:
    """Example processing of HDFC table-format statements"""
    
    # Sample HDFC table data (from spreadsheet)
    SAMPLE_HDFC_TABLE = [
        {
            'date': '10-12-2025',
            'description': 'UPI/DR/301234567/JOHN.DOE/HDFC/**XYZ@OKHDFCBANK/PAYMENT//152030',
            'amount': 3500.00,
            'type': 'DEBIT',
            'balance': 75000.00
        },
        {
            'date': '12-12-2025',
            'description': 'UPI/CR/567890123/SALARY DEPOSIT/HDFC/**SAL@OKHDFCBANK/MONTHLY//090015',
            'amount': 50000.00,
            'type': 'CREDIT',
            'balance': 125000.00
        },
    ]
    
    @staticmethod
    def process_hdfc_table(table_rows):
        """Process HDFC table format"""
        print("\n" + "="*70)
        print("PROCESSING HDFC TABLE FORMAT")
        print("="*70)
        
        processed = []
        
        for row in table_rows:
            print(f"\nDate: {row['date']}")
            
            desc = row['description']
            
            if UPIParser.is_upi_description(desc):
                # Parse using table parser
                results = TableFormatUPIParser.parse_table_cell(desc)
                
                for result in results:
                    print(f"  UPI Transaction Found")
                    print(f"    Type: {result['transaction_type']}")
                    print(f"    Name: {result['sender_receiver']}")
                    print(f"    Timestamp: {result['timestamp']}")
                    
                    processed.append({
                        'date': row['date'],
                        'description': desc,
                        'amount': row['amount'],
                        'transaction_type': row['type'],
                        'upi_data': result,
                        'balance': row['balance']
                    })
        
        return processed


# ============================================================================
# EXAMPLE 3: Canara E-Passbook Format
# ============================================================================

class CanaraExample:
    """Example processing of Canara Bank e-passbook"""
    
    SAMPLE_CANARA_TEXT = """
    Date        Description                                    Debit    Credit   Balance
    10-12-2025  UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707    5000.00           45000.00
                @OKSBI/VALUATION//160234
    
    11-12-2025  UPI/CR/234567891011/MERCHANT/ICIC/**ABC123    -        10000.00 55000.00
                @OKSBI/REF//143056
    """
    
    @staticmethod
    def process_canara_epassbook(text):
        """Process Canara e-passbook text"""
        print("\n" + "="*70)
        print("PROCESSING CANARA E-PASSBOOK")
        print("="*70)
        
        # Split into lines
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        
        # Extract wrapped UPI descriptions
        results = PlainTextUPIParser.extract_wrapped_descriptions(lines)
        
        print(f"Found {len(results)} UPI transactions")
        
        for i, result in enumerate(results, 1):
            print(f"\nTransaction {i}:")
            print(f"  Type: {result['transaction_type']}")
            print(f"  Name: {result['sender_receiver']}")
            print(f"  Timestamp: {result['timestamp']}")
            print(f"  Fields: {result['raw_fields']}")
        
        return results


# ============================================================================
# EXAMPLE 4: Multiple UPI Transactions on One Line
# ============================================================================

class MultiUPIExample:
    """Example handling multiple UPI on single line"""
    
    SAMPLE_MULTI_UPI = (
        "10-12-2025 UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VAL//160234 "
        "UPI/CR/234567891011/MERCHANT/ICIC/**ABC123@OKSBI/REF//143056"
    )
    
    @staticmethod
    def process_multi_upi():
        """Process multiple UPI transactions"""
        print("\n" + "="*70)
        print("PROCESSING MULTIPLE UPI ON ONE LINE")
        print("="*70)
        
        print(f"Input: {MultiUPIExample.SAMPLE_MULTI_UPI[:70]}...")
        
        # Split into individual transactions
        transactions = UPIParser.split_multi_upi_transactions(
            MultiUPIExample.SAMPLE_MULTI_UPI
        )
        
        print(f"\nSplit into {len(transactions)} transactions:")
        
        for i, txn in enumerate(transactions, 1):
            if UPIParser.is_upi_description(txn):
                timestamp = UPIParser.extract_time(txn)
                fields = UPIParser.parse_upi_fields(txn)
                
                print(f"\nTransaction {i}:")
                print(f"  Type: {fields['transaction_type']}")
                print(f"  Timestamp: {timestamp}")
                print(f"  Name: {fields['sender_receiver']}")


# ============================================================================
# EXAMPLE 5: Data Quality Checking
# ============================================================================

class DataQualityExample:
    """Example of data quality checks using UPI parser"""
    
    SAMPLE_DESCRIPTIONS = [
        "UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VALUATION//160234",
        "UPI/CR/234567891011/MERCHANT/ICIC/**ABC123@OKSBI/REF//143056",
        "UPI/IMPS/301234567/JOHN.DOE/HDFC/**XYZ@OKHDFCBANK/PAYMENT//152030",
        "Regular bank transfer - no UPI",
        "UPI/DR/123456789/NAME/BANK/ID",  # No timestamp
        "",  # Empty
    ]
    
    @staticmethod
    def validate_upi_descriptions():
        """Validate and report on UPI descriptions"""
        print("\n" + "="*70)
        print("DATA QUALITY CHECK")
        print("="*70)
        
        stats = {
            'total': len(DataQualityExample.SAMPLE_DESCRIPTIONS),
            'valid_upi': 0,
            'upi_with_time': 0,
            'upi_with_name': 0,
            'upi_with_id': 0,
            'incomplete': [],
        }
        
        for desc in DataQualityExample.SAMPLE_DESCRIPTIONS:
            if not desc:
                continue
            
            if UPIParser.is_upi_description(desc):
                stats['valid_upi'] += 1
                
                if UPIParser.extract_time(desc):
                    stats['upi_with_time'] += 1
                
                fields = UPIParser.parse_upi_fields(desc)
                
                if fields.get('sender_receiver'):
                    stats['upi_with_name'] += 1
                
                if fields.get('upi_id'):
                    stats['upi_with_id'] += 1
                
                # Check for missing fields
                if not UPIParser.extract_time(desc):
                    stats['incomplete'].append(f"Missing time: {desc[:50]}...")
        
        print(f"\nTotal descriptions: {stats['total']}")
        print(f"Valid UPI: {stats['valid_upi']}")
        print(f"With timestamp: {stats['upi_with_time']}")
        print(f"With sender/receiver name: {stats['upi_with_name']}")
        print(f"With UPI ID: {stats['upi_with_id']}")
        
        if stats['incomplete']:
            print(f"\nIncomplete records: {len(stats['incomplete'])}")
            for item in stats['incomplete']:
                print(f"  - {item}")
        
        return stats


# ============================================================================
# EXAMPLE 6: Rule-Based Categorization
# ============================================================================

class RuleBasedExample:
    """Example of using UPI parser for smart categorization"""
    
    SAMPLE_TRANSACTIONS = [
        {
            'desc': 'UPI/DR/570467584215/ZOMATO/HDFC/**ZOMATO@OKHDFCBANK/ORDER//160234',
            'amount': 450.00,
        },
        {
            'desc': 'UPI/DR/234567891011/AMAZON/ICIC/**AMAZON@OKHDFCBANK/PURCHASE//143056',
            'amount': 2999.00,
        },
        {
            'desc': 'UPI/DR/301234567/AIRTEL/HDFC/**AIRTEL@OKHDFCBANK/RECHARGE//152030',
            'amount': 499.00,
        },
        {
            'desc': 'UPI/CR/567890123/EMPLOYER/HDFC/**SAL@OKHDFCBANK/SALARY//090015',
            'amount': 50000.00,
        },
    ]
    
    @staticmethod
    def categorize_with_rules():
        """Categorize transactions using UPI metadata"""
        print("\n" + "="*70)
        print("RULE-BASED CATEGORIZATION USING UPI PARSER")
        print("="*70)
        
        rules = {
            'FOOD': ['ZOMATO', 'SWIGGY', 'DOMINOS', 'RESTAURANT'],
            'SHOPPING': ['AMAZON', 'FLIPKART', 'MYNTRA', 'EBAY'],
            'UTILITIES': ['AIRTEL', 'JIOFIBER', 'ELECTRICITY', 'WATER'],
            'INCOME': lambda f: f.get('transaction_type') == 'CR',
        }
        
        for txn in RuleBasedExample.SAMPLE_TRANSACTIONS:
            desc = txn['desc']
            amount = txn['amount']
            
            fields = UPIParser.parse_upi_fields(desc)
            name = fields.get('sender_receiver', '').upper()
            
            category = 'OTHER'
            
            for cat, rule in rules.items():
                if callable(rule):
                    if rule(fields):
                        category = cat
                        break
                else:
                    if any(kw in name for kw in rule):
                        category = cat
                        break
            
            print(f"\n{name:20} ₹{amount:10.2f} -> {category}")


# ============================================================================
# MAIN: Run All Examples
# ============================================================================

def run_all_examples():
    """Run all example demonstrations"""
    
    print("\n" + "="*70)
    print("UPI PARSER - PRACTICAL EXAMPLES")
    print("="*70)
    
    # Example 1: SBIN
    sbin_processed = SBINExample.process_sbin_statement(
        SBINExample.SAMPLE_SBIN_TRANSACTIONS
    )
    
    # Example 2: HDFC
    hdfc_processed = HDFCExample.process_hdfc_table(
        HDFCExample.SAMPLE_HDFC_TABLE
    )
    
    # Example 3: Canara
    CanaraExample.process_canara_epassbook(CanaraExample.SAMPLE_CANARA_TEXT)
    
    # Example 4: Multiple UPI
    MultiUPIExample.process_multi_upi()
    
    # Example 5: Data Quality
    DataQualityExample.validate_upi_descriptions()
    
    # Example 6: Rule-Based
    RuleBasedExample.categorize_with_rules()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)


if __name__ == '__main__':
    run_all_examples()
