"""Session state manager for LedgerBud Streamlit app."""

import streamlit as st


def init_session_state():
    """Initialize all session state variables and attempt session restoration."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "active_wallet_id" not in st.session_state:
        st.session_state.active_wallet_id = None  # None means "All Wallets"

    # Attempt automatic session restoration from cookie if not already authenticated
    if not st.session_state.authenticated:
        try_restore_session()


def try_restore_session() -> bool:
    """Restore active user session from browser cookies if valid."""
    try:
        cookies = getattr(st.context, "cookies", {})
        token = cookies.get("lb_session_token")
        if token and isinstance(token, str) and len(token) > 20:
            from ui.api_client import api_client
            st.session_state.token = token
            user_info = api_client.get_me()
            if user_info and isinstance(user_info, dict) and "id" in user_info:
                st.session_state.authenticated = True
                st.session_state.user = user_info
                return True
            st.session_state.token = None
    except Exception:
        st.session_state.token = None
        st.session_state.authenticated = False
    return False


def login_user(token: str, user: dict):
    """Set authentication details in session state."""
    st.session_state.authenticated = True
    st.session_state.token = token
    st.session_state.user = user
    st.session_state.show_auth = False


def logout_user():
    """Clear authentication details from session state."""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.active_wallet_id = None
    st.session_state.show_auth = False
