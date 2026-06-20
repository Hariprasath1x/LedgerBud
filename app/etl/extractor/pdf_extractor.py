"""
PDF Statement Extractor
Uses pdfplumber to extract transaction tables from bank statement PDFs.
Designed to be bank-agnostic with intelligent pattern detection.
"""
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from datetime import date

import pdfplumber

from .base import BaseExtractor, ExtractionResult, RawTransaction, StatementMetadata

logger = logging.getLogger(__name__)


# Bank detection patterns: (institution_name, list_of_header_keywords)
BANK_PATTERNS = {
    'SBI': ['state bank of india', 'sbi', 'state bank'],
    'HDFC': ['hdfc bank', 'hdfc'],
    'ICICI': ['icici bank', 'icici'],
    'Axis Bank': ['axis bank', 'axis'],
    'Canara Bank': ['canara bank', 'canara'],
    'Indian Bank': ['indian bank'],
    'Union Bank': ['union bank of india', 'union bank'],
    'Bank of Baroda': ['bank of baroda', 'baroda', 'bob'],
    'Kotak Mahindra': ['kotak mahindra', 'kotak'],
    'Yes Bank': ['yes bank'],
    'Punjab National Bank': ['punjab national bank', 'pnb'],
    'Bank of India': ['bank of india'],
    'IndusInd Bank': ['indusind bank', 'indusind'],
    'Federal Bank': ['federal bank'],
    'IDFC First': ['idfc first', 'idfc'],
    'RBL Bank': ['rbl bank'],
}

# Common column header patterns across banks
DATE_HEADERS = ['date', 'txn date', 'transaction date', 'value date', 'posting date', 'trans date', 'tran date']
DESC_HEADERS = ['description', 'narration', 'particulars', 'details', 'transaction details',
                'remarks', 'transaction narration', 'trans details', 'transaction remarks']
DEBIT_HEADERS = ['debit', 'withdrawal', 'dr', 'debit amount', 'withdrawals', 'dr amount', 'amount debit']
CREDIT_HEADERS = ['credit', 'deposit', 'cr', 'credit amount', 'deposits', 'cr amount', 'amount credit']
BALANCE_HEADERS = ['balance', 'closing balance', 'running balance', 'available balance', 'bal']
REF_HEADERS = ['ref no', 'reference', 'chq no', 'cheque no', 'reference no', 'transaction id', 'ref', 'txn id']
AMOUNT_HEADERS = ['amount', 'transaction amount', 'txn amount']


class PDFExtractor(BaseExtractor):
    """Extracts transactions from bank statement PDFs using pdfplumber."""

    def can_handle(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == '.pdf'

    def extract(self, file_path: str) -> ExtractionResult:
        result = ExtractionResult()
        raw_text_parts = []

        try:
            with pdfplumber.open(file_path) as pdf:
                all_tables = []

                for page_num, page in enumerate(pdf.pages):
                    # Collect all text for metadata detection
                    page_text = page.extract_text() or ''
                    raw_text_parts.append(page_text)

                    # Extract tables from this page
                    tables = page.extract_tables({
                        'vertical_strategy': 'lines',
                        'horizontal_strategy': 'lines',
                        'snap_tolerance': 3,
                        'join_tolerance': 3,
                    })

                    if not tables:
                        # Try text-based extraction as fallback
                        tables = page.extract_tables()

                    for table in tables:
                        if table:
                            all_tables.append(table)

                full_text = '\n'.join(raw_text_parts)

                # Detect institution from text
                result.metadata.institution = self._detect_institution(full_text)
                result.metadata.raw_text = full_text[:2000]

                # Extract account metadata
                self._extract_metadata(full_text, result.metadata)

                # Process tables to find transaction data
                for table in all_tables:
                    transactions = self._process_table(table)
                    result.transactions.extend(transactions)

                # If no tables found, attempt text-based line parsing
                if not result.transactions:
                    result.transactions = self._extract_from_text(full_text)

                if not result.transactions:
                    result.errors.append('No transaction data could be extracted from this PDF. '
                                         'Please ensure it is a digital (not scanned) bank statement.')
                    result.success = False

        except Exception as e:
            logger.exception(f'PDF extraction failed for {file_path}')
            result.errors.append(f'PDF extraction error: {str(e)}')
            result.success = False

        return result

    def _detect_institution(self, text: str) -> Optional[str]:
        """Detect bank/institution name from statement text."""
        text_lower = text.lower()
        for institution, keywords in BANK_PATTERNS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return institution
        return None

    def _extract_metadata(self, text: str, metadata: StatementMetadata):
        """Extract account number, period, etc. from statement text."""
        # Account number patterns
        acc_patterns = [
            r'account\s*(?:number|no\.?|#)\s*[:\-]?\s*([A-Z0-9\-]{6,20})',
            r'a/c\s*(?:no\.?|#)?\s*[:\-]?\s*([A-Z0-9\-]{6,20})',
            r'acct\s*(?:no\.?|#)?\s*[:\-]?\s*([A-Z0-9\-]{6,20})',
        ]
        for pattern in acc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata.account_number = match.group(1).strip()
                break

        # Statement period patterns
        period_patterns = [
            r'from\s+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s+to\s+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'period\s*[:\-]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*(?:to|-)\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'statement\s+period\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*(?:to|-)\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        ]
        for pattern in period_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                from app.etl.transformer.normalizer import parse_date
                metadata.statement_period_start = parse_date(match.group(1))
                metadata.statement_period_end = parse_date(match.group(2))
                break

    def _process_table(self, table: List[List]) -> List[RawTransaction]:
        """Process a raw extracted table into RawTransaction objects."""
        if not table or len(table) < 2:
            return []

        # Find header row
        header_row_idx, col_map = self._find_header_row(table)
        if header_row_idx is None or not col_map:
            return []

        transactions = []
        for row in table[header_row_idx + 1:]:
            if not row:
                continue
            txn = self._parse_row(row, col_map)
            if txn:
                transactions.append(txn)

        return transactions

    def _find_header_row(self, table: List[List]) -> Tuple[Optional[int], Dict[str, int]]:
        """Find the header row index and build column mapping."""
        for idx, row in enumerate(table[:10]):  # Check first 10 rows
            if not row:
                continue

            col_map = {}
            row_str = [str(cell).lower().strip() if cell else '' for cell in row]

            # Check if this row has date + description columns
            has_date = any(any(h in cell for h in DATE_HEADERS) for cell in row_str)
            has_desc = any(any(h in cell for h in DESC_HEADERS) for cell in row_str)

            if has_date and has_desc:
                for col_idx, cell in enumerate(row_str):
                    if any(h in cell for h in DATE_HEADERS) and 'date' not in col_map:
                        col_map['date'] = col_idx
                    elif any(h in cell for h in DESC_HEADERS) and 'description' not in col_map:
                        col_map['description'] = col_idx
                    elif any(h in cell for h in DEBIT_HEADERS) and 'debit' not in col_map:
                        col_map['debit'] = col_idx
                    elif any(h in cell for h in CREDIT_HEADERS) and 'credit' not in col_map:
                        col_map['credit'] = col_idx
                    elif any(h in cell for h in BALANCE_HEADERS) and 'balance' not in col_map:
                        col_map['balance'] = col_idx
                    elif any(h in cell for h in REF_HEADERS) and 'reference' not in col_map:
                        col_map['reference'] = col_idx
                    elif any(h in cell for h in AMOUNT_HEADERS) and 'amount' not in col_map:
                        col_map['amount'] = col_idx

                if 'date' in col_map and 'description' in col_map:
                    return idx, col_map

        return None, {}

    def _parse_row(self, row: List, col_map: Dict[str, int]) -> Optional[RawTransaction]:
        """Parse a single table row into a RawTransaction."""
        def safe_get(col_key: str) -> str:
            idx = col_map.get(col_key)
            if idx is not None and idx < len(row):
                val = row[idx]
                return str(val).strip() if val else ''
            return ''

        date_val = safe_get('date')
        desc_val = safe_get('description')

        # Skip rows without date and description
        if not date_val or not desc_val:
            return None

        # Skip header-like rows or total rows
        skip_keywords = ['total', 'opening balance', 'closing balance', 'brought forward',
                         'carried forward', 'opening', 'closing']
        if any(k in desc_val.lower() for k in skip_keywords) and not safe_get('debit') and not safe_get('credit'):
            return None

        # Must look like a date
        if not re.search(r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{2}\s+\w{3}\s+\d{4}', date_val):
            return None

        return RawTransaction(
            date=date_val,
            description=desc_val,
            debit=safe_get('debit') or None,
            credit=safe_get('credit') or None,
            amount=safe_get('amount') or None,
            balance=safe_get('balance') or None,
            reference_no=safe_get('reference') or None,
            raw_row=dict(zip(col_map.keys(), [safe_get(k) for k in col_map])),
        )

    def _extract_from_text(self, text: str) -> List[RawTransaction]:
        """Fallback: attempt to extract transactions from raw text lines."""
        transactions = []
        lines = text.split('\n')

        # Pattern: date followed by description and amounts
        date_pattern = re.compile(
            r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{2}\s+\w{3}\s+\d{4})'
        )
        amount_pattern = re.compile(r'[\d,]+\.\d{2}')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            date_match = date_pattern.match(line)
            if not date_match:
                continue

            amounts = amount_pattern.findall(line)
            if not amounts:
                continue

            description = line[date_match.end():].strip()
            description = amount_pattern.sub('', description).strip()

            if len(description) < 3:
                continue

            txn = RawTransaction(
                date=date_match.group(1),
                description=description,
                amount=amounts[0] if amounts else None,
                balance=amounts[-1] if len(amounts) > 1 else None,
            )
            transactions.append(txn)

        return transactions
