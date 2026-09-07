"""LedgerBud Entry Point — Multipage Streamlit Application."""

import streamlit as st
from ui.state import init_session_state, logout_user
from ui.auth import render_auth_page
from ui.api_client import api_client
from ui.components.error_banner import render_error_banner

# Global app layout configurations
st.set_page_config(
    page_title="LedgerBud Workspace",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize global session variables
init_session_state()

if not st.session_state.authenticated:
    render_auth_page()
else:
    # Sidebar global context controls
    with st.sidebar:
        st.markdown("### 💼 **LedgerBud Workspace**")
        st.caption(f"Connected: **{st.session_state.user.get('full_name')}**")
        
        st.divider()
        
        # Global Wallet Selector
        try:
            wallets = api_client.list_wallets()
            if not wallets:
                st.warning("No wallets registered.")
                # Popover block to add a wallet
                with st.popover("➕ Add First Wallet", use_container_width=True):
                    with st.form("sidebar_wallet_form", clear_on_submit=True):
                        w_name = st.text_input("Name", placeholder="e.g. HDFC Salary")
                        w_type = st.selectbox("Type", ["bank", "credit_card", "cash", "digital"])
                        w_bal = st.number_input("Starting Balance", min_value=0.0, format="%.2f")
                        submit = st.form_submit_button("Save Wallet", use_container_width=True)
                        if submit:
                            if not w_name:
                                st.error("Name is required.")
                            else:
                                api_client.create_wallet(w_name, w_type, w_bal)
                                st.success("Wallet created successfully!")
                                st.rerun()
            else:
                # Compile list of options for wallet selection
                wallet_options = {"All Wallets": None}
                for w in wallets:
                    label = f"{w['wallet_name']} ({w['wallet_type'].title()})"
                    wallet_options[label] = w["id"]

                # Active selection mapping
                curr_wallet_idx = 0
                if st.session_state.active_wallet_id:
                    # Find matching label index if already selected
                    for idx, (lbl, val) in enumerate(wallet_options.items()):
                        if val == st.session_state.active_wallet_id:
                            curr_wallet_idx = idx
                            break

                selected_wallet_label = st.selectbox(
                    "Selected Wallet Filter",
                    options=list(wallet_options.keys()),
                    index=curr_wallet_idx,
                    help="Filters transactions, budget usage, and metrics dynamically."
                )
                
                # Sync back to session state
                st.session_state.active_wallet_id = wallet_options[selected_wallet_label]
                
                # Button to create a new wallet
                with st.popover("➕ Add Wallet", use_container_width=True):
                    with st.form("sidebar_new_wallet_form", clear_on_submit=True):
                        w_name = st.text_input("Wallet Name", placeholder="e.g. ICICI Savings")
                        w_type = st.selectbox("Type", ["bank", "credit_card", "cash", "digital"])
                        w_bal = st.number_input("Starting Balance (₹)", min_value=0.0, format="%.2f")
                        submit = st.form_submit_button("Create", use_container_width=True)
                        if submit:
                            if w_name:
                                api_client.create_wallet(w_name, w_type, w_bal)
                                st.success("Wallet created.")
                                st.rerun()
                            else:
                                st.error("Please enter a name.")
        except Exception as exc:
            render_error_banner(exc, "loading wallets in sidebar")

        st.divider()
        
        # Log out button at bottom of sidebar
        if st.button("Sign Out of Workspace", type="secondary", use_container_width=True):
            logout_user()
            st.rerun()

    # Launch page routing
    from ui.navigation import run_navigation
    run_navigation()
