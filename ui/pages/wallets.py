"""Wallet Management Workspace — LedgerBud."""

import streamlit as st
import pandas as pd
from ui.api_client import api_client
from ui.components.error_banner import render_error_banner
from ui.formatters import format_currency


@st.dialog("Create Wallet")
def show_create_wallet_dialog():
    with st.form("create_wallet_form"):
        name = st.text_input("Wallet Name", placeholder="e.g. HDFC Checking")
        w_type = st.selectbox("Wallet Type", ["Bank", "Cash", "UPI", "Credit", "Custom"])
        balance = st.number_input("Starting Balance", min_value=0.0, format="%.2f")
        if st.form_submit_button("Create Wallet", use_container_width=True):
            if not name:
                st.error("Name is required.")
            else:
                try:
                    api_client.create_wallet(name, w_type, balance)
                    st.success("Wallet created.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


@st.dialog("Archive Wallet")
def show_archive_wallet_dialog(wallet):
    st.warning(f"Are you sure you want to archive '{wallet['wallet_name']}'? It will be hidden from the active list but its transactions will be preserved.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Archive", type="primary", use_container_width=True):
            try:
                api_client.archive_wallet(wallet['id'])
                st.success("Wallet archived.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


@st.dialog("Transfer Funds")
def show_transfer_dialog(wallets):
    if len(wallets) < 2:
        st.error("You need at least two active wallets to transfer funds.")
        return
        
    with st.form("transfer_form"):
        wallet_opts = {f"{w['wallet_name']} (₹{w['balance']:,.2f})": w['id'] for w in wallets}
        
        from_w = st.selectbox("From Wallet", list(wallet_opts.keys()), key="from_w")
        to_w = st.selectbox("To Wallet", list(wallet_opts.keys()), key="to_w")
        
        amount = st.number_input("Amount", min_value=0.01, format="%.2f")
        from datetime import date
        t_date = st.date_input("Date", value=date.today())
        notes = st.text_area("Notes", placeholder="e.g. Moved to savings")
        
        if st.form_submit_button("Transfer", use_container_width=True):
            if wallet_opts[from_w] == wallet_opts[to_w]:
                st.error("Cannot transfer to the same wallet.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                try:
                    api_client.transfer_funds(
                        wallet_opts[from_w], 
                        wallet_opts[to_w], 
                        amount, 
                        notes=notes, 
                        transaction_date=str(t_date)
                    )
                    st.success("Transfer complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Transfer failed: {e}")


st.title("Wallets & Accounts")
st.markdown("Manage your accounts, check balances, and perform transfers.")

try:
    with st.spinner("Loading wallets..."):
        wallets = api_client.list_wallets()
        summary = api_client.wallet_summary()
except Exception as e:
    render_error_banner(e, "loading wallets")
    st.stop()

# Header Metrics
col_tot, col_cnt = st.columns(2)
with col_tot:
    st.metric("Total Balance", format_currency(summary.get("total_balance", 0)))
with col_cnt:
    st.metric("Active Wallets", summary.get("total_wallets", 0))

st.divider()

col_add, col_trans, _ = st.columns([1, 1, 3])
with col_add:
    if st.button("➕ Add Wallet", use_container_width=True):
        show_create_wallet_dialog()
with col_trans:
    if st.button("🔄 Transfer Funds", use_container_width=True):
        show_transfer_dialog(wallets)

if not wallets:
    st.info("No active wallets found. Create one to get started.")
else:
    st.subheader("Your Wallets")
    for w in wallets:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{w['wallet_name']}**")
                st.caption(f"Type: {w['wallet_type']}")
            with col2:
                st.write(f"**{format_currency(w['balance'])}**")
            with col3:
                if st.button("Archive", key=f"arch_{w['id']}", use_container_width=True):
                    show_archive_wallet_dialog(w)
