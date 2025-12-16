"""
UPI Transaction Parser

Handles parsing of UPI transaction descriptions that:
- Start with "UPI" (followed by markers like /, /DR, /CR, etc.)
- End with a time format (HH:MM:SS, HH:MM, or similar)
- May contain multiple fields separated by / delimiters
- Can appear in table format or plain text across multiple banks

UPI Description Format Examples:
1. UPI/DR/570467584215/RADHAKRIS/SBIN/**NR707@OKSBI/VALUATION//160234
2. UPI/CR/123456789/MERCHANT/ICIC/**ABC123@OKSBI/REF//143056
3. UPI IMPS 234567/JOHN/HDFC//152030

Metadata extraction includes:
- Transaction type (DR/CR)
- Reference number
- Sender/Receiver name
- UPI ID or Bank details
- Timestamp
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class UPIParser:
    """Parser for UPI transaction descriptions with flexible format handling"""
    
    # UPI transaction type markers
    UPI_MARKERS = ['UPI/', 'UPI/DR', 'UPI/CR', 'UPI/IMPS', 'UPI IMPS', 'UPI/RTGS', 'UPI/NEFT']
    
    # Time format patterns (various banks use different formats)
    TIME_PATTERNS = [
        r'(\d{1,2}):(\d{2}):(\d{2})(?:\s|$)',  # HH:MM:SS
        r'(\d{1,2}):(\d{2})(?:\s|$)',          # HH:MM
        r'(\d{6})(?:\s|$)',                    # HHMMSS (6 digits)
        r'(\d{4})(?:\s|$)',                    # HHMM (4 digits)
        r'T(\d{2}):(\d{2}):(\d{2})',           # ISO format T HH:MM:SS
    ]
    
    # Common UPI field delimiters
    DELIMITER = '/'
    
    @staticmethod
    def is_upi_description(description: str) -> bool:
        """Check if a description appears to be a UPI transaction"""
        if not description:
            return False
        text = description.upper().strip()
        return any(text.startswith(marker) for marker in UPIParser.UPI_MARKERS)
    
    @staticmethod
    def extract_time(description: str) -> Optional[str]:
        """Extract time from end of UPI description
        
        Returns:
            Time string in HH:MM:SS format, or None if not found
        """
        if not description:
            return None
        
        # Try each time pattern
        for pattern in UPIParser.TIME_PATTERNS:
            match = re.search(pattern, description)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # HH:MM:SS format
                    return f"{groups[0]:0>2}:{groups[1]}:{groups[2]}"
                elif len(groups) == 2:  # HH:MM format
                    return f"{groups[0]:0>2}:{groups[1]}"
                elif len(groups) == 1:  # 6-digit HHMMSS or 4-digit HHMM
                    time_str = groups[0]
                    if len(time_str) == 6:
                        return f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
                    elif len(time_str) == 4:
                        return f"{time_str[0:2]}:{time_str[2:4]}"
        
        return None
    
    @staticmethod
    def remove_timestamp(description: str) -> str:
        """Remove trailing timestamp from description
        
        Returns:
            Description without the timestamp
        """
        if not description:
            return description
        
        for pattern in UPIParser.TIME_PATTERNS:
            description = re.sub(pattern, '', description)
        
        return description.rstrip()
    
    @staticmethod
    def parse_upi_fields(description: str) -> Dict[str, Optional[str]]:
        """Parse UPI description fields separated by /
        
        Returns:
            Dict with keys: upi_type, transaction_type, reference, sender_receiver, 
                           upi_id, remarks, timestamp, raw_fields
        """
        result = {
            'upi_type': None,
            'transaction_type': None,  # DR or CR
            'reference': None,
            'sender_receiver': None,
            'upi_id': None,
            'remarks': None,
            'timestamp': None,
            'raw_fields': []
        }
        
        if not description:
            return result
        
        # Extract timestamp first
        timestamp = UPIParser.extract_time(description)
        if timestamp:
            result['timestamp'] = timestamp
            # Remove timestamp for field parsing
            description = UPIParser.remove_timestamp(description)
        
        # Split by delimiter
        fields = [f.strip() for f in description.split(UPIParser.DELIMITER)]
        result['raw_fields'] = fields
        
        if not fields:
            return result
        
        # First field is UPI type
        first_field = fields[0].upper()
        if first_field.startswith('UPI'):
            result['upi_type'] = fields[0]
            fields = fields[1:]
        
        # Process remaining fields
        if fields:
            # Second field may be transaction type (DR/CR) or reference
            field = fields[0].upper()
            if field in ['DR', 'CR']:
                result['transaction_type'] = field
                fields = fields[1:]
            elif field in ['IMPS', 'RTGS', 'NEFT']:
                result['transaction_type'] = field
                fields = fields[1:]
        
        # Next field is typically reference/RRN (numeric)
        if fields and fields[0]:
            field = fields[0]
            if field.isdigit() or re.match(r'^[A-Z0-9]+$', field):
                result['reference'] = field
                fields = fields[1:]
        
        # Next field is sender/receiver name
        if fields and fields[0]:
            result['sender_receiver'] = fields[0]
            fields = fields[1:]
        
        # Next field could be bank code or additional info
        if fields and fields[0]:
            result['upi_id'] = fields[0]
            fields = fields[1:]
        
        # Remaining fields as remarks
        if fields:
            remarks = [f for f in fields if f]
            if remarks:
                result['remarks'] = ' '.join(remarks)
        
        return result
    
    @staticmethod
    def extract_upi_id(description: str) -> Optional[str]:
        """Extract UPI ID (format: username@bank) from description
        
        Returns:
            UPI ID string or None
        """
        if not description:
            return None
        
        # Pattern for UPI ID: xxx@bank or **xxx@bank
        upi_pattern = r'(\*{0,2}[\w\.]+@\w+)'
        match = re.search(upi_pattern, description)
        
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    def extract_rrn(description: str) -> Optional[str]:
        """Extract RRN (Reconciliation Reference Number) from description
        
        RRN is typically an 8-12 digit number after UPI/ marker
        Returns:
            RRN string or None
        """
        if not description:
            return None
        
        # Look for numeric sequence after UPI marker
        pattern = r'UPI/?[A-Z/]*?(\d{8,12})'
        match = re.search(pattern, description, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    def extract_name(description: str) -> Optional[str]:
        """Extract sender/receiver name from UPI description
        
        Returns:
            Name string or None
        """
        fields = UPIParser.parse_upi_fields(description)
        return fields.get('sender_receiver')
    
    @staticmethod
    def normalize_description(description: str, keep_timestamp: bool = False) -> str:
        """Clean and normalize a UPI description
        
        Args:
            description: Raw description
            keep_timestamp: If True, preserve timestamp; otherwise remove it
        
        Returns:
            Normalized description
        """
        if not description:
            return description
        
        # Remove extra whitespace
        normalized = ' '.join(description.split())
        
        # If not keeping timestamp, remove it
        if not keep_timestamp:
            normalized = UPIParser.remove_timestamp(normalized)
        
        # Clean up multiple slashes
        normalized = re.sub(r'/+', '/', normalized)
        
        return normalized.strip()
    
    @staticmethod
    def split_multi_upi_transactions(text: str) -> List[str]:
        """Split text containing multiple UPI transactions (delimited by UPI/)
        
        Some bank statements list multiple transactions on one line.
        Example: "UPI/DR/123/NAME1/... UPI/CR/456/NAME2/..."
        
        Returns:
            List of individual transaction strings
        """
        if not text:
            return []
        
        # Find all UPI positions
        upi_positions = [m.start() for m in re.finditer(r'UPI', text, re.IGNORECASE)]
        
        if len(upi_positions) <= 1:
            return [text]
        
        # Split at each UPI position
        transactions = []
        for i, pos in enumerate(upi_positions):
            if i < len(upi_positions) - 1:
                transactions.append(text[pos:upi_positions[i+1]].strip())
            else:
                transactions.append(text[pos:].strip())
        
        return transactions
    
    @staticmethod
    def detect_format_variant(description: str) -> str:
        """Detect the UPI format variant used in this description
        
        Returns:
            String describing format: 'standard', 'table', 'compact', 'unknown'
        """
        if not description:
            return 'unknown'
        
        # Count delimiters
        slash_count = description.count('/')
        
        if slash_count >= 5:
            return 'standard'  # Full UPI/ format with many fields
        elif slash_count >= 2:
            return 'table'     # Table-like format (fewer fields per cell)
        elif re.match(r'UPI\s+\w+', description):
            return 'compact'   # Space-separated variant
        else:
            return 'unknown'


class TableFormatUPIParser:
    """Handle UPI descriptions from table-format bank statements
    
    In table format, a single cell might contain multiple UPI descriptions
    or descriptions might span multiple columns
    """
    
    @staticmethod
    def parse_table_cell(cell_content: str) -> List[Dict]:
        """Parse a single table cell that might contain UPI descriptions
        
        Returns:
            List of parsed UPI field dictionaries
        """
        if not cell_content:
            return []
        
        # Check if multiple transactions in one cell
        transactions = UPIParser.split_multi_upi_transactions(cell_content)
        
        results = []
        for txn in transactions:
            if UPIParser.is_upi_description(txn):
                parsed = UPIParser.parse_upi_fields(txn)
                results.append(parsed)
        
        return results
    
    @staticmethod
    def merge_table_descriptions(columns: List[str]) -> str:
        """Merge descriptions from multiple table columns
        
        Some statements split descriptions across columns.
        Example: Column1="UPI/DR/123", Column2="NAME", Column3="BANK"
        
        Args:
            columns: List of column values
        
        Returns:
            Merged description
        """
        # Join non-empty columns with space
        merged = ' '.join([str(col).strip() for col in columns if str(col).strip()])
        return merged


class PlainTextUPIParser:
    """Handle UPI descriptions from plain text (non-table) statements"""
    
    @staticmethod
    def extract_upi_descriptions(text: str) -> List[Dict]:
        """Extract all UPI descriptions from plain text
        
        Returns:
            List of parsed UPI field dictionaries
        """
        results = []
        
        if not text:
            return results
        
        # Find all lines containing UPI
        lines = text.split('\n')
        for line in lines:
            if UPIParser.is_upi_description(line):
                # Check for multiple transactions on same line
                transactions = UPIParser.split_multi_upi_transactions(line)
                for txn in transactions:
                    parsed = UPIParser.parse_upi_fields(txn)
                    results.append(parsed)
        
        return results
    
    @staticmethod
    def extract_wrapped_descriptions(lines: List[str]) -> List[Dict]:
        """Extract UPI descriptions that might wrap across multiple lines
        
        Args:
            lines: List of text lines
        
        Returns:
            List of parsed UPI field dictionaries
        """
        results = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if UPIParser.is_upi_description(line):
                # Start collecting description
                full_desc = line
                i += 1
                
                # Collect continuation lines (those not starting with known markers)
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    # Stop if next line is a new transaction marker
                    if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', next_line):
                        break
                    
                    # Stop if next line is another UPI marker
                    if UPIParser.is_upi_description(next_line):
                        break
                    
                    # Otherwise, append as continuation
                    if next_line:
                        full_desc += ' ' + next_line
                    
                    i += 1
                
                # Parse the complete description
                transactions = UPIParser.split_multi_upi_transactions(full_desc)
                for txn in transactions:
                    parsed = UPIParser.parse_upi_fields(txn)
                    results.append(parsed)
            else:
                i += 1
        
        return results
