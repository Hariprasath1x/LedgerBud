"""Import routes."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.core.config import settings
from app.fastapi_app.schemas.import_job import ImportCommitResponse, ImportJobRead, ImportPreviewResponse
from app.fastapi_app.services.import_service import ALLOWED_EXTENSIONS, ImportService

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.get("", response_model=list[ImportJobRead])
def list_import_jobs(
    limit: int = 20,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return ImportService(session).list_jobs(current_user.id, limit=limit)


@router.get("/{job_id}", response_model=ImportJobRead)
def get_import_job(
    job_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    job = ImportService(session).get_job(current_user.id, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return job


@router.post("/upload", response_model=ImportPreviewResponse)
async def upload_statement(
    wallet_id: int = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: '{ext}'. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Check Content-Length / file size if available upfront
    if file.size is not None and file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb}MB",
        )

    # Stream read file in chunks to prevent unbounded memory consumption
    chunks: list[bytes] = []
    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb}MB",
            )
        chunks.append(chunk)

    if total_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    file_bytes = b"".join(chunks)

    try:
        return ImportService(session).process_upload(
            user_id=current_user.id,
            wallet_id=wallet_id,
            file_bytes=file_bytes,
            original_filename=file.filename,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        if "exceeds" in msg.lower():
            raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/{job_id}/commit", response_model=ImportCommitResponse)
def commit_import(
    job_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        return ImportService(session).commit_import(current_user.id, job_id)
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
