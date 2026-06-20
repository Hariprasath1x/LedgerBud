"""
ETL Pipeline Orchestrator
Coordinates Extract → Transform → Load for statement ingestion.
"""
import os
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.extensions import db
from app.models import Transaction, ImportJob, Merchant, Category, AuditLog, Wallet
from .extractor import PDFExtractor, CSVExtractor, XLSXExtractor
from .transformer.normalizer import parse_date, parse_amount, clean_description, determine_transaction_type
from .transformer.deduplicator import detect_duplicates, NormalizedTransaction
from .transformer.merchant_resolver import resolve_merchant

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Full ETL pipeline for statement ingestion.
    Coordinates extraction, transformation, and loading.
    """

    EXTRACTORS = [PDFExtractor(), CSVExtractor(), XLSXExtractor()]

    def __init__(self):
        self._merchant_lookup = None

    def _build_merchant_lookup(self) -> dict:
        """Build a keyword → (merchant_id, canonical_name) lookup dict from DB."""
        lookup = {}
        try:
            merchants = Merchant.query.filter_by(is_verified=True).all()
            for m in merchants:
                keywords = m.keywords or []
                # Always include canonical name as a keyword
                all_keys = [m.canonical_name.lower()] + [k.lower() for k in keywords]
                for keyword in all_keys:
                    if keyword and keyword not in lookup:
                        lookup[keyword] = (m.id, m.canonical_name)
        except Exception as e:
            logger.error(f'Failed to build merchant lookup: {e}')
        return lookup

    def process(self, file_path: str, import_job_id: int, wallet_id: int) -> dict:
        """
        Full pipeline: Extract → Transform → Load.
        Returns a summary dict.
        """
        import_job = ImportJob.query.get(import_job_id)
        if not import_job:
            return {'success': False, 'error': 'Import job not found'}

        try:
            # --- EXTRACT ---
            import_job.status = 'processing'
            db.session.commit()

            extractor = self._get_extractor(file_path)
            if not extractor:
                raise ValueError(f'No extractor available for file: {file_path}')

            extraction_result = extractor.extract(file_path)

            if not extraction_result.success and not extraction_result.transactions:
                import_job.status = 'failed'
                import_job.error_message = '; '.join(extraction_result.errors)
                db.session.commit()
                return {'success': False, 'error': import_job.error_message}

            # Update job with metadata
            meta = extraction_result.metadata
            import_job.institution_detected = meta.institution
            import_job.account_number_detected = meta.account_number
            import_job.statement_period_start = meta.statement_period_start
            import_job.statement_period_end = meta.statement_period_end
            import_job.total_records = len(extraction_result.transactions)
            db.session.commit()

            # --- TRANSFORM ---
            self._merchant_lookup = self._build_merchant_lookup()

            normalized_transactions = []
            failed_count = 0

            for raw_txn in extraction_result.transactions:
                try:
                    norm = self._transform_transaction(raw_txn)
                    if norm:
                        normalized_transactions.append(norm)
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.warning(f'Transform failed for row: {e}')
                    failed_count += 1

            # Deduplication against existing transactions
            existing = self._get_existing_fingerprints(wallet_id)
            unique_transactions, duplicate_transactions = detect_duplicates(
                normalized_transactions, existing
            )

            import_job.duplicate_count = len(duplicate_transactions)
            import_job.failed_count = failed_count

            # Build preview data
            import_job.preview_data = self._build_preview(unique_transactions, extraction_result.metadata)
            import_job.status = 'preview'
            db.session.commit()

            return {
                'success': True,
                'import_job_id': import_job_id,
                'total_records': len(extraction_result.transactions),
                'unique_count': len(unique_transactions),
                'duplicate_count': len(duplicate_transactions),
                'failed_count': failed_count,
                'institution': meta.institution,
                'period_start': meta.statement_period_start.isoformat() if meta.statement_period_start else None,
                'period_end': meta.statement_period_end.isoformat() if meta.statement_period_end else None,
                'preview': import_job.preview_data,
            }

        except Exception as e:
            logger.exception(f'Pipeline failed for import job {import_job_id}')
            if import_job:
                import_job.status = 'failed'
                import_job.error_message = str(e)
                db.session.commit()
            return {'success': False, 'error': str(e)}

    def commit(self, import_job_id: int, wallet_id: int) -> dict:
        """
        Commit extracted transactions to database (Load step).
        Called after user confirms the preview.
        """
        import_job = ImportJob.query.get(import_job_id)
        if not import_job or import_job.status not in ('preview', 'processing'):
            return {'success': False, 'error': 'Invalid import job state'}

        try:
            # Re-run extract + transform (or use cached preview_data)
            file_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'static', 'uploads',
                import_job.filename
            )
            file_path = os.path.normpath(file_path)

            extractor = self._get_extractor(file_path)
            extraction_result = extractor.extract(file_path)

            self._merchant_lookup = self._build_merchant_lookup()

            normalized_transactions = []
            for raw_txn in extraction_result.transactions:
                try:
                    norm = self._transform_transaction(raw_txn)
                    if norm:
                        normalized_transactions.append(norm)
                except Exception:
                    pass

            existing = self._get_existing_fingerprints(wallet_id)
            unique_transactions, duplicate_transactions = detect_duplicates(normalized_transactions, existing)

            # Load
            imported_count = 0
            for norm in unique_transactions:
                try:
                    txn = self._load_transaction(norm, wallet_id, import_job_id)
                    if txn:
                        imported_count += 1
                except Exception as e:
                    logger.warning(f'Load failed for transaction: {e}')

            # Update wallet balance
            wallet = Wallet.query.get(wallet_id)
            if wallet and unique_transactions:
                last_balance = [t.balance_after for t in unique_transactions if t.balance_after]
                if last_balance:
                    wallet.balance = last_balance[-1]
                    db.session.add(wallet)

            import_job.imported_count = imported_count
            import_job.duplicate_count = len(duplicate_transactions)
            import_job.status = 'completed'
            import_job.completed_at = datetime.utcnow()
            db.session.commit()

            # Audit log
            self._write_audit(import_job_id, 'TRANSACTIONS_IMPORTED', {
                'imported': imported_count,
                'duplicates': len(duplicate_transactions),
                'wallet_id': wallet_id,
            })

            return {
                'success': True,
                'imported_count': imported_count,
                'duplicate_count': len(duplicate_transactions),
                'total_records': len(extraction_result.transactions),
            }

        except Exception as e:
            logger.exception(f'Commit failed for import job {import_job_id}')
            if import_job:
                import_job.status = 'failed'
                import_job.error_message = str(e)
                db.session.commit()
            return {'success': False, 'error': str(e)}

    def _get_extractor(self, file_path: str):
        for extractor in self.EXTRACTORS:
            if extractor.can_handle(file_path):
                return extractor
        return None

    def _transform_transaction(self, raw_txn) -> Optional[NormalizedTransaction]:
        """Transform a RawTransaction into a NormalizedTransaction."""
        parsed_date = parse_date(raw_txn.date)
        if not parsed_date:
            return None

        txn_type, amount = determine_transaction_type(
            raw_txn.debit, raw_txn.credit, raw_txn.amount, raw_txn.description
        )

        if not amount or amount <= 0:
            return None

        description = clean_description(raw_txn.description)
        balance = parse_amount(raw_txn.balance) if raw_txn.balance else None

        # Merchant resolution
        merchant_id, merchant_name = resolve_merchant(description, self._merchant_lookup or {})

        return NormalizedTransaction(
            date=parsed_date,
            description=description,
            amount=amount,
            type=txn_type,
            balance_after=balance,
            reference_no=raw_txn.reference_no,
            merchant_name_raw=merchant_name or description[:100],
            raw_date_str=raw_txn.date or '',
        )

    def _load_transaction(self, norm: NormalizedTransaction, wallet_id: int, import_job_id: int):
        """Persist a single normalized transaction to the database."""
        # Resolve merchant_id and category_id
        merchant_id = None
        category_id = None

        if norm.merchant_name_raw:
            merchant_lookup = self._merchant_lookup or {}
            for keyword, (mid, cname) in merchant_lookup.items():
                if keyword in norm.merchant_name_raw.lower():
                    merchant_id = mid
                    break

        if merchant_id:
            merchant = Merchant.query.get(merchant_id)
            if merchant:
                category_id = merchant.category_id

        txn = Transaction(
            wallet_id=wallet_id,
            merchant_id=merchant_id,
            category_id=category_id,
            import_job_id=import_job_id,
            date=norm.date,
            description=norm.description,
            merchant_name_raw=norm.merchant_name_raw,
            amount=norm.amount,
            type=norm.type,
            balance_after=norm.balance_after,
            reference_no=norm.reference_no,
            is_duplicate=False,
            is_manual=False,
        )
        db.session.add(txn)
        db.session.flush()
        return txn

    def _get_existing_fingerprints(self, wallet_id: int) -> list:
        """Fetch existing transactions for duplicate detection."""
        try:
            txns = Transaction.query.filter_by(wallet_id=wallet_id).with_entities(
                Transaction.date, Transaction.amount, Transaction.description
            ).all()
            return [
                {'date': t.date.isoformat() if t.date else '', 'amount': str(t.amount), 'description': t.description}
                for t in txns
            ]
        except Exception:
            return []

    def _build_preview(self, transactions: list, metadata) -> dict:
        """Build preview data for the confirmation step."""
        sample = []
        for txn in transactions[:10]:
            sample.append({
                'date': txn.date.isoformat() if txn.date else '',
                'description': txn.description,
                'amount': str(txn.amount),
                'type': txn.type,
                'merchant': txn.merchant_name_raw,
            })

        return {
            'institution': metadata.institution,
            'account_number': metadata.account_number,
            'period_start': metadata.statement_period_start.isoformat() if metadata.statement_period_start else None,
            'period_end': metadata.statement_period_end.isoformat() if metadata.statement_period_end else None,
            'sample_transactions': sample,
            'total_unique': len(transactions),
        }

    def _write_audit(self, import_job_id: int, action: str, metadata: dict):
        """Write an audit log entry."""
        try:
            log = AuditLog(
                action=action,
                entity_type='import_job',
                entity_id=import_job_id,
                import_job_id=import_job_id,
                metadata=metadata,
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f'Audit log failed: {e}')


# Singleton pipeline instance
pipeline = IngestionPipeline()
