"""Multipage navigation structure for LedgerBud using st.navigation."""

import streamlit as st


def get_navigation():
    """Build and return the appropriate st.navigation object based on auth state."""
    raw_auth = st.query_params.get("auth", "false")
    if isinstance(raw_auth, list):
        raw_auth = raw_auth[0] if raw_auth else "false"
    is_auth_param = str(raw_auth).lower() in ("true", "1")
    show_auth = is_auth_param or st.session_state.get("show_auth", False)
    if show_auth:
        st.session_state.show_auth = True

    # When unauthenticated: provide Welcome and Auth pages
    if not st.session_state.get("authenticated", False):
        welcome_page = st.Page("ui/pages/welcome.py", title="Welcome & Overview", icon="✨", default=not show_auth)
        auth_page = st.Page("ui/pages/auth_page.py", title="Sign In to Workspace", icon="🔐", default=show_auth)
        return st.navigation([welcome_page, auth_page], position="hidden")

    # When authenticated: provide full workspace suites
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
        ],
        "Settings": [
            st.Page("ui/pages/profile.py", title="User Profile", icon="👤"),
            st.Page("ui/pages/welcome.py", title="Welcome & Overview", icon="✨"),
        ]
    }

    return st.navigation(pages, position="sidebar")


def run_navigation():
    """Define the page mapping and execute Streamlit navigation."""
    pg = get_navigation()
    pg.run()

