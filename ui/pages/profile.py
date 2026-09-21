"""User Profile & Security Settings."""

import streamlit as st
import pandas as pd
from ui.api_client import api_client
from ui.auth import firebase_auth_request
from ui.state import logout_user
from ui.formatters import format_currency

st.title("User Profile & Security")
st.markdown("Manage your account settings, secure wallet vault, and data retention.")

if "wallets_unlocked" not in st.session_state:
    st.session_state.wallets_unlocked = False

user = st.session_state.get("user", {})

# --- SECTION 1: PROFILE SETTINGS ---
st.subheader("👤 Profile Information")
with st.container(border=True):
    with st.form("update_name_form", clear_on_submit=False):
        new_name = st.text_input("Display Name", value=user.get("full_name", ""))
        submit_name = st.form_submit_button("Update Name")
        if submit_name:
            if not new_name:
                st.error("Name cannot be empty.")
            else:
                try:
                    updated_user = api_client.update_name(new_name)
                    st.session_state.user = updated_user
                    st.success("Name updated successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update name: {e}")

# --- SECTION 2: PASSWORD SETTINGS ---
st.subheader("🔐 Security Settings")
with st.container(border=True):
    with st.form("update_password_form", clear_on_submit=True):
        st.write("Update your account password.")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        submit_pass = st.form_submit_button("Change Password")
        
        if submit_pass:
            if len(new_pass) < 8:
                st.error("Password must be at least 8 characters.")
            elif new_pass != confirm_pass:
                st.error("Passwords do not match.")
            else:
                try:
                    firebase_auth_request(
                        "accounts:update",
                        {
                            "idToken": st.session_state.token,
                            "password": new_pass,
                            "returnSecureToken": True
                        }
                    )
                    st.success("Password updated successfully.")
                except Exception as e:
                    st.error(f"Failed to update password: {e}")

# --- SECTION 3: SECURE WALLET VAULT ---
st.subheader("🏦 Secure Wallet Vault")
with st.container(border=True):
    if not st.session_state.wallets_unlocked:
        st.info("Your wallet balances are locked for privacy. Enter your password to view them.")
        with st.form("unlock_vault_form", clear_on_submit=True):
            vault_pass = st.text_input("Account Password", type="password")
            unlock_submit = st.form_submit_button("Unlock Vault")
            if unlock_submit:
                if not vault_pass:
                    st.error("Please enter your password.")
                else:
                    try:
                        # Verify by attempting to sign in
                        firebase_auth_request(
                            "accounts:signInWithPassword",
                            {
                                "email": user.get("email"),
                                "password": vault_pass,
                                "returnSecureToken": True
                            }
                        )
                        st.session_state.wallets_unlocked = True
                        st.success("Vault Unlocked!")
                        st.rerun()
                    except Exception as e:
                        st.error("Incorrect password.")
    else:
        st.success("Vault is unlocked.")
        if st.button("🔒 Lock Vault", type="secondary"):
            st.session_state.wallets_unlocked = False
            st.rerun()
            
        try:
            wallets = api_client.list_wallets()
            if not wallets:
                st.write("You have no wallets registered.")
            else:
                df = pd.DataFrame(wallets)
                df = df[["wallet_name", "wallet_type", "balance"]]
                df.columns = ["Wallet Name", "Type", "Balance"]
                df["Type"] = df["Type"].str.title()
                df["Balance"] = df["Balance"].apply(format_currency)
                st.dataframe(df, width="stretch", hide_index=True)
        except Exception as e:
            st.error("Failed to load wallets.")

# --- SECTION 4: LOGOUT ---
st.subheader("🚪 Session")
with st.container(border=True):
    st.write("Sign out of the LedgerBud Workspace on this device.")
    if st.button("Sign Out", type="secondary"):
        logout_user()
        st.rerun()

# --- SECTION 5: DANGER ZONE ---
st.subheader("⚠️ Danger Zone")
with st.container(border=True):
    st.write("Destructive actions that cannot be undone.")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.popover("Delete All Transactions", width="stretch"):
            st.warning("This will permanently delete ALL your transactions. Wallets and budgets will remain.")
            if st.button("Confirm Delete Transactions", type="primary"):
                try:
                    res = api_client.delete_all_transactions()
                    st.success(res.get("message", "Transactions deleted."))
                except Exception as e:
                    st.error(f"Failed to delete: {e}")
                    
    with col2:
        with st.popover("Delete Account Completely", width="stretch"):
            st.error("This will permanently delete your identity, wallets, transactions, goals, and all associated data. THIS CANNOT BE UNDONE.")
            if st.button("Confirm Delete Account", type="primary"):
                try:
                    api_client.delete_profile()
                    logout_user()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete account: {e}")
