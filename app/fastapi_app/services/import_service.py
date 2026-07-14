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


ALLOWED_EXTENSIONS = {"pdf", "csv", "xlsx", "xls"}
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "app/static/uploads")


_flask_app = None


def get_flask_app():
    global _flask_app
    if _flask_app is None:
        from app import create_app
        _flask_app = create_app()
    return _flask_app


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
        preview_txns = result.get("preview", {}).get("transactions", [])
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

    def _run_etl_extract(self, file_path: str, job_id: int, wallet_id: int) -> dict:
        """
        Delegate to the existing ETL pipeline for extract + transform phases.
        The pipeline.process() function uses Flask-SQLAlchemy, so we call it
        as a thin wrapper that returns preview data without committing transactions.
        """
        try:
            flask_app = get_flask_app()
            with flask_app.app_context():
                from app.etl import pipeline as etl_pipeline
                result = etl_pipeline.process(file_path, job_id, wallet_id)
                return result
        except Exception as exc:
            raise RuntimeError(f"ETL extraction failed: {exc}") from exc

    def _run_etl_commit(self, file_path: str, job_id: int, wallet_id: int, user_id: int) -> dict:
        """Delegate to ETL commit phase."""
        try:
            flask_app = get_flask_app()
            with flask_app.app_context():
                from app.etl import pipeline as etl_pipeline
                result = etl_pipeline.commit(job_id, wallet_id)
                return result
        except Exception as exc:
            raise RuntimeError(f"ETL commit failed: {exc}") from exc

    def _parse_date(self, value: str | None):
        if not value:
            return None
        try:
            from datetime import date
            return date.fromisoformat(str(value))
        except Exception:
            return None
