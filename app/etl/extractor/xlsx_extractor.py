"""
XLSX Statement Extractor
"""
import logging
from pathlib import Path
from typing import List, Optional

import openpyxl

from .base import BaseExtractor, ExtractionResult, RawTransaction, StatementMetadata

logger = logging.getLogger(__name__)

DATE_HEADERS = ['date', 'txn date', 'transaction date', 'value date', 'posting date']
DESC_HEADERS = ['description', 'narration', 'particulars', 'details', 'remarks']
DEBIT_HEADERS = ['debit', 'withdrawal', 'dr', 'debit amount', 'withdrawals']
CREDIT_HEADERS = ['credit', 'deposit', 'cr', 'credit amount', 'deposits']
BALANCE_HEADERS = ['balance', 'closing balance', 'running balance']
REF_HEADERS = ['ref no', 'reference', 'chq no', 'reference no', 'transaction id']
AMOUNT_HEADERS = ['amount', 'transaction amount']


class XLSXExtractor(BaseExtractor):

    def can_handle(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in ('.xlsx', '.xls')

    def extract(self, file_path: str) -> ExtractionResult:
        result = ExtractionResult()
        result.metadata = StatementMetadata()

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active

            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                result.errors.append('XLSX file is empty.')
                result.success = False
                return result

            header_idx, col_map = self._find_header(rows)
            if header_idx is None:
                result.errors.append('Could not detect header row in XLSX.')
                result.success = False
                return result

            for row in rows[header_idx + 1:]:
                txn = self._parse_row(row, col_map)
                if txn:
                    result.transactions.append(txn)

        except Exception as e:
            logger.exception(f'XLSX extraction failed for {file_path}')
            result.errors.append(f'XLSX extraction error: {str(e)}')
            result.success = False

        return result

    def _find_header(self, rows):
        for idx, row in enumerate(rows[:15]):
            if not row:
                continue
            row_str = [str(cell).lower().strip() if cell else '' for cell in row]
            has_date = any(any(h in cell for h in DATE_HEADERS) for cell in row_str)
            has_desc = any(any(h in cell for h in DESC_HEADERS) for cell in row_str)
            if has_date and has_desc:
                col_map = {}
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

    def _parse_row(self, row, col_map):
        def get(key):
            idx = col_map.get(key)
            if idx is not None and idx < len(row):
                val = row[idx]
                return str(val).strip() if val is not None else ''
            return ''

        date_val = get('date')
        desc_val = get('description')
        if not date_val or not desc_val:
            return None

        skip_keywords = ['total', 'opening balance', 'closing balance']
        if any(k in str(desc_val).lower() for k in skip_keywords):
            return None

        return RawTransaction(
            date=str(date_val),
            description=str(desc_val),
            debit=get('debit') or None,
            credit=get('credit') or None,
            amount=get('amount') or None,
            balance=get('balance') or None,
            reference_no=get('reference') or None,
        )
