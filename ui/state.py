"""Session state manager for LedgerBud Streamlit app."""

import streamlit as st


def init_session_state():
    """Initialize all session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "active_wallet_id" not in st.session_state:
        st.session_state.active_wallet_id = None  # None means "All Wallets"


def login_user(token: str, user: dict):
    """Set authentication details in session state."""
    st.session_state.authenticated = True
    st.session_state.token = token
    st.session_state.user = user


def logout_user():
    """Clear authentication details from session state."""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.active_wallet_id = None
