"""
CSV Statement Extractor
"""
import csv
import logging
from pathlib import Path
from typing import List

from .base import BaseExtractor, ExtractionResult, RawTransaction, StatementMetadata

logger = logging.getLogger(__name__)

DATE_HEADERS = ['date', 'txn date', 'transaction date', 'value date', 'posting date']
DESC_HEADERS = ['description', 'narration', 'particulars', 'details', 'remarks']
DEBIT_HEADERS = ['debit', 'withdrawal', 'dr', 'debit amount', 'withdrawals']
CREDIT_HEADERS = ['credit', 'deposit', 'cr', 'credit amount', 'deposits']
BALANCE_HEADERS = ['balance', 'closing balance', 'running balance']
REF_HEADERS = ['ref no', 'reference', 'chq no', 'reference no', 'transaction id', 'ref']
AMOUNT_HEADERS = ['amount', 'transaction amount']


class CSVExtractor(BaseExtractor):

    def can_handle(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == '.csv'

    def extract(self, file_path: str) -> ExtractionResult:
        result = ExtractionResult()
        result.metadata = StatementMetadata()

        try:
            with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                # Try to sniff delimiter
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
                except Exception:
                    dialect = csv.excel

                reader = csv.DictReader(f, dialect=dialect)
                headers = [h.lower().strip() for h in (reader.fieldnames or [])]

                col_map = self._map_columns(headers)

                if 'date' not in col_map or 'description' not in col_map:
                    result.errors.append('Could not detect date and description columns in CSV.')
                    result.success = False
                    return result

                for row in reader:
                    txn = self._parse_row(row, col_map, headers)
                    if txn:
                        result.transactions.append(txn)

        except Exception as e:
            logger.exception(f'CSV extraction failed for {file_path}')
            result.errors.append(f'CSV extraction error: {str(e)}')
            result.success = False

        return result

    def _map_columns(self, headers: List[str]) -> dict:
        col_map = {}
        for idx, header in enumerate(headers):
            h = header.lower().strip()
            if any(d in h for d in DATE_HEADERS) and 'date' not in col_map:
                col_map['date'] = header
            elif any(d in h for d in DESC_HEADERS) and 'description' not in col_map:
                col_map['description'] = header
            elif any(d in h for d in DEBIT_HEADERS) and 'debit' not in col_map:
                col_map['debit'] = header
            elif any(d in h for d in CREDIT_HEADERS) and 'credit' not in col_map:
                col_map['credit'] = header
            elif any(d in h for d in BALANCE_HEADERS) and 'balance' not in col_map:
                col_map['balance'] = header
            elif any(d in h for d in REF_HEADERS) and 'reference' not in col_map:
                col_map['reference'] = header
            elif any(d in h for d in AMOUNT_HEADERS) and 'amount' not in col_map:
                col_map['amount'] = header
        return col_map

    def _parse_row(self, row: dict, col_map: dict, headers: List[str]) -> RawTransaction:
        def get(key):
            col = col_map.get(key)
            return str(row.get(col, '')).strip() if col else ''

        date_val = get('date')
        desc_val = get('description')

        if not date_val or not desc_val:
            return None

        skip_keywords = ['total', 'opening balance', 'closing balance', 'opening', 'closing']
        if any(k in desc_val.lower() for k in skip_keywords):
            return None

        return RawTransaction(
            date=date_val,
            description=desc_val,
            debit=get('debit') or None,
            credit=get('credit') or None,
            amount=get('amount') or None,
            balance=get('balance') or None,
            reference_no=get('reference') or None,
        )
