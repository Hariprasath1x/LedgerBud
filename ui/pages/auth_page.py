"""Authentication Page — LedgerBud Workspace Login & Registration."""

import streamlit as st
from ui.auth import render_auth_page


def main():
    # If already authenticated, redirect directly to Overview
    if st.session_state.get("authenticated", False):
        try:
            st.switch_page("ui/pages/overview.py")
            return
        except Exception:
            pass

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Back to Welcome", type="secondary", key="btn_back_to_welcome"):
            st.session_state.show_auth = False
            st.query_params.clear()
            try:
                st.switch_page("ui/pages/welcome.py")
            except Exception:
                st.rerun()

    render_auth_page()


if __name__ != "ui.pages.auth_page" or __name__ == "__main__":
    main()
