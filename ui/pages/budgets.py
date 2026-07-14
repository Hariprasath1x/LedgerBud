"""Budget Monitoring Workspace — LedgerBud."""

import streamlit as st
from datetime import date
from ui.api_client import api_client
from ui.formatters import format_currency, format_percentage
from ui.components.error_banner import render_error_banner

# Standard categories list
EXPENSE_CATEGORIES = [
    "Food & Dining", "Groceries", "Shopping", "Entertainment", "Travel",
    "Utilities", "Healthcare", "Education", "Investments", "Insurance",
    "Loan Repayment", "Credit Card", "Rent", "Transfers", "Miscellaneous"
]


@st.dialog("Create Budget")
def show_create_dialog():
    """Native form to create a new budget category."""
    with st.form("create_budget_form", clear_on_submit=True):
        name = st.text_input("Budget Name", placeholder="e.g. Grocery Budget")
        category = st.selectbox("Category", EXPENSE_CATEGORIES)
        amount = st.number_input("Limit Amount (INR)", min_value=1.0, format="%.2f", step=500.0)
        period = st.selectbox("Period", ["monthly", "weekly", "yearly"])
        submit = st.form_submit_button("Save Budget", use_container_width=True)

        if submit:
            if not name:
                st.error("Name is required.")
            else:
                try:
                    api_client.create_budget(name, category, amount, period)
                    st.success("Budget created!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")


@st.dialog("Edit Budget")
def show_edit_dialog(budget):
    """Native form to update a budget."""
    with st.form("edit_budget_form"):
        name = st.text_input("Budget Name", value=budget.get("name", ""))
        
        default_cat_idx = 0
        if budget.get("category") in EXPENSE_CATEGORIES:
            default_cat_idx = EXPENSE_CATEGORIES.index(budget.get("category"))
            
        category = st.selectbox("Category", EXPENSE_CATEGORIES, index=default_cat_idx)
        amount = st.number_input("Limit Amount (INR)", min_value=1.0, value=float(budget.get("amount", 0.0)), format="%.2f", step=500.0)
        period = st.selectbox("Period", ["monthly", "weekly", "yearly"], index=["monthly", "weekly", "yearly"].index(budget.get("period", "monthly")))
        
        submit = st.form_submit_button("Update Budget", use_container_width=True)

        if submit:
            if not name:
                st.error("Name is required.")
            else:
                try:
                    payload = {"name": name, "category": category, "amount": amount, "period": period}
                    api_client.update_budget(budget.get("id"), payload)
                    st.success("Budget updated!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")


@st.dialog("Delete Budget")
def show_delete_dialog(budget):
    """Prompt user for confirmation before budget deletion."""
    st.write(f"Are you sure you want to deactivate budget **{budget.get('name')}**?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Deactivate", type="primary", use_container_width=True):
            try:
                api_client.delete_budget(budget.get("id"))
                st.success("Budget deactivated successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to deactivate: {exc}")
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


st.title("Budget Monitoring")
st.markdown("Set expense limit rules on categories and track execution progress.")

# Action control
col_act, _ = st.columns([1, 4])
with col_act:
    if st.button("➕ Create Budget", use_container_width=True):
        show_create_dialog()

# Retrieve active budgets with utilization details
try:
    with st.spinner("Calculating budget allocations..."):
        budgets = api_client.list_budgets()
except Exception as e:
    render_error_banner(e, "retrieving budgets list")
    st.stop()

if not budgets:
    st.info("No budgets configured yet. Create a budget to monitor category expenditures.")
else:
    # Summarize budget execution metrics
    total_budgeted = sum(b.get("amount", 0.0) for b in budgets)
    total_spent = sum(b.get("spent", 0.0) for b in budgets)
    
    col_tb, col_ts, col_tr = st.columns(3)
    with col_tb:
        st.metric("Total Budgeted", format_currency(total_budgeted))
    with col_ts:
        st.metric("Total Spent", format_currency(total_spent))
    with col_tr:
        rem = max(0.0, total_budgeted - total_spent)
        st.metric("Total Remaining", format_currency(rem), delta=f"{format_percentage((total_spent/total_budgeted*100) if total_budgeted > 0 else 0)} used", delta_color="inverse")

    st.divider()

    # Loop through active budgets
    for b in budgets:
        limit = float(b.get("amount", 0.0))
        spent = float(b.get("spent", 0.0))
        remaining = float(b.get("remaining", 0.0))
        pct = float(b.get("utilization_pct", 0.0))
        status = b.get("status", "healthy")

        with st.container(border=True):
            col_info, col_val, col_actions = st.columns([3, 2, 1])

            with col_info:
                st.markdown(f"#### **{b.get('name')}**")
                st.caption(f"Category: **{b.get('category')}** | Period: {b.get('period').title()}")
                
                # Dynamic indicator messages
                if status == "exceeded":
                    st.error(f"🚨 Budget exceeded by {format_currency(spent - limit)}!")
                elif status == "warning":
                    st.warning("⚠️ High utilization. Limit approaching.")
                else:
                    st.success("🟢 Healthy budget execution.")

            with col_val:
                st.write(f"Spent: **{format_currency(spent)}** of **{format_currency(limit)}**")
                st.write(f"Remaining: **{format_currency(remaining)}**")
                # Ensure progress bar does not crash (maximum value 1.0)
                norm_pct = min(1.0, pct / 100.0)
                st.progress(norm_pct)
                st.caption(f"Utilization: **{format_percentage(pct)}**")

            with col_actions:
                st.write("")
                if st.button("✏️ Edit", key=f"edit_{b.get('id')}", use_container_width=True):
                    show_edit_dialog(b)
                if st.button("🗑️ Remove", key=f"del_{b.get('id')}", use_container_width=True):
                    show_delete_dialog(b)
