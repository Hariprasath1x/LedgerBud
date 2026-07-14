"""Bank Statement Ingestion Workflow — LedgerBud."""

import streamlit as st
import pandas as pd
from ui.api_client import api_client
from ui.formatters import format_currency, format_date
from ui.components.error_banner import render_error_banner

st.title("Statement Ingestion")
st.markdown("Import PDF/CSV bank statements directly into wallet transaction records.")

# Retrieve wallets for forms
try:
    wallets = api_client.list_wallets()
except Exception as e:
    render_error_banner(e, "retrieving active wallets")
    st.stop()

# Set up state storage for import process
if "import_preview" not in st.session_state:
    st.session_state.import_preview = None

# Grid: Upload Section (Left) and Job History (Right)
col_upload, col_history = st.columns([3, 2])

with col_upload:
    st.subheader("📥 Upload Statement")
    
    if not wallets:
        st.warning("Please configure at least one active wallet before importing statements.")
    else:
        wallet_options = {f"{w['wallet_name']} ({w['wallet_type'].title()})": w["id"] for w in wallets}
        target_wallet = st.selectbox("Import to Wallet", list(wallet_options.keys()))
        
        uploaded_file = st.file_uploader(
            "Select Statement File (PDF, CSV, XLSX, XLS)",
            type=["pdf", "csv", "xlsx", "xls"],
            help="Limit 16MB. Ensure format matches institution layouts."
        )

        if uploaded_file is not None:
            if st.button("Process & Parse Statement", type="primary", use_container_width=True):
                with st.status("Ingesting file...", expanded=True) as status_indicator:
                    try:
                        status_indicator.write("Uploading file to server...")
                        file_bytes = uploaded_file.read()
                        
                        status_indicator.write("Parsing bank transaction records...")
                        preview = api_client.upload_statement(
                            wallet_id=wallet_options[target_wallet],
                            filename=uploaded_file.name,
                            file_bytes=file_bytes
                        )
                        
                        st.session_state.import_preview = preview
                        status_indicator.update(label="Parsing complete!", state="complete", expanded=False)
                        st.success("File processed. Review the extracted data below.")
                    except Exception as exc:
                        status_indicator.update(label="Processing failed.", state="error")
                        render_error_banner(exc, "processing statement upload")

with col_history:
    st.subheader("🕒 Previous Import Jobs")
    try:
        jobs = api_client.list_import_jobs()
        if not jobs:
            st.info("No import history found.")
        else:
            j_df = pd.DataFrame(jobs)
            j_df = j_df[["id", "original_filename", "status", "total_records", "imported_count", "created_at"]]
            j_df.columns = ["Job ID", "Filename", "Status", "Records Count", "Imported Count", "Date Ingested"]
            j_df["Date Ingested"] = pd.to_datetime(j_df["Date Ingested"]).dt.strftime("%d %b %Y %H:%M")
            st.dataframe(j_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_error_banner(exc, "retrieving import history")

st.divider()

# Active Preview Section
if st.session_state.import_preview:
    preview = st.session_state.import_preview
    job_id = preview.get("job_id")
    
    st.subheader("🔍 Review Transactions & Confirm Import")
    
    # Render metadata metrics
    col_t, col_u, col_d, col_f = st.columns(4)
    with col_t:
        st.metric("Total Extracted", preview.get("total_records", 0))
    with col_u:
        st.metric("Unique Records", preview.get("unique_count", 0))
    with col_d:
        st.metric("Duplicates Flagged", preview.get("duplicate_count", 0), delta_color="inverse")
    with col_f:
        st.metric("Failed Ingests", preview.get("failed_count", 0), delta_color="inverse")

    st.write(f"**Institution Detected:** {preview.get('institution') or 'Generic Provider'} "
             f"| **Statement Period:** {format_date(preview.get('period_start'))} - {format_date(preview.get('period_end'))}")

    # Render Preview Table
    txns = preview.get("transactions", [])
    if not txns:
        st.warning("No valid transactions found in statement.")
    else:
        df_preview = pd.DataFrame(txns)
        # Select and format columns
        df_preview = df_preview[["date", "description", "amount", "transaction_type", "merchant_name", "category", "is_duplicate"]]
        df_preview.columns = ["Date", "Description", "Amount", "Type", "Resolved Merchant", "Resolved Category", "Duplicate?"]
        
        column_config = {
            "Date": st.column_config.TextColumn("Date"),
            "Description": st.column_config.TextColumn("Description"),
            "Amount": st.column_config.NumberColumn("Amount (INR)", format="₹%.2f"),
            "Type": st.column_config.TextColumn("Type"),
            "Resolved Merchant": st.column_config.TextColumn("Resolved Merchant"),
            "Resolved Category": st.column_config.TextColumn("Resolved Category"),
            "Duplicate?": st.column_config.CheckboxColumn("Duplicate?"),
        }
        
        st.dataframe(
            df_preview,
            column_config=column_config,
            use_container_width=True,
            hide_index=True
        )

        col_cancel, col_confirm = st.columns(2)
        with col_cancel:
            if st.button("Discard Ingestion", use_container_width=True):
                st.session_state.import_preview = None
                st.rerun()
                
        with col_confirm:
            if st.button("Confirm Ingestion to Database", type="primary", use_container_width=True):
                with st.spinner("Writing statement rows to database..."):
                    try:
                        commit_res = api_client.commit_import(job_id)
                        st.success(f"Successfully imported {commit_res.get('imported_count')} transactions! "
                                   f"({commit_res.get('duplicate_count')} duplicate records skipped.)")
                        st.session_state.import_preview = None
                        st.rerun()
                    except Exception as exc:
                        render_error_banner(exc, "committing imported transactions")
