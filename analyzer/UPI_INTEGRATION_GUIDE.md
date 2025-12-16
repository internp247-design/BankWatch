"""
UPI PARSER INTEGRATION GUIDE

This document shows how to integrate the UPI parser with your existing
BankWatch system to handle UPI descriptions that start with "UPI" and
end with time formats.

Different banks provide UPI descriptions in different formats:
- SBIN (State Bank): UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VALUATION//160234
- HDFC: UPI/CR/123456/NAME/HDFC/**ABC@OKHDFCBANK/REF//143056  
- ICICI: UPI IMPS 234567/MERCHANT/ICIC//152030
- Canara: Similar formats, various layouts

Time formats vary:
- 160234 (HHMMSS as 6 digits)
- 16:02:34 (HH:MM:SS with colons)
- 1602 (HHMM as 4 digits)
- 16:02 (HH:MM with colons)
"""

# ============================================================================
# INTEGRATION POINT 1: Enhance file_parsers.py PDFParser
# ============================================================================

"""
MODIFICATION: Add UPI parsing to PDFParser.extract_transactions()

Replace this section in file_parsers.py line ~100:

    @staticmethod
    def extract_transactions(pdf_path):
        # ... existing code ...
        
        for match in all_matches:
            try:
                # ... existing code ...
                
                transactions.append({
                    'date': date,
                    'description': description.strip(),
                    'amount': amount,
                    'transaction_type': transaction_type
                })

With this enhanced version:
"""

# Enhanced PDFParser.extract_transactions section
from analyzer.upi_parser import UPIParser

def extract_transactions_enhanced(pdf_path):
    """
    Enhanced extract_transactions with UPI parsing
    """
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
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.*?)\s+([+-]?[\d,]+\.\d{2})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+([+-]?[\d,]+\.\d{2})\s+(.*)',
            ]
            
            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, text)
                all_matches.extend(matches)
            
            print(f"Found {len(all_matches)} potential transactions")
            
            for match in all_matches:
                try:
                    if len(match) == 3:
                        if match[1].replace(',', '').replace('.', '').replace('-', '').isdigit():
                            date_str, amount_str, description = match
                        else:
                            date_str, description, amount_str = match
                    
                    # Parse date
                    date = PDFParser._parse_date(date_str)
                    if not date:
                        continue
                    
                    # Parse amount
                    amount, transaction_type = PDFParser._parse_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # NEW: Enhanced with UPI parsing
                    description_clean = description.strip()
                    upi_timestamp = None
                    upi_metadata = None
                    
                    if UPIParser.is_upi_description(description_clean):
                        # Extract timestamp
                        upi_timestamp = UPIParser.extract_time(description_clean)
                        # Parse UPI fields
                        upi_metadata = UPIParser.parse_upi_fields(description_clean)
                        # Normalize description
                        description_clean = UPIParser.normalize_description(
                            description_clean, 
                            keep_timestamp=True
                        )
                    
                    txn_dict = {
                        'date': date,
                        'description': description_clean,
                        'amount': amount,
                        'transaction_type': transaction_type
                    }
                    
                    # Add UPI metadata if present
                    if upi_metadata:
                        txn_dict.update({
                            'upi_type': upi_metadata.get('upi_type'),
                            'upi_transaction_type': upi_metadata.get('transaction_type'),
                            'upi_reference': upi_metadata.get('reference'),
                            'upi_sender_receiver': upi_metadata.get('sender_receiver'),
                            'upi_id': upi_metadata.get('upi_id'),
                            'upi_timestamp': upi_timestamp,
                        })
                    
                    transactions.append(txn_dict)
                    
                except Exception as e:
                    print(f"Error processing match: {e}")
                    continue
    
    except Exception as e:
        print(f"Error processing PDF: {e}")
    
    if not transactions:
        print("No transactions found in PDF, creating sample data")
        transactions = StatementParser._create_sample_transactions()
    
    return transactions


# ============================================================================
# INTEGRATION POINT 2: Enhance pdf_parser.py parse_transactions_from_text
# ============================================================================

"""
MODIFICATION: Improve UPI handling in parse_transactions_from_text()

Current code at lines ~280-350 handles UPI transactions by splitting on UPI/.
Enhance it to also extract timestamps:
"""

def parse_transactions_from_text_enhanced(text):
    """
    Enhanced version with UPI timestamp extraction
    """
    from analyzer.upi_parser import UPIParser
    
    raw_lines = [ln for ln in text.splitlines()]
    date_re = re.compile(r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b")
    amt_re = re.compile(r"(?<!\d)(\d{1,3}(?:[,]\d{3})*(?:\.\d{1,2})?)(?!\d)")
    markers = ['UPI/', 'IMPS', 'RTGS', 'MB', 'SI', 'CHQ', 'CHEQUE', 'CR', 'DR', 'NEFT', 'PAYMENT']
    
    # ... existing merging logic ...
    
    txs = []
    for ln in lines:
        m = date_re.search(ln)
        if not m:
            continue
        
        date_str = m.group(1)
        date = _try_parse_date(date_str)
        
        # Check for multiple UPI transactions
        block_text = ln
        upi_blocks = []
        
        for mk in ['UPI/', 'IMPS', 'RTGS', 'NEFT']:
            parts = re.split(f'(?={mk})', block_text)
            if len(parts) > 1:
                upi_blocks = [p for p in parts if p.strip()]
                break
        
        if len(upi_blocks) > 1:
            for upi_block in upi_blocks:
                desc = upi_block
                
                # NEW: Extract UPI timestamp
                upi_timestamp = UPIParser.extract_time(desc)
                
                # ... existing amount extraction ...
                amts = amt_re.findall(desc)
                amount = None
                transaction_type = 'UNKNOWN'
                
                # ... existing amount selection logic ...
                
                # NEW: Enhanced metadata
                upi_metadata = {}
                if UPIParser.is_upi_description(desc):
                    upi_metadata = UPIParser.parse_upi_fields(desc)
                
                txn_dict = {
                    'date': date,
                    'description': desc.strip(),
                    'amount': amount,
                    'transaction_type': transaction_type,
                }
                
                if upi_timestamp:
                    txn_dict['upi_timestamp'] = upi_timestamp
                
                if upi_metadata:
                    txn_dict['upi_metadata'] = upi_metadata
                
                txs.append(txn_dict)
        else:
            # ... existing single transaction logic ...
            
            # NEW: Add UPI parsing for single transactions
            if UPIParser.is_upi_description(description):
                upi_timestamp = UPIParser.extract_time(description)
                upi_metadata = UPIParser.parse_upi_fields(description)
                
                if upi_timestamp:
                    txn_dict['upi_timestamp'] = upi_timestamp
                if upi_metadata:
                    txn_dict['upi_metadata'] = upi_metadata
            
            txs.append(txn_dict)
    
    return txs


# ============================================================================
# INTEGRATION POINT 3: Update Database Model
# ============================================================================

"""
MODIFICATION: Add UPI fields to BankStatement model in models.py

In analyzer/models.py, update the BankStatement or Transaction model:
"""

# Add these fields to your model:
class BankStatementEnhanced:
    # ... existing fields ...
    
    # UPI-specific fields
    upi_type = models.CharField(max_length=20, null=True, blank=True)
    upi_transaction_type = models.CharField(max_length=10, null=True, blank=True)
    upi_reference = models.CharField(max_length=20, null=True, blank=True)
    upi_sender_receiver = models.CharField(max_length=100, null=True, blank=True)
    upi_id = models.CharField(max_length=50, null=True, blank=True)
    upi_timestamp = models.TimeField(null=True, blank=True)
    
    class Meta:
        # ... existing meta ...
        indexes = [
            models.Index(fields=['upi_id']),
            models.Index(fields=['upi_sender_receiver']),
            models.Index(fields=['upi_reference']),
        ]


# ============================================================================
# INTEGRATION POINT 4: Use UPI Parser in Rules Engine
# ============================================================================

"""
MODIFICATION: Enhance rules_engine.py to use UPI metadata

In analyzer/rules_engine.py, update apply_rule() method:
"""

def apply_rule_enhanced(rule, transaction, upi_metadata=None):
    """
    Enhanced rule matching with UPI metadata
    """
    from analyzer.upi_parser import UPIParser
    
    # ... existing rule matching logic ...
    
    # NEW: UPI-based rules
    if upi_metadata:
        # Rule by UPI ID
        if rule.condition_type == 'UPI_ID':
            return upi_metadata.get('upi_id', '').lower() == rule.condition_value.lower()
        
        # Rule by sender/receiver name
        elif rule.condition_type == 'UPI_NAME':
            sender = upi_metadata.get('sender_receiver', '').lower()
            return rule.condition_value.lower() in sender
        
        # Rule by transaction type (DR/CR)
        elif rule.condition_type == 'UPI_TYPE':
            return upi_metadata.get('transaction_type') == rule.condition_value
        
        # Rule by reference number
        elif rule.condition_type == 'UPI_REFERENCE':
            return upi_metadata.get('reference', '').startswith(rule.condition_value)
    
    # ... existing category assignment ...


# ============================================================================
# INTEGRATION POINT 5: Display UPI Metadata in Views
# ============================================================================

"""
MODIFICATION: Enhance views.py to display UPI information

In analyzer/views.py, update results view:
"""

def results_view_enhanced(request):
    """Enhanced results view showing UPI metadata"""
    from analyzer.upi_parser import UPIParser
    
    # ... existing view logic ...
    
    transactions_with_metadata = []
    
    for txn in transactions:
        txn_data = {
            'date': txn.date,
            'description': txn.description,
            'amount': txn.amount,
            'transaction_type': txn.transaction_type,
            'category': txn.category,
        }
        
        # Add UPI metadata if available
        if hasattr(txn, 'upi_timestamp') and txn.upi_timestamp:
            txn_data['upi_metadata'] = {
                'timestamp': txn.upi_timestamp,
                'type': getattr(txn, 'upi_transaction_type', None),
                'sender_receiver': getattr(txn, 'upi_sender_receiver', None),
                'upi_id': getattr(txn, 'upi_id', None),
                'reference': getattr(txn, 'upi_reference', None),
            }
        
        transactions_with_metadata.append(txn_data)
    
    context = {
        'transactions': transactions_with_metadata,
        # ... existing context ...
    }
    
    return render(request, 'analyzer/results.html', context)


# ============================================================================
# INTEGRATION POINT 6: Template Enhancement
# ============================================================================

"""
MODIFICATION: Update templates/analyzer/results.html

Add UPI metadata display in transaction detail rows:

{% for txn in transactions %}
    <tr>
        <td>{{ txn.date }}</td>
        <td>
            {{ txn.description }}
            {% if txn.upi_metadata %}
                <div class="upi-info">
                    <small>
                        {% if txn.upi_metadata.sender_receiver %}
                            <strong>Name:</strong> {{ txn.upi_metadata.sender_receiver }}
                        {% endif %}
                        {% if txn.upi_metadata.upi_id %}
                            <br><strong>UPI ID:</strong> {{ txn.upi_metadata.upi_id }}
                        {% endif %}
                        {% if txn.upi_metadata.reference %}
                            <br><strong>Ref:</strong> {{ txn.upi_metadata.reference }}
                        {% endif %}
                        {% if txn.upi_metadata.timestamp %}
                            <br><strong>Time:</strong> {{ txn.upi_metadata.timestamp }}
                        {% endif %}
                    </small>
                </div>
            {% endif %}
        </td>
        <td>{{ txn.amount }}</td>
        <td>{{ txn.transaction_type }}</td>
        <td>{{ txn.category }}</td>
    </tr>
{% endfor %}
"""

# ============================================================================
# QUICK START: Minimal Integration
# ============================================================================

"""
If you only want to add UPI parsing without modifying models/database:

1. Import in views.py:
   from analyzer.upi_parser import UPIParser

2. In transaction processing:
   for txn in transactions:
       if UPIParser.is_upi_description(txn.description):
           timestamp = UPIParser.extract_time(txn.description)
           upi_id = UPIParser.extract_upi_id(txn.description)
           # Store or use as needed

3. In categorization:
   if UPIParser.is_upi_description(description):
       fields = UPIParser.parse_upi_fields(description)
       name = fields.get('sender_receiver', '')
       # Use name for better categorization
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Common issues and solutions:

1. Time not extracting properly:
   - Check if time is at end of description
   - Verify time format matches one of these:
     * HHMMSS (6 digits): 160234
     * HH:MM:SS: 16:02:34
     * HHMM (4 digits): 1602
     * HH:MM: 16:02
   - Use detect_format_variant() to check format

2. Multiple UPI transactions on one line:
   - Use split_multi_upi_transactions() first
   - Then parse each separately

3. Descriptions spanning multiple lines:
   - Use extract_wrapped_descriptions() for plain text
   - Merge table columns with merge_table_descriptions()

4. UPI ID not extracting:
   - Verify format includes @ character
   - Check pattern: user@bank or **user@bank
   - Some banks use different formats

5. RRN not extracting:
   - RRN should be 8-12 digits after UPI/ marker
   - Some banks may use different field order
"""
