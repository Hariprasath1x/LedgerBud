"""Metrics display components for financial indicators."""

import streamlit as st
from ui.formatters import format_currency, format_percentage


def render_overview_metrics(summary: dict, health_score: int, health_grade: str):
    """Render financial KPIs (Balance, Income, Expenses, Savings, Health Score)."""
    # 5-column layout for main KPIs
    col_bal, col_inc, col_exp, col_sav, col_hlth = st.columns(5)

    with col_bal:
        st.metric(
            label="Total Balance",
            value=format_currency(summary.get("wallet_balance")),
            help="Consolidated balance across all active wallets.",
        )

    with col_inc:
        st.metric(
            label="Monthly Income",
            value=format_currency(summary.get("total_income")),
        )

    with col_exp:
        # Expenses are typically displayed with no negative sign, but we color or emphasize
        st.metric(
            label="Monthly Expenses",
            value=format_currency(summary.get("total_expense")),
        )

    with col_sav:
        savings = summary.get("savings", 0.0)
        income = summary.get("total_income", 0.0)
        rate = (savings / income * 100) if income > 0 else 0.0
        st.metric(
            label="Savings Rate",
            value=format_percentage(rate),
            delta=format_currency(savings),
            delta_color="normal" if savings >= 0 else "inverse",
        )

    with col_hlth:
        st.metric(
            label="Health Score",
            value=f"{health_score}/100",
            delta=f"Grade: {health_grade}",
            delta_color="off",
            help="Financial intelligence calculation based on savings rate, budget discipline, and spending behavior.",
        )
