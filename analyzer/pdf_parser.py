from datetime import datetime
import re

# Common transaction description markers
MARKERS = ['UPI/', 'IMPS', 'RTGS', 'MB', 'SI', 'CHQ', 'CHEQUE', 'CR', 'DR', 'NEFT', 'PAYMENT']

# Import only if available
try:
    from .file_parsers import StatementParser, PDFParser, ExcelParser, CSVParser
    FILE_PARSERS_AVAILABLE = True
except ImportError:
    FILE_PARSERS_AVAILABLE = False

# Optional OCR dependencies (used only for fallback parsing)
try:
    import fitz  # PyMuPDF
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

def extract_transactions_from_pdf(pdf_path):
    """Extract transactions from PDF file (backward compatibility)"""
    if FILE_PARSERS_AVAILABLE:
        return PDFParser.extract_transactions(pdf_path)
    else:
        # Fallback to simple parsing; prefer OCR if available
        return _simple_extract_transactions(pdf_path)

def extract_transactions_from_file(file_path, file_type):
    """Extract transactions from any supported file type"""
    if FILE_PARSERS_AVAILABLE:
        return StatementParser.parse_file(file_path, file_type)
    else:
        # Fallback
        return _create_sample_transactions()

def categorize_transaction(description, amount, transaction_type):
    """
    Categorize transactions based on description keywords
    """
    description_lower = description.lower()
    
    if transaction_type == 'CREDIT':
        return 'INCOME'
    
    expense_keywords = {
        'FOOD': ['restaurant', 'cafe', 'food', 'grocery', 'supermarket', 'zomato', 'swiggy'],
        'SHOPPING': ['mall', 'shopping', 'store', 'amazon', 'flipkart', 'myntra'],
        'BILLS': ['electricity', 'water', 'internet', 'mobile', 'bill', 'broadband'],
        'TRANSPORT': ['fuel', 'petrol', 'uber', 'ola', 'taxi', 'bus', 'metro'],
        'LOAN': ['loan', 'emi', 'repayment'],
        'ENTERTAINMENT': ['movie', 'netflix', 'entertainment', 'hotstar'],
        'HEALTHCARE': ['hospital', 'clinic', 'medical', 'pharmacy'],
        'TRAVEL': ['flight', 'hotel', 'travel', 'booking'],
    }
    
    for category, keywords in expense_keywords.items():
        if any(keyword in description_lower for keyword in keywords):
            return category
    
    return 'OTHER'

# Simple fallback functions
def _simple_extract_transactions(pdf_path):
    """Simple fallback PDF parser"""
    print("Using simple PDF parser")
    # If OCR libs are available, attempt to extract raw text from the PDF
    if OCR_AVAILABLE:
        try:
            text = extract_text_from_pdf(pdf_path)
            # Return a single pseudo-transaction containing the raw OCR text
            return [
                {
                    'date': None,
                    'description': text,
                    'amount': None,
                    'transaction_type': 'UNKNOWN'
                }
            ]
        except Exception as e:
            # Fall back to sample transactions on any OCR error
            print(f"OCR fallback failed: {e}")
            return _create_sample_transactions()
    else:
        return _create_sample_transactions()


def extract_text_from_pdf(pdf_path, pages=None, dpi=200):
    """Extract OCR text from a PDF using PyMuPDF + Tesseract.

    - `pages`: None (all) or iterable of zero-based page indices to process.
    - `dpi`: render resolution for rasterization.
    Returns the concatenated text from the requested pages.
    """
    if not OCR_AVAILABLE:
        raise RuntimeError("OCR dependencies not available (PyMuPDF/pytesseract)")

    doc = fitz.open(pdf_path)
    if pages is None:
        pages_to_process = range(doc.page_count)
    else:
        pages_to_process = pages

    texts = []
    import tempfile, os
    for pno in pages_to_process:
        page = doc.load_page(pno)
        pix = page.get_pixmap(dpi=dpi)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_name = tmp.name
        try:
            pix.save(tmp_name)
            img = Image.open(tmp_name)
            page_text = pytesseract.image_to_string(img, lang='eng')
            texts.append(page_text)
        finally:
            try:
                os.remove(tmp_name)
            except Exception:
                pass

    return "\n".join(texts)


def _try_parse_date(date_str):
    """Try common date formats and dateutil as fallback."""
    # Normalize separators
    s = date_str.strip()
    s = s.replace('/', '-').replace('.', '-')
    # Try common formats
    for fmt in ("%d-%m-%Y", "%d-%m-%y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    # Fallback to dateutil if available
    try:
        from dateutil import parser as _p
        return _p.parse(s, dayfirst=True).date()
    except Exception:
        return None


def parse_transactions_from_text(text):
    """Parse OCR text to a list of transaction dicts.

    Heuristic-based parser: finds lines containing a date, extracts amount(s)
    and determines debit/credit where possible.
    Returns list of dicts: {date, description, amount, transaction_type}
    """
    raw_lines = [ln for ln in text.splitlines()]
    # regex for dates like 09-09-2025 or 09/09/2025 (used while merging)
    date_re = re.compile(r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b")
    # regex for amounts like 3,626.30 or 3500.00 (captures commas and decimals)
    amt_re = re.compile(r"(?<!\d)(\d{1,3}(?:[,]\d{3})*(?:\.\d{1,2})?)(?!\d)")
    # common transaction markers that often start the description
    markers = ['UPI/', 'IMPS', 'RTGS', 'MB', 'SI', 'CHQ', 'CHEQUE', 'CR', 'DR', 'NEFT', 'PAYMENT']
    
    # Keywords that signal page summary/footer (stop collecting transaction lines)
    page_markers = ['deposits', 'withdrawals', 'balance', 'narration', 'summary', 'page']

    # Keep original (possibly empty) lines to preserve structure; we'll trim selectively
    # Merge lines so that a date-starting line collects following lines that don't start with a date.
    lines = []
    i = 0
    total = len(raw_lines)
    while i < total:
        ln = raw_lines[i].strip()
        if not ln:
            i += 1
            continue
        # If current line contains a date, start a new block and collect continuation lines
        if date_re.search(ln):
            # Lookahead: check if this is a real transaction (has UPI/ etc) or just a header
            # Look at the next few non-empty lines
            lookahead_idx = i + 1
            has_marker = False
            lookahead_count = 0
            while lookahead_idx < total and lookahead_count < 5:
                lookahead_line = raw_lines[lookahead_idx].strip()
                if lookahead_line:
                    # Check if this non-empty line is another date
                    if date_re.search(lookahead_line):
                        # This date is a header if the next non-empty line is also a date
                        # Skip this date line
                        break
                    # Check for transaction markers
                    if any(mk in lookahead_line for mk in ['UPI/', 'IMPS', 'RTGS', 'NEFT']):
                        has_marker = True
                        break
                    lookahead_count += 1
                lookahead_idx += 1
            
            # Skip if it's a header date (next non-empty is another date, no marker found)
            if not has_marker and lookahead_idx < total and date_re.search(raw_lines[lookahead_idx].strip()):
                i += 1
                continue
            
            block_lines = [ln]
            j = i + 1
            while j < total:
                nxt = raw_lines[j].strip()
                if not nxt:
                    j += 1
                    continue
                # Stop collecting if next line looks like it contains a new date (new transaction)
                if date_re.search(nxt):
                    break
                # Stop collecting if we hit page summary markers
                if any(kw.lower() in nxt.lower() for kw in page_markers):
                    break
                # Stop if the line is just a single digit (page number)
                if re.match(r'^\d+$', nxt):
                    break
                # Otherwise treat as continuation of the description — preserve as a newline
                block_lines.append(nxt)
                j += 1
            # Join with newline to preserve multi-line descriptions
            lines.append("\n".join(block_lines))
            i = j
        else:
            # If a line doesn't contain a date, it might be a stray header/footer; skip or attach to previous if exists
            if lines:
                # attach as continuation to last block
                lines[-1] = lines[-1] + "\n" + ln
            else:
                # no previous block, skip
                pass
            i += 1
    txs = []

    # regex for dates like 09-09-2025 or 09/09/2025
    date_re = re.compile(r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b")
    # regex for amounts like 3,626.30 or 3500.00 (captures commas and decimals)
    amt_re = re.compile(r"(?<!\d)(\d{1,3}(?:[,]\d{3})*(?:\.\d{1,2})?)(?!\d)")
    # common transaction markers that often start the description
    markers = ['UPI/', 'IMPS', 'RTGS', 'MB', 'SI', 'CHQ', 'CHEQUE', 'CR', 'DR', 'NEFT', 'PAYMENT']

    for ln in lines:
        m = date_re.search(ln)
        if not m:
            continue
        date_str = m.group(1)
        date = _try_parse_date(date_str)

        # Check if this block contains multiple UPI transactions (split by UPI/)
        # This handles Canara e-passbooks where multiple transactions share one date line
        block_text = ln
        upi_blocks = []
        
        # Find all UPI/ positions in the block
        for mk in ['UPI/', 'IMPS', 'RTGS', 'NEFT']:
            parts = re.split(f'(?={mk})', block_text)
            if len(parts) > 1:
                # This block has multiple transactions
                upi_blocks = [p for p in parts if p.strip()]
                break
        
        # If we found multiple transaction markers, process each as separate
        if len(upi_blocks) > 1:
            for upi_block in upi_blocks:
                desc = upi_block
                amts = amt_re.findall(desc)
                amount = None
                transaction_type = 'UNKNOWN'
                
                # Helper to convert amount strings to float
                def to_float(s):
                    try:
                        return float(s.replace(',', ''))
                    except Exception:
                        return None
                
                amt_vals = [(a, to_float(a)) for a in amts]
                amt_vals = [t for t in amt_vals if t[1] is not None]
                decimals = [t for t in amt_vals if '.' in t[0]]
                large = [t for t in amt_vals if (',' in t[0] or len(re.sub(r"[^0-9]", "", t[0])) >= 3)]
                small = [t for t in amt_vals if t not in decimals and t not in large]
                
                chosen = None
                if decimals:
                    chosen = decimals[-2][1] if len(decimals) >= 2 else decimals[-1][1]
                elif large:
                    chosen = large[-2][1] if len(large) >= 2 else large[-1][1]
                elif amt_vals:
                    if len(amt_vals) >= 2:
                        cand = amt_vals[-2][1]
                        if cand is not None and cand > 31:
                            chosen = cand
                    else:
                        cand = amt_vals[-1][1]
                        if cand is not None and cand > 31:
                            chosen = cand
                
                if chosen is not None:
                    amount = chosen
                    if 'CR' in desc.upper():
                        transaction_type = 'CREDIT'
                    else:
                        transaction_type = 'DEBIT'
                
                txs.append({
                    'date': date,
                    'description': desc.strip(),
                    'amount': amount,
                    'transaction_type': transaction_type,
                })
            continue
        
        # Single transaction per date (normal case)
        # remove the date token from the block to get description (keep remaining newlines)
        after_date = ln[m.end():].lstrip()
        # find amounts on the line
        amts = amt_re.findall(ln)
        amount = None
        transaction_type = 'UNKNOWN'

        # helper to convert amount strings to float
        def to_float(s):
            try:
                return float(s.replace(',', ''))
            except Exception:
                return None

        # Better amount selection heuristics:
        # - Classify candidates into decimals (have '.'), large numbers (commas or >=3 digits), and small integers.
        # - Prefer a decimal-containing amount (likely transaction value). If multiple, choose the penultimate among decimals.
        # - Else prefer a large number (with commas or >=3 digits). Use the penultimate one when multiple.
        # - As a last resort choose the penultimate numeric token if it's >31 (not a day number).
        amt_vals = [(a, to_float(a)) for a in amts]
        amt_vals = [t for t in amt_vals if t[1] is not None]
        decimals = [t for t in amt_vals if '.' in t[0]]
        large = [t for t in amt_vals if (',' in t[0] or len(re.sub(r"[^0-9]", "", t[0])) >= 3)]
        small = [t for t in amt_vals if t not in decimals and t not in large]

        chosen = None
        if decimals:
            # if multiple decimals, prefer penultimate decimal (last may be balance)
            chosen = decimals[-2][1] if len(decimals) >= 2 else decimals[-1][1]
        elif large:
            chosen = large[-2][1] if len(large) >= 2 else large[-1][1]
        elif amt_vals:
            # pick penultimate numeric value if it looks not like day (greater than 31)
            if len(amt_vals) >= 2:
                cand = amt_vals[-2][1]
                if cand is not None and cand > 31:
                    chosen = cand
            if chosen is None:
                # fallback: take last but ensure >31
                cand = amt_vals[-1][1]
                if cand is not None and cand > 31:
                    chosen = cand

        amount = chosen

        # check for DR/CR hints
        ln_upper = ln.upper()
        if ' DR ' in ln_upper or '/DR/' in ln_upper or 'DEBIT' in ln_upper or ' DR/' in ln_upper:
            transaction_type = 'DEBIT'
        elif ' CR ' in ln_upper or '/CR/' in ln_upper or 'CREDIT' in ln_upper or 'CR/' in ln_upper:
            transaction_type = 'CREDIT'
        else:
            # No explicit marker found - try to infer from description keywords
            # Default to DEBIT since most transactions are expenses
            transaction_type = 'DEBIT'
            
            # Check for credit-indicating keywords in description
            if amount is not None:
                desc_upper = ln.upper()
                credit_keywords = ['SALARY', 'DEPOSIT', 'REFUND', 'CREDIT', 'INCOME', 'TRANSFER IN', 'RECEIVED']
                if any(kw in desc_upper for kw in credit_keywords):
                    transaction_type = 'CREDIT'

        # Try to find a marker in the remaining text to start description
        desc = after_date
        # Preserve newlines in description to match original multi-line OCR parts
        marker_pos = None
        for mk in markers:
            # search case-insensitive in the part after the date and in the whole line
            idx = desc.upper().find(mk)
            if idx != -1:
                marker_pos = idx
                break
        if marker_pos is not None:
            description = desc[marker_pos:]
        else:
            # fallback: try find marker anywhere in the line
            found = None
            for mk in markers:
                idx = ln.upper().find(mk)
                if idx != -1:
                    found = idx
                    break
            if found is not None:
                # include the rest of the block starting at the marker; keep newlines
                description = '\n'.join(ln[found:].splitlines())
            else:
                description = desc

        # Remove trailing amount/balance tokens or partial numeric fragments from description
        description = re.sub(r"[,:\-]*\s*(\d{1,3}(?:[,]\d{3})*(?:\.\d{1,2})?)\s*[,:\-]*$", "", description).strip()
        # Remove trailing tokens that are small integers (likely day numbers or fragments)
        description = re.sub(r"\s+\b\d{1,2}\b[,:\-]*$", "", description).strip()
        # Remove trailing stray commas or punctuation
        description = re.sub(r"[,:;\-]+$", "", description).strip()
        # Clean some artifacts and collapse whitespace
        description = re.sub(r"\s{2,}", " ", description)

        txs.append({
            'date': date,
            'description': description,
            'amount': amount,
            'transaction_type': transaction_type,
        })

    return txs


def is_table_like(text, amount_token_threshold=2, line_ratio_threshold=0.4):
    """Detect whether OCR text already contains table-like rows/columns.

    Heuristic: if a significant fraction of non-empty lines contain >= `amount_token_threshold`
    numeric amount tokens (commas/decimals), consider it table-like.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    amt_pattern = re.compile(r"(?<!\d)(\d{1,3}(?:[,]\d{3})*(?:\.\d{1,2})?)(?!\d)")
    count = 0
    for ln in lines:
        amts = amt_pattern.findall(ln)
        if len(amts) >= amount_token_threshold:
            count += 1
    return (count / len(lines)) >= line_ratio_threshold


def parse_table_lines(text):
    """Parse lines that look like table rows into structured dicts.

    Returns list of dicts with columns: date, description, debit, credit, balance, transaction_type
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    date_re = re.compile(r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b")
    amt_re = re.compile(r"(?<!\d)(\d{1,3}(?:[,]\d{3})*(?:\.\d{1,2})?)(?!\d)")
    results = []
    for ln in lines:
        m = date_re.search(ln)
        if not m:
            continue
        date = _try_parse_date(m.group(1))
        after = ln[m.end():].strip()
        amts = amt_re.findall(ln)
        amt_vals = [float(a.replace(',', '')) for a in amts if a]
        debit = credit = balance = None
        if len(amt_vals) >= 2:
            # assume last is balance, penultimate is transaction amount
            balance = amt_vals[-1]
            txn_amt = amt_vals[-2]
            if len(amt_vals) >= 3:
                debit = amt_vals[-3]
            else:
                debit = txn_amt
        elif len(amt_vals) == 1:
            debit = amt_vals[0]

        # Force description to start at a recognized marker if present
        desc = after
        marker_pos = None
        for mk in MARKERS:
            idx = desc.upper().find(mk)
            if idx != -1:
                marker_pos = idx
                break
        if marker_pos is not None:
            description = desc[marker_pos:]
        else:
            # fallback: try find marker anywhere in the full line
            found = None
            for mk in MARKERS:
                idx = ln.upper().find(mk)
                if idx != -1:
                    found = idx
                    break
            if found is not None:
                description = ln[found:]
            else:
                description = desc

        # strip footer tokens and trailing numeric fragments
        description = re.sub(r"\bpage\b.*$", "", description, flags=re.I).strip()
        description = re.sub(r"[,;:\-]*\s*(\d{1,3}(?:[,]\d{3})*(?:\.\d{1,2})?)\s*[,;:\-]*$", "", description).strip()

        results.append({
            'date': date,
            'description': description,
            'debit': debit,
            'credit': credit,
            'balance': balance,
            'transaction_type': 'UNKNOWN'
        })
    return results


def convert_freeform_to_table(text):
    """Convert freeform OCR text (no table) into table rows using our parser heuristics.

    Returns list of dicts with columns: date, description, debit, credit, balance, transaction_type
    """
    blocks = parse_transactions_from_text(text)
    table = []
    amt_re = re.compile(r"(?<!\d)(\d{1,3}(?:[,]\d{3})*(?:\.\d{1,2})?)(?!\d)")
    for b in blocks:
        desc_block = b.get('description', '')
        # find all numeric tokens in the block (including continuation lines)
        amts = amt_re.findall(desc_block)
        amt_vals = [float(a.replace(',', '')) for a in amts if a]
        debit = credit = balance = None
        if b.get('amount') is not None:
            # if parse_transactions_from_text already determined an amount, use it
            debit = b['amount'] if b.get('transaction_type') == 'DEBIT' else None
            credit = b['amount'] if b.get('transaction_type') == 'CREDIT' else None
        # Use heuristic: if there's at least one numeric token at end of description, treat last as balance
        if amt_vals:
            if len(amt_vals) >= 2:
                balance = amt_vals[-1]
                txn_amt = amt_vals[-2]
                # assign txn_amt to debit/credit based on existing type, else to debit
                if b.get('transaction_type') == 'CREDIT':
                    credit = txn_amt
                else:
                    debit = txn_amt
            else:
                # single amount — treat as debit by default
                debit = amt_vals[0]

        table.append({
            'date': b.get('date'),
            'description': desc_block,
            'debit': debit,
            'credit': credit,
            'balance': balance,
            'transaction_type': b.get('transaction_type', 'UNKNOWN')
        })
    return table


def process_pdf_to_table(pdf_path, pages=None):
    """High-level: extract text, detect table-like structure, and return table rows.

    If the document is already table-like, parse table lines; otherwise convert freeform to table.
    """
    text = extract_text_from_pdf(pdf_path, pages=pages)
    # If this looks like a known bank format, use bank-specific parser
    txt_upper = text.upper() if isinstance(text, str) else ''
    fname = pdf_path.lower() if isinstance(pdf_path, str) else ''
    if 'CANARA' in txt_upper or 'canara' in fname or 'epassbook' in fname:
        try:
            rows = parse_canara_epassbook(text)
            return rows
        except Exception:
            # fallback to generic path on errors
            pass

    if is_table_like(text):
        rows = parse_table_lines(text)
    else:
        rows = convert_freeform_to_table(text)
    return rows


def _normalize_amount_str(s: str):
    """Normalize an amount string by removing commas and non-numeric prefixes/suffixes.

    Returns float or None.
    """
    if not s:
        return None
    s = s.strip()
    # remove common trailing words like 'page'
    s = re.sub(r"\bpage\b.*$", "", s, flags=re.I).strip()
    # keep digits, commas and dot and minus
    s = re.sub(r"[^0-9,\.\-]", "", s)
    if not s:
        return None
    # remove commas (works for both Indian and western grouping)
    s2 = s.replace(',', '')
    try:
        return float(s2)
    except Exception:
        return None


def parse_canara_epassbook(text):
    """Parse Canara e-passbook style OCR text into table rows.

    Strategy:
    - Use `parse_transactions_from_text` to get multi-line blocks (preserves descriptions)
    - Split blocks containing multiple UPI transactions (detected by UPI/ markers)
    - For each block, find numeric tokens in description; interpret last as balance when present
      and penultimate as transaction amount.
    - Normalize numeric strings robustly (handles commas / Indian grouping).
    - Strip footer tokens like 'page' from descriptions.
    - Filter out reference-only entries (cheques without actual amounts).
    - Clean OCR noise like 'Deposits', 'Withdrawals', 'Date', 'Balance', 'page X' etc.
    """
    blocks = parse_transactions_from_text(text)
    
    # Split blocks containing multiple UPI transactions
    expanded_blocks = []
    for b in blocks:
        desc = b.get('description', '')
        # Count UPI/ markers in this block
        upi_count = desc.upper().count('UPI/')
        if upi_count > 1:
            # Split by UPI/ marker, keeping marker with each piece
            import re as re_module
            parts = re_module.split(r'(?=UPI/)', desc)
            for part in parts:
                if part.strip():
                    expanded_blocks.append({
                        'date': b['date'],
                        'description': part.strip(),
                        'amount': b.get('amount'),
                        'transaction_type': b.get('transaction_type', 'UNKNOWN')
                    })
        else:
            expanded_blocks.append(b)
    
    rows = []
    # Amount regex: must have decimal OR comma OR be short (max 6 digits without decimal)
    # This filters out bare multi-digit fragments like "569" from reference numbers "569684442474"
    amt_re = re.compile(r"(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d{1,2}(?:\.\d{1,2})?)")
    
    # Page element keywords that should be stripped from descriptions
    page_keywords = [
        'deposits', 'withdrawals', 'balance', 'date', 'page', 'narration',
        'statement', 'account', 'summary'
    ]
    
    for b in expanded_blocks:
        desc = b.get('description', '') or ''
        
        # Remove page markers and footer information
        desc_clean = desc
        for kw in page_keywords:
            desc_clean = re.sub(r'\b' + kw + r'\b.*?(?=UPI/|IMPS|RTGS|NEFT|$)', '', desc_clean, flags=re.I)
        
        # remove common footer header words and page references
        desc_clean = re.sub(r"\bpage\s+\d+\b", "", desc_clean, flags=re.I)
        desc_clean = re.sub(r"^ *\d+$", "", desc_clean, flags=re.MULTILINE)  # single digits per line (page numbers)
        # Remove Chq/Cha reference lines (they're metadata, not part of description)
        desc_clean = re.sub(r'\b(?:Chq|Cha):\s*\d+\b', '', desc_clean, flags=re.I)
        
        # Clean up multi-line descriptions - join them but preserve UPI markers
        desc_clean = '\n'.join([line.strip() for line in desc_clean.split('\n') if line.strip()])
        
        # Skip empty descriptions and pure reference entries
        if not desc_clean or desc_clean.lower().startswith('chq:') or desc_clean.lower().startswith('cha:'):
            continue
        
        # Skip if this part contains a marker but ONLY has Chq/Cha lines (reference-only)
        has_upi_marker = any(mk in desc_clean.upper() for mk in ['UPI/', 'IMPS', 'RTGS', 'NEFT'])
        has_chq_marker = 'CHQ:' in desc_clean.upper() or 'CHA:' in desc_clean.upper()
        if not has_upi_marker and has_chq_marker:
            continue
        
        # Skip if description contains ONLY page keywords (noise-only entries)
        if all(kw.lower() in desc_clean.lower() for kw in ['withdrawals', 'deposits']):
            continue
        
        # Force description to start at a known marker if present
        marker_pos = None
        for mk in MARKERS:
            idx = desc_clean.upper().find(mk)
            if idx != -1:
                marker_pos = idx
                break
        if marker_pos is not None:
            desc_clean = desc_clean[marker_pos:]
        else:
            # If no marker found, skip - we only accept well-formed transactions with markers
            continue
        
        # Extract amounts BEFORE trimming (amounts may come after the time on same line in PDF)
        # find all amount-like tokens in the FULL description (before clipping)
        amts = amt_re.findall(desc_clean)
        # normalize
        amt_vals = [_normalize_amount_str(a) for a in amts if _normalize_amount_str(a) is not None]
        
        # Filter out huge numbers (likely reference IDs not amounts)
        amt_vals = [a for a in amt_vals if a < 1000000]
        
        # Now extract the clean transaction display text (from UPI marker to time format HH:MM:SS)
        # Remove "Chq:" lines which are metadata after the transaction
        time_match = re.search(r'\d{1,2}:\d{2}:\d{2}', desc_clean)
        if time_match:
            # Keep everything up to and including the time
            desc_clean = desc_clean[:time_match.end()]
        
        # Remove any "Chq:" or "Cha:" lines (reference metadata)
        desc_clean = re.sub(r'Cha?:\s*\d+', '', desc_clean).strip()

        debit = credit = balance = None
        # choose balance and txn amount heuristics
        if len(amt_vals) >= 2:
            balance = amt_vals[-1]
            txn_amt = amt_vals[-2]
            # set debit/credit based on DR/CR tokens
            dun = desc_clean.upper()
            if ' CR' in dun or '/CR/' in dun or 'CREDIT' in dun:
                credit = txn_amt
            else:
                debit = txn_amt
        elif len(amt_vals) == 1:
            # single amount -> treat as debit by default unless 'CR' present
            if ' CR' in desc_clean.upper() or '/CR/' in desc_clean.upper():
                credit = amt_vals[0]
            else:
                debit = amt_vals[0]
        else:
            # No valid amounts found, skip
            continue
        
        # Skip transactions without either debit or credit
        if debit is None and credit is None:
            continue

        rows.append({
            'date': b.get('date'),
            'description': desc_clean,
            'debit': debit,
            'credit': credit,
            'balance': balance,
            'transaction_type': b.get('transaction_type', 'UNKNOWN')
        })

    return rows

def _create_sample_transactions():
    """Create sample transactions"""
    return [
        {
            'date': datetime.now().date(),
            'description': 'Salary Deposit',
            'amount': 50000.00,
            'transaction_type': 'CREDIT'
        },
        {
            'date': datetime.now().date(),
            'description': 'Grocery Shopping',
            'amount': 2500.50,
            'transaction_type': 'DEBIT'
        },
        {
            'date': datetime.now().date(),
            'description': 'Internet Bill',
            'amount': 899.00,
            'transaction_type': 'DEBIT'
        }
    ]
    
def parse_transactions_from_text(text):
    """
    FIXED VERSION – Extracts full multi-line descriptions without cutting.
    Works for Canara Bank and all free-form statements.
    """

    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # DATE DETECTOR
    date_re = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b")
    amt_re = re.compile(r"(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)")

    blocks = []
    i = 0

    # 1) GROUP LINES BY DATE → description continues until next date
    while i < len(raw_lines):
        line = raw_lines[i]

        if date_re.search(line):
            current_block = [line]
            j = i + 1

            while j < len(raw_lines):
                nxt = raw_lines[j]

                # next date → stop description
                if date_re.search(nxt):
                    break

                current_block.append(nxt)
                j += 1

            blocks.append("\n".join(current_block))
            i = j
        else:
            i += 1

    transactions = []

    # 2) Parse each block
    for block in blocks:
        m = date_re.search(block)
        if not m:
            continue

        date_str = m.group(1)
        date = _try_parse_date(date_str)

        # FULL DESCRIPTION (keep all lines except date)
        description = block.replace(date_str, "").strip()

        # Detect amount
        amts = amt_re.findall(block)
        cleaned_amts = [a for a in amts if a.replace(",", "").replace(".", "").isdigit()]

        amount = None
        transaction_type = "UNKNOWN"

        # Choose penultimate amount (txn amount), last = balance
        if len(cleaned_amts) >= 2:
            amount = float(cleaned_amts[-2].replace(",", ""))
        elif len(cleaned_amts) == 1:
            amount = float(cleaned_amts[0].replace(",", ""))

        # DR / CR detection
        up = block.upper()
        if " DR" in up or "/DR/" in up:
            transaction_type = "DEBIT"
        elif " CR" in up or "/CR/" in up:
            transaction_type = "CREDIT"

        transactions.append({
            "date": date,
            "description": description,
            "amount": amount,
            "transaction_type": transaction_type
        })

    return transactions

def extract_upi_metadata(description):
    """
    Extract UPI metadata from multi-line descriptions.
    Works for Canara, SBI, HDFC, ICICI, Axis UPI formats.
    """

    meta = {
        "method": "UPI",
        "sender_name": None,
        "receiver_name": None,
        "upi_id": None,
        "merchant": None,
        "rrn": None,
        "reference_no": None,
        "bank_trace_id": None,
        "timestamp": None,
    }

    # Clean description for easier pattern matching
    text = description.replace("\n", " ").replace("//", "/")

    # ---------------------------------------
    # UPI ID (example: anoop@okaxis)
    # ---------------------------------------
    upi_match = re.search(r"\b([a-zA-Z0-9.\-_]+@[a-zA-Z]+)\b", text)
    if upi_match:
        meta["upi_id"] = upi_match.group(1)

    # ---------------------------------------
    # RRN (UPI Reference Transaction Number)
    # Usually 10–18 digits
    # ---------------------------------------
    rrn_match = re.search(r"\b(\d{10,18})\b", text)
    if rrn_match:
        meta["rrn"] = rrn_match.group(1)

    # ---------------------------------------
    # Bank Trace ID (alphanumeric 16–32 chars)
    # ---------------------------------------
    trace_match = re.search(r"\b([A-Z0-9]{12,32})\b", text)
    if trace_match:
        meta["bank_trace_id"] = trace_match.group(1)

    # ---------------------------------------
    # Merchant (PURCHASE, PAYMENT, SHOP NAME)
    # ---------------------------------------
    merchant_match = re.search(r"\b(PURCHASE|PAYMENT|SHOP|MERCHANT|POS|UPI PAY)\b", text, re.IGNORECASE)
    if merchant_match:
        meta["merchant"] = merchant_match.group(1).upper()

    # ---------------------------------------
    # Sender name (first UPI/DR/.../<NAME>)
    # ---------------------------------------
    sender = re.search(r"/DR/[\d]+/([A-Z ]+)", text)
    if sender:
        meta["sender_name"] = sender.group(1).strip()

    # ---------------------------------------
    # Receiver name (from upi_id: **ANOOP@OKAXIS)
    # ---------------------------------------
    if meta["upi_id"]:
        user_part = meta["upi_id"].split("@")[0]
        meta["receiver_name"] = user_part.upper()

    # ---------------------------------------
    # Reference Number (ICI..., HDFC..., CAN..., SBIN...)
    # ---------------------------------------
    ref_match = re.search(r"\b([A-Z]{2,4}[A-Z0-9]{6,20})\b", text)
    if ref_match:
        meta["reference_no"] = ref_match.group(1)

    # ---------------------------------------
    # Timestamp
    # ---------------------------------------
    time_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4}\s+\d{1,2}:\d{2}:\d{2})", text)
    if time_match:
        meta["timestamp"] = time_match.group(1)

    return meta


# ===== Optional pdfplumber-based extraction utilities =====
# These functions use pdfplumber for embedded text extraction (faster, more accurate than OCR when available)

def _is_new_transaction(line):
    """Check if a line starts a new transaction block."""
    return (
        re.match(r"^\d{2}-\d{2}-\d{4}", line) or
        line.startswith(("UPI/", "IMPS", "RTGS", "MB-", "SI "))
    )


def extract_table_pdfplumber(pdf_path):
    """Extract transactions from a PDF using pdfplumber (embedded text, not OCR).
    
    This is faster and more accurate than OCR when the PDF contains embedded text.
    Returns a pandas DataFrame with columns: Date, Description, Debit, Credit, Balance, Ref No
    """
    try:
        import pdfplumber
        import pandas as pd
    except ImportError:
        raise RuntimeError("pdfplumber and pandas required for this function. Install with: pip install pdfplumber pandas")
    
    with pdfplumber.open(pdf_path) as pdf:
        lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))

    transactions = []
    current = []

    for line in lines:
        if _is_new_transaction(line):
            if current:
                transactions.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        transactions.append(current)

    parsed = []
    for block in transactions:
        text = " ".join(block)

        # Date
        date = re.search(r"\d{2}-\d{2}-\d{4}", text)
        date = date.group() if date else ""

        # Debit / Credit / Balance
        money = re.findall(r"\d[\d,]*\.\d{2}", text)

        debit = credit = balance = ""

        if len(money) >= 2:
            # usually last is balance
            balance = money[-1]

            # previous is debit (if UPI/DR)
            if "UPI/DR" in text or "IMPS-DR" in text or "MB-IMPS-DR" in text:
                debit = money[-2]
                credit = "0"
            else:
                credit = money[-2]
                debit = "0"

        # Reference number: the long number
        ref = ""
        refmatch = re.search(r"\b\d{6,15}\b", text)
        if refmatch:
            ref = refmatch.group()

        # Description (text without date and amounts)
        desc = text.replace(date, "")
        desc = desc.replace(debit, "").replace(credit, "").replace(balance, "").strip()

        parsed.append({
            "Date": date,
            "Description": desc,
            "Debit": debit,
            "Credit": credit,
            "Balance": balance,
            "Ref No": ref
        })

    try:
        import pandas as pd
        return pd.DataFrame(parsed)
    except ImportError:
        # Return as list of dicts if pandas not available
        return parsed


def extract_and_save_csv(pdf_path, output_csv=None):
    """Extract transactions from PDF and save to CSV.
    
    Args:
        pdf_path: Path to the PDF file
        output_csv: Output CSV path (default: same name as PDF with .csv extension)
    """
    try:
        import pandas as pd
    except ImportError:
        raise RuntimeError("pandas required for CSV export. Install with: pip install pandas")
    
    if output_csv is None:
        output_csv = pdf_path.replace('.pdf', '.csv')
    
    df = extract_table_pdfplumber(pdf_path)
    df.to_csv(output_csv, index=False)
    print(f"Saved {len(df)} transactions to {output_csv}")
