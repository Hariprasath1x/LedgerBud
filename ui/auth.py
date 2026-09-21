"""Authentication views and handlers (Login/Registration/Forgot Password)."""

import os
import httpx
import streamlit as st
from ui.api_client import api_client
from ui.state import login_user


def _get_api_key():
    return os.environ.get("FIREBASE_API_KEY", "")

def firebase_auth_request(endpoint: str, payload: dict) -> dict:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("FIREBASE_API_KEY environment variable is not set. Please check your .env file.")
        
    url = f"https://identitytoolkit.googleapis.com/v1/{endpoint}?key={api_key}"
    resp = httpx.post(url, json=payload, timeout=10.0)
    
    if resp.status_code != 200:
        error_data = resp.json().get("error", {})
        error_msg = error_data.get("message", "Authentication failed")
        raise Exception(error_msg)
        
    return resp.json()


def render_auth_page():
    """Render a clean login/register/reset card interface using native components."""
    st.title("LedgerBud Workspace")
    st.subheader("Financial Intelligence & Cash-flow Control")

    # Center-aligned, simple financial design layout
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab_login, tab_register, tab_reset = st.tabs(["Sign In", "Create Account", "Forgot Password"])

        with tab_login:
            st.write("Access your LedgerBud intelligence workspace.")
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email Address", placeholder="name@company.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Sign In to Workspace", width="stretch")

                if submit:
                    if not email or not password:
                        st.error("Please fill in all fields.")
                    else:
                        try:
                            # 1. Authenticate with Firebase
                            fb_res = firebase_auth_request(
                                "accounts:signInWithPassword",
                                {
                                    "email": email,
                                    "password": password,
                                    "returnSecureToken": True
                                }
                            )
                            access_token = fb_res["idToken"]
                            
                            # 2. Store token temporarily in session state to retrieve user info
                            st.session_state.token = access_token
                            
                            # 3. Retrieve/auto-provision user profile info from FastAPI backend
                            user_info = api_client.get_me()
                            
                            # Complete login setup
                            login_user(access_token, user_info)
                            st.success(f"Welcome back, {user_info['full_name']}!")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                        except Exception as exc:
                            st.error(f"Authentication failed: {exc}")

        with tab_register:
            st.write("Start building structure and trust in your finances.")
            with st.form("register_form", clear_on_submit=False):
                full_name = st.text_input("Full Name", placeholder="Hari Prasath")
                email = st.text_input("Email Address", placeholder="name@company.com")
                password = st.text_input("Password", type="password", placeholder="At least 8 characters")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                submit = st.form_submit_button("Register & Setup Wallet", width="stretch")

                if submit:
                    if not full_name or not email or not password or not confirm_password:
                        st.error("Please fill in all fields.")
                    elif password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters.")
                    else:
                        try:
                            # 1. Register with Firebase
                            # Note: Firebase Auth REST API doesn't take display_name on signup,
                            # so we pass it later or let backend auto-provision grab the name from email
                            fb_res = firebase_auth_request(
                                "accounts:signUp",
                                {
                                    "email": email,
                                    "password": password,
                                    "returnSecureToken": True
                                }
                            )
                            access_token = fb_res["idToken"]
                            
                            # 2. Store token temporarily in session state
                            st.session_state.token = access_token
                            
                            # Update profile with full name (optional, but good practice)
                            try:
                                firebase_auth_request(
                                    "accounts:update",
                                    {
                                        "idToken": access_token,
                                        "displayName": full_name,
                                        "returnSecureToken": True
                                    }
                                )
                            except Exception:
                                pass # Ignore if it fails, backend will fallback to email
                            
                            # 3. Retrieve user profile info from FastAPI backend (auto-provisions)
                            user_info = api_client.get_me()
                            
                            # Complete registration login setup
                            login_user(access_token, user_info)
                            st.success("Account successfully created!")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                        except Exception as exc:
                            err_msg = str(exc)
                            if "EMAIL_EXISTS" in err_msg:
                                err_msg = "An account with this email already exists."
                            st.error(f"Registration failed: {err_msg}")

        with tab_reset:
            st.write("Reset your password via email.")
            with st.form("reset_form", clear_on_submit=True):
                email = st.text_input("Email Address", placeholder="name@company.com")
                submit = st.form_submit_button("Send Reset Email", width="stretch")

                if submit:
                    if not email:
                        st.error("Please provide an email address.")
                    else:
                        try:
                            firebase_auth_request(
                                "accounts:sendOobCode",
                                {
                                    "requestType": "PASSWORD_RESET",
                                    "email": email
                                }
                            )
                            # Display generic success message to prevent email enumeration
                            st.success("If an account exists with this email, a password reset link has been sent.")
                        except ValueError as exc:
                            st.error(str(exc))
                        except Exception as exc:
                            # Display generic success message even on some errors to prevent enumeration
                            st.success("If an account exists with this email, a password reset link has been sent.")
