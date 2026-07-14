"""Plotly financial charts library for LedgerBud workspace."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Classic financial intelligence palette
COLORS = {
    "income": "#2b8a3e",       # Calm dark green
    "expense": "#c92a2a",      # Muted red
    "savings": "#1c7ed6",      # Muted blue
    "neutral": "#495057",      # Slate grey
    "background": "#ffffff",
    "grid": "#f1f3f5",
    "text": "#212529"
}


def render_cash_flow_trend(trend_data: list[dict]):
    """Render monthly Income vs Expense vs Savings trend chart."""
    if not trend_data:
        st.info("No trend data available.")
        return

    df = pd.DataFrame(trend_data)
    # Parse month to human readable
    from ui.formatters import format_month
    df["Month Display"] = df["month"].apply(format_month)

    fig = go.Figure()

    # Add Income Bar
    fig.add_trace(go.Bar(
        x=df["Month Display"],
        y=df["income"],
        name="Income",
        marker_color=COLORS["income"],
        hovertemplate="Income: ₹%{y:,.2f}<extra></extra>"
    ))

    # Add Expense Bar
    fig.add_trace(go.Bar(
        x=df["Month Display"],
        y=df["expense"],
        name="Expense",
        marker_color=COLORS["expense"],
        hovertemplate="Expense: ₹%{y:,.2f}<extra></extra>"
    ))

    # Add Savings Line
    fig.add_trace(go.Scatter(
        x=df["Month Display"],
        y=df["savings"],
        name="Net Savings",
        mode="lines+markers",
        line=dict(color=COLORS["savings"], width=3),
        marker=dict(size=8),
        hovertemplate="Savings: ₹%{y:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        title="Monthly Cash Flow Trend",
        barmode="group",
        plot_bgcolor=COLORS["background"],
        paper_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        xaxis=dict(gridcolor=COLORS["grid"]),
        yaxis=dict(title="Amount (INR)", gridcolor=COLORS["grid"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_category_pie(category_data: list[dict]):
    """Render spending breakdown by category."""
    if not category_data:
        st.info("No category expenses detected this month.")
        return

    df = pd.DataFrame(category_data)

    fig = px.pie(
        df,
        values="amount",
        names="category",
        title="Expenses by Category",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Safe
    )

    fig.update_traces(
        textinfo="percent+label",
        hovertemplate="Category: %{label}<br>Amount: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>"
    )

    fig.update_layout(
        plot_bgcolor=COLORS["background"],
        paper_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=50, b=80)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_savings_trend(trend_data: list[dict]):
    """Render savings rate trend."""
    if not trend_data:
        st.info("No trend data available.")
        return

    df = pd.DataFrame(trend_data)
    from ui.formatters import format_month
    df["Month Display"] = df["month"].apply(format_month)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Month Display"],
        y=df["savings_rate"],
        name="Savings Rate",
        mode="lines+markers",
        line=dict(color=COLORS["savings"], width=3, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(28, 126, 214, 0.15)",
        marker=dict(size=8),
        hovertemplate="Savings Rate: %{y:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title="Savings Rate Trend (%)",
        plot_bgcolor=COLORS["background"],
        paper_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        xaxis=dict(gridcolor=COLORS["grid"]),
        yaxis=dict(title="Savings Rate (%)", gridcolor=COLORS["grid"]),
        margin=dict(l=40, r=20, t=60, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)
