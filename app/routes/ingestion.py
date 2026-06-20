"""
Ingestion Routes — Smart Statement Ingestion Engine
"""
import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import ImportJob, Wallet, AuditLog
from app.etl import pipeline
from datetime import datetime

ingestion_bp = Blueprint('ingestion', __name__, url_prefix='/ingestion')

ALLOWED_EXTENSIONS = {'pdf', 'csv', 'xlsx', 'xls'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@ingestion_bp.route('/')
def index():
    wallets = Wallet.query.filter_by(is_active=True).all()
    recent_jobs = ImportJob.query.order_by(ImportJob.created_at.desc()).limit(10).all()
    return render_template('ingestion.html', wallets=wallets, recent_jobs=recent_jobs)


@ingestion_bp.route('/upload', methods=['POST'])
def upload():
    """Handle file upload and trigger ETL extraction phase."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    file = request.files['file']
    wallet_id = request.form.get('wallet_id', type=int)

    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type. Upload PDF, CSV, or XLSX.'}), 400

    if not wallet_id:
        return jsonify({'success': False, 'error': 'Please select a wallet'}), 400

    # Save file
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[-1].lower()
    stored_filename = f'{uuid.uuid4().hex}.{ext}'
    file_path = os.path.join(upload_folder, stored_filename)
    file.save(file_path)

    # Create import job
    import_job = ImportJob(
        filename=stored_filename,
        original_filename=original_filename,
        file_type=ext,
        wallet_id=wallet_id,
        status='pending',
    )
    db.session.add(import_job)
    db.session.commit()

    # Write audit log
    audit = AuditLog(
        action='STATEMENT_UPLOADED',
        entity_type='import_job',
        entity_id=import_job.id,
        import_job_id=import_job.id,
        meta_data={'filename': original_filename, 'wallet_id': wallet_id},
    )
    db.session.add(audit)
    db.session.commit()

    # Run ETL extraction + transform (synchronous for now)
    result = pipeline.process(file_path, import_job.id, wallet_id)

    if result.get('success'):
        return jsonify({
            'success': True,
            'import_job_id': import_job.id,
            'total_records': result.get('total_records', 0),
            'unique_count': result.get('unique_count', 0),
            'duplicate_count': result.get('duplicate_count', 0),
            'failed_count': result.get('failed_count', 0),
            'institution': result.get('institution'),
            'period_start': result.get('period_start'),
            'period_end': result.get('period_end'),
            'preview': result.get('preview', {}),
        })
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Processing failed')}), 500


@ingestion_bp.route('/preview/<int:job_id>')
def preview(job_id):
    """Get preview data for an import job."""
    job = ImportJob.query.get_or_404(job_id)
    return jsonify({
        'success': True,
        'job': job.to_dict(),
        'preview_data': job.preview_data or {},
    })


@ingestion_bp.route('/commit/<int:job_id>', methods=['POST'])
def commit(job_id):
    """Commit the import — Load step."""
    job = ImportJob.query.get_or_404(job_id)

    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, job.filename)

    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'Original file not found. Please re-upload.'}), 400

    result = pipeline.commit(job_id, job.wallet_id)

    if result.get('success'):
        return jsonify({
            'success': True,
            'imported_count': result.get('imported_count', 0),
            'duplicate_count': result.get('duplicate_count', 0),
            'total_records': result.get('total_records', 0),
        })
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Import failed')}), 500


@ingestion_bp.route('/history')
def history():
    """Import history page."""
    jobs = ImportJob.query.order_by(ImportJob.created_at.desc()).all()
    return render_template('import_history.html', jobs=jobs)


@ingestion_bp.route('/job/<int:job_id>')
def job_detail(job_id):
    """Job detail JSON."""
    job = ImportJob.query.get_or_404(job_id)
    return jsonify(job.to_dict())
