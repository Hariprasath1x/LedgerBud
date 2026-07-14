"""Transaction Management Workspace — LedgerBud."""

import streamlit as st
import pandas as pd
from datetime import date
from ui.api_client import api_client
from ui.components.tables import render_transactions_table
from ui.components.error_banner import render_error_banner

# Standard categories for form selection
EXPENSE_CATEGORIES = [
    "Food & Dining", "Groceries", "Shopping", "Entertainment", "Travel",
    "Utilities", "Healthcare", "Education", "Investments", "Insurance",
    "Loan Repayment", "Credit Card", "Rent", "Transfers", "Miscellaneous"
]
INCOME_CATEGORIES = [
    "Salary", "Interest", "Rental Income", "Refunds", "Freelance", "Other Income"
]
ALL_CATEGORIES = sorted(EXPENSE_CATEGORIES + INCOME_CATEGORIES)


@st.dialog("Add Transaction")
def show_add_dialog(wallets):
    """Native modal dialog to create a transaction."""
    with st.form("add_txn_form", clear_on_submit=True):
        wallet_options = {f"{w['wallet_name']} ({w['wallet_type'].title()})": w["id"] for w in wallets}
        selected_wallet = st.selectbox("Wallet", list(wallet_options.keys()))
        
        merchant = st.text_input("Merchant / Payee Name", placeholder="e.g. Amazon, Salary Account")
        txn_type = st.segmented_control("Transaction Type", ["Expense", "Income"], default="Expense")
        
        # Categorize depending on type selection
        cats = EXPENSE_CATEGORIES if txn_type == "Expense" else INCOME_CATEGORIES
        category = st.selectbox("Category", cats)
        
        amount = st.number_input("Amount (INR)", min_value=0.01, format="%.2f", step=10.0)
        txn_date = st.date_input("Transaction Date", value=date.today())
        notes = st.text_area("Notes (Optional)", placeholder="Add context...")

        submit = st.form_submit_button("Save Transaction", use_container_width=True)
        if submit:
            if not merchant:
                st.error("Merchant name is required.")
            else:
                try:
                    api_client.create_transaction(
                        wallet_id=wallet_options[selected_wallet],
                        merchant_name=merchant,
                        category=category,
                        amount=amount,
                        transaction_type=txn_type,
                        transaction_date=str(txn_date),
                        notes=notes
                    )
                    st.success("Transaction created!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error creating transaction: {exc}")


@st.dialog("Edit Transaction")
def show_edit_dialog(wallets, txn):
    """Native modal dialog to edit a transaction."""
    with st.form("edit_txn_form"):
        wallet_options = {f"{w['wallet_name']} ({w['wallet_type'].title()})": w["id"] for w in wallets}
        
        # Determine starting index for wallet selectbox
        wallet_names = list(wallet_options.keys())
        default_w_idx = 0
        for idx, name in enumerate(wallet_names):
            if wallet_options[name] == txn.get("wallet_id"):
                default_w_idx = idx
                break

        selected_wallet = st.selectbox("Wallet", wallet_names, index=default_w_idx)
        merchant = st.text_input("Merchant / Payee Name", value=txn.get("merchant_name", ""))
        txn_type = st.segmented_control("Transaction Type", ["Expense", "Income"], default=txn.get("transaction_type", "Expense"))
        
        # Determine category list & index
        cats = EXPENSE_CATEGORIES if txn_type == "Expense" else INCOME_CATEGORIES
        default_cat_idx = 0
        if txn.get("category") in cats:
            default_cat_idx = cats.index(txn.get("category"))
        category = st.selectbox("Category", cats, index=default_cat_idx)
        
        amount = st.number_input("Amount (INR)", min_value=0.01, value=float(txn.get("amount", 0.0)), format="%.2f", step=10.0)
        
        # Parse default date
        from datetime import datetime
        try:
            default_date = datetime.strptime(txn.get("transaction_date", ""), "%Y-%m-%d").date()
        except Exception:
            default_date = date.today()
            
        txn_date = st.date_input("Transaction Date", value=default_date)
        notes = st.text_area("Notes", value=txn.get("notes") or "")

        submit = st.form_submit_button("Update Transaction", use_container_width=True)
        if submit:
            if not merchant:
                st.error("Merchant name is required.")
            else:
                try:
                    payload = {
                        "wallet_id": wallet_options[selected_wallet],
                        "merchant_name": merchant,
                        "category": category,
                        "amount": amount,
                        "transaction_type": txn_type,
                        "transaction_date": str(txn_date),
                        "notes": notes
                    }
                    api_client.update_transaction(txn.get("id"), payload)
                    st.success("Transaction updated!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error updating transaction: {exc}")


@st.dialog("Delete Transaction")
def show_delete_dialog(txn):
    """Prompt user for confirmation before deletion."""
    st.write(f"Are you sure you want to delete the transaction of **₹{txn.get('amount'):,.2f}** at **{txn.get('merchant_name')}**?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete", type="primary", use_container_width=True):
            try:
                api_client.delete_transaction(txn.get("id"))
                st.success("Deleted successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to delete: {exc}")
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


st.title("Transaction Management")
st.markdown("Monitor, filter, and modify transaction records.")

# Retrieve wallets
try:
    wallets = api_client.list_wallets()
except Exception as e:
    render_error_banner(e, "retrieving active wallets")
    st.stop()

# Filters grid layout
col_search, col_cat, col_type = st.columns([2, 1, 1])

with col_search:
    search_q = st.text_input("Search Merchant / Notes", placeholder="e.g. Amazon, Uber...")

with col_cat:
    category_q = st.selectbox("Category Filter", ["All Categories"] + ALL_CATEGORIES)

with col_type:
    type_q = st.selectbox("Type Filter", ["All Types", "Expense", "Income"])

# Determine final query parameters — use .get() for safe access before session is initialized
wallet_id = st.session_state.get("active_wallet_id", None)
search = search_q if search_q else None
category = category_q if category_q != "All Categories" else None
transaction_type = type_q if type_q != "All Types" else None

# Action Controls
col_add, col_space = st.columns([1, 4])
with col_add:
    if st.button("➕ Add Transaction", use_container_width=True):
        if not wallets:
            st.warning("Please create a wallet first.")
        else:
            show_add_dialog(wallets)

# Fetch transactions
try:
    # Set limit high for direct visualization
    res = api_client.list_transactions(
        wallet_id=wallet_id,
        search=search,
        category=category,
        transaction_type=transaction_type,
        per_page=100
    )
    transactions = res.get("items", [])
except Exception as e:
    render_error_banner(e, "retrieving transactions list")
    st.stop()

if not transactions:
    st.info("No transactions match the selected filters.")
else:
    # Use interactive selection to edit/delete
    df = pd.DataFrame(transactions)
    df_display = df[["id", "transaction_date", "merchant_name", "category", "transaction_type", "amount", "notes"]].copy()
    df_display["transaction_date"] = pd.to_datetime(df_display["transaction_date"])
    
    # Configure columns nicely
    column_config = {
        "id": st.column_config.NumberColumn("ID", disabled=True, format="%d"),
        "transaction_date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
        "merchant_name": st.column_config.TextColumn("Merchant / Payee"),
        "category": st.column_config.TextColumn("Category"),
        "transaction_type": st.column_config.TextColumn("Type"),
        "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
        "notes": st.column_config.TextColumn("Notes"),
    }
    
    selection = st.dataframe(
        df_display,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # Check selection indices
    selected_rows = selection.get("selection", {}).get("rows", [])
    if selected_rows:
        selected_idx = selected_rows[0]
        selected_txn = transactions[selected_idx]
        
        st.write("---")
        st.write(f"**Selected Action Context: ID #{selected_txn.get('id')}**")
        col_edit, col_del, _ = st.columns([1, 1, 3])
        with col_edit:
            if st.button("✏️ Edit Selected", use_container_width=True):
                show_edit_dialog(wallets, selected_txn)
        with col_del:
            if st.button("🗑️ Delete Selected", use_container_width=True):
                show_delete_dialog(selected_txn)
