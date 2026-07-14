"""Tabular views using st.dataframe and st.column_config."""

import pandas as pd
import streamlit as st
from ui.formatters import format_currency


def render_transactions_table(transactions: list[dict], use_editor: bool = False, key: str = "txn_tbl"):
    """Render transactions list in a structured, searchable interactive table."""
    if not transactions:
        st.info("No transactions found matching your criteria.")
        return None

    df = pd.DataFrame(transactions)

    # Reorder and select relevant columns
    cols = ["id", "transaction_date", "merchant_name", "category", "transaction_type", "amount", "notes"]
    available_cols = [c for c in cols if c in df.columns]
    df = df[available_cols]

    # Convert transaction_date to datetime for proper sorting & display
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])

    column_config = {
        "id": st.column_config.NumberColumn("ID", disabled=True, format="%d"),
        "transaction_date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
        "merchant_name": st.column_config.TextColumn("Merchant / Payee"),
        "category": st.column_config.TextColumn("Category"),
        "transaction_type": st.column_config.SelectboxColumn(
            "Type",
            options=["Income", "Expense"],
        ),
        "amount": st.column_config.NumberColumn(
            "Amount (INR)",
            format="₹%.2f",
        ),
        "notes": st.column_config.TextColumn("Notes"),
    }

    if use_editor:
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key=key,
        )
        return edited_df
    else:
        st.dataframe(
            df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            key=key,
        )
        return None


def render_simple_table(df: pd.DataFrame, column_config: dict | None = None, key: str = "tbl"):
    """Render a generic styled table."""
    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key=key,
    )
