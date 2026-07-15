"""Import service — file upload, ETL orchestration, and commit."""

from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fastapi_app.models.import_job import ImportJob
from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.schemas.import_job import ImportCommitResponse, ImportJobRead, ImportPreviewResponse, ImportPreviewTransaction

from app.etl.extractor import PDFExtractor, CSVExtractor, XLSXExtractor
from app.etl.transformer.normalizer import parse_date, parse_amount, clean_description, determine_transaction_type
from app.etl.transformer.deduplicator import detect_duplicates, NormalizedTransaction
from app.etl.transformer.merchant_resolver import resolve_merchant
from app.fastapi_app.models.wallet import Wallet


ALLOWED_EXTENSIONS = {"pdf", "csv", "xlsx", "xls"}
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "app/static/uploads")





class ImportService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_jobs(self, user_id: int, limit: int = 20) -> list[ImportJob]:
        return list(
            self.session.scalars(
                select(ImportJob)
                .where(ImportJob.user_id == user_id)
                .order_by(ImportJob.created_at.desc())
                .limit(limit)
            ).all()
        )

    def get_job(self, user_id: int, job_id: int) -> ImportJob | None:
        return self.session.scalar(
            select(ImportJob).where(ImportJob.id == job_id, ImportJob.user_id == user_id)
        )

    def process_upload(
        self,
        user_id: int,
        wallet_id: int,
        file_bytes: bytes,
        original_filename: str,
    ) -> ImportPreviewResponse:
        """Save file, run ETL extract + transform, return preview."""
        ext = original_filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, stored_name)

        with open(file_path, "wb") as fh:
            fh.write(file_bytes)

        # Create import job record
        job = ImportJob(
            user_id=user_id,
            wallet_id=wallet_id,
            filename=stored_name,
            original_filename=original_filename,
            file_type=ext,
            status="processing",
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)

        # Run ETL pipeline (Extract + Transform only — no DB write yet)
        try:
            result = self._run_etl_extract(file_path, job.id, wallet_id)
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            self.session.commit()
            raise

        # Store preview data on the job
        preview_txns = result.get("preview", {}).get("sample_transactions", [])
        job.status = "preview"
        job.institution_detected = result.get("institution")
        job.statement_period_start = self._parse_date(result.get("period_start"))
        job.statement_period_end = self._parse_date(result.get("period_end"))
        job.total_records = result.get("total_records", 0)
        job.duplicate_count = result.get("duplicate_count", 0)
        job.failed_count = result.get("failed_count", 0)
        job.preview_data = result.get("preview", {})
        self.session.commit()

        transactions = [
            ImportPreviewTransaction(
                date=str(t.get("date", "")),
                description=t.get("description", ""),
                amount=float(t.get("amount", 0)),
                transaction_type=t.get("transaction_type", "Expense"),
                merchant_name=t.get("merchant_name"),
                category=t.get("category"),
                is_duplicate=t.get("is_duplicate", False),
            )
            for t in preview_txns
        ]

        return ImportPreviewResponse(
            job_id=job.id,
            status=job.status,
            institution=job.institution_detected,
            period_start=str(job.statement_period_start) if job.statement_period_start else None,
            period_end=str(job.statement_period_end) if job.statement_period_end else None,
            total_records=job.total_records,
            unique_count=job.total_records - job.duplicate_count,
            duplicate_count=job.duplicate_count,
            failed_count=job.failed_count,
            transactions=transactions,
        )

    def commit_import(self, user_id: int, job_id: int) -> ImportCommitResponse:
        """Load approved transactions into the database."""
        job = self.get_job(user_id, job_id)
        if not job:
            raise ValueError("Import job not found")
        if job.status not in ("preview", "processing"):
            raise ValueError(f"Job is in state '{job.status}'; cannot commit")

        file_path = os.path.join(UPLOAD_FOLDER, job.filename)
        if not os.path.exists(file_path):
            raise ValueError("Source file not found. Please re-upload the statement.")

        try:
            result = self._run_etl_commit(file_path, job.id, job.wallet_id, user_id)
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            self.session.commit()
            raise

        job.status = "completed"
        job.imported_count = result.get("imported_count", 0)
        job.duplicate_count = result.get("duplicate_count", 0)
        job.total_records = result.get("total_records", 0)
        job.completed_at = datetime.utcnow()
        self.session.commit()

        return ImportCommitResponse(
            job_id=job.id,
            imported_count=job.imported_count,
            duplicate_count=job.duplicate_count,
            total_records=job.total_records,
            status=job.status,
        )

    # --- ETL bridge methods ---

    def _get_extractor(self, file_path: str):
        for ext in [PDFExtractor(), CSVExtractor(), XLSXExtractor()]:
            if ext.can_handle(file_path):
                return ext
        return None

    def _transform_transaction(self, raw_txn) -> NormalizedTransaction | None:
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
        
        _, merchant_name = resolve_merchant(description, {})
        
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

    def _get_existing_fingerprints(self, wallet_id: int) -> list:
        txns = self.session.scalars(select(Transaction).where(Transaction.wallet_id == wallet_id)).all()
        return [
            {'date': t.transaction_date.isoformat(), 'amount': str(t.amount), 'description': t.notes or t.merchant_name}
            for t in txns
        ]

    def _run_etl_extract(self, file_path: str, job_id: int, wallet_id: int) -> dict:
        """Extract and transform without saving."""
        extractor = self._get_extractor(file_path)
        if not extractor:
            raise ValueError(f"No extractor available for file: {file_path}")
        
        ext_res = extractor.extract(file_path)
        if not ext_res.success and not ext_res.transactions:
            raise RuntimeError("; ".join(ext_res.errors))
        
        normalized = []
        failed = 0
        for raw in ext_res.transactions:
            try:
                norm = self._transform_transaction(raw)
                if norm:
                    normalized.append(norm)
                else:
                    failed += 1
            except Exception:
                failed += 1
                
        existing = self._get_existing_fingerprints(wallet_id)
        unique_txns, dup_txns = detect_duplicates(normalized, existing)
        
        meta = ext_res.metadata
        
        sample = []
        for txn in unique_txns[:10]:
            sample.append({
                'date': txn.date.isoformat() if txn.date else '',
                'description': txn.description,
                'amount': str(txn.amount),
                'transaction_type': txn.type.capitalize() if txn.type else 'Expense',
                'merchant_name': txn.merchant_name_raw,
                'category': None,
                'is_duplicate': False,
            })
            
        return {
            'institution': meta.institution,
            'period_start': meta.statement_period_start.isoformat() if meta.statement_period_start else None,
            'period_end': meta.statement_period_end.isoformat() if meta.statement_period_end else None,
            'total_records': len(ext_res.transactions),
            'unique_count': len(unique_txns),
            'duplicate_count': len(dup_txns),
            'failed_count': failed,
            'preview': {'sample_transactions': sample}
        }

    def _run_etl_commit(self, file_path: str, job_id: int, wallet_id: int, user_id: int) -> dict:
        """Extract, transform, and load unique transactions to database."""
        extractor = self._get_extractor(file_path)
        if not extractor:
            raise ValueError("No extractor available")
            
        ext_res = extractor.extract(file_path)
        
        normalized = []
        for raw in ext_res.transactions:
            try:
                norm = self._transform_transaction(raw)
                if norm:
                    normalized.append(norm)
            except Exception:
                pass
                
        existing = self._get_existing_fingerprints(wallet_id)
        unique_txns, dup_txns = detect_duplicates(normalized, existing)
        
        imported_count = 0
        for norm in unique_txns:
            try:
                txn = Transaction(
                    user_id=user_id,
                    wallet_id=wallet_id,
                    merchant_name=norm.merchant_name_raw or norm.description[:100],
                    category=None,
                    amount=norm.amount,
                    transaction_type=norm.type.capitalize() if norm.type else "Expense",
                    notes=norm.description,
                    transaction_date=norm.date,
                    is_transfer=False
                )
                self.session.add(txn)
                imported_count += 1
            except Exception:
                pass
                
        if unique_txns:
            wallet = self.session.scalar(select(Wallet).where(Wallet.id == wallet_id))
            if wallet:
                last_balance = [t.balance_after for t in unique_txns if t.balance_after]
                if last_balance:
                    wallet.balance = last_balance[-1]
                    self.session.add(wallet)
                    
        self.session.flush()
        
        return {
            'imported_count': imported_count,
            'duplicate_count': len(dup_txns),
            'total_records': len(ext_res.transactions)
        }

    def _parse_date(self, value: str | None):
        if not value:
            return None
        try:
            from datetime import date
            return date.fromisoformat(str(value))
        except Exception:
            return None
