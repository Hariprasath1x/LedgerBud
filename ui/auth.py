"""Authentication views and handlers (Login/Registration)."""

import streamlit as st
import httpx
from ui.api_client import api_client
from ui.state import login_user


def render_auth_page():
    """Render a clean login/register card interface using native components."""
    st.title("LedgerBud Workspace")
    st.subheader("Financial Intelligence & Cash-flow Control")

    # Center-aligned, simple financial design layout
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            st.write("Access your LedgerBud intelligence workspace.")
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email Address", placeholder="name@company.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Sign In to Workspace", use_container_width=True)

                if submit:
                    if not email or not password:
                        st.error("Please fill in all fields.")
                    else:
                        try:
                            # Connect to FastAPI login endpoint
                            token_res = api_client.login(email, password)
                            access_token = token_res["access_token"]
                            
                            # Store token temporarily in session state to retrieve user info
                            st.session_state.token = access_token
                            
                            # Retrieve user profile info
                            user_info = api_client.get_me()
                            
                            # Complete login setup
                            login_user(access_token, user_info)
                            st.success(f"Welcome back, {user_info['full_name']}!")
                            st.rerun()
                        except httpx.HTTPStatusError as exc:
                            st.error(f"Authentication failed: {exc.response.json().get('detail', 'Invalid credentials')}")
                        except Exception as exc:
                            st.error(f"Could not connect to API server: {exc}")

        with tab_register:
            st.write("Start building structure and trust in your finances.")
            with st.form("register_form", clear_on_submit=False):
                full_name = st.text_input("Full Name", placeholder="Hari Prasath")
                email = st.text_input("Email Address", placeholder="name@company.com")
                password = st.text_input("Password", type="password", placeholder="At least 8 characters")
                submit = st.form_submit_button("Register & Setup Wallet", use_container_width=True)

                if submit:
                    if not full_name or not email or not password:
                        st.error("Please fill in all fields.")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters.")
                    else:
                        try:
                            # Register user
                            auth_res = api_client.register(email, password, full_name)
                            
                            # The auth/register endpoint returns AuthResponse (user + token)
                            access_token = auth_res["token"]["access_token"]
                            user_info = auth_res["user"]
                            
                            # Complete registration login setup
                            login_user(access_token, user_info)
                            st.success("Account successfully created!")
                            st.rerun()
                        except httpx.HTTPStatusError as exc:
                            st.error(f"Registration failed: {exc.response.json().get('detail', 'Email already in use')}")
                        except Exception as exc:
                            st.error(f"Could not connect to API server: {exc}")
