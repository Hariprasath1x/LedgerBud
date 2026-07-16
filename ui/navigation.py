"""Multipage navigation structure for LedgerBud using st.navigation."""

import streamlit as st


def run_navigation():
    """Define the page mapping and execute Streamlit navigation."""
    # Define available workspace pages
    pages = {
        "Core": [
            st.Page("ui/pages/overview.py", title="Financial Overview", icon="📊", default=True),
            st.Page("ui/pages/wallets.py", title="Wallets", icon="💳"),
            st.Page("ui/pages/transactions.py", title="Transactions", icon="💸"),
            st.Page("ui/pages/statement_import.py", title="Statement Import", icon="📥"),
        ],
        "Planning": [
            st.Page("ui/pages/budgets.py", title="Budgets", icon="📈"),
            st.Page("ui/pages/goals.py", title="Savings Goals", icon="🎯"),
            st.Page("ui/pages/subscriptions.py", title="Subscriptions", icon="🔄"),
        ],
        "Intelligence": [
            st.Page("ui/pages/intelligence.py", title="Intelligence", icon="🧠"),
            st.Page("ui/pages/net_worth.py", title="Net Worth", icon="🏦"),
            st.Page("ui/pages/fire_planner.py", title="FIRE Planner", icon="🔥"),
            st.Page("ui/pages/advisor.py", title="AI Financial Advisor", icon="🤖"),
            st.Page("ui/pages/analytics.py", title="Analytics", icon="📉"),
        ]
    }

    pg = st.navigation(pages, position="sidebar")
    pg.run()

