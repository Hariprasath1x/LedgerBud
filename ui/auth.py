"""Authentication views and handlers (Login/Registration/Forgot Password)."""

import os
import httpx
import streamlit as st
from ui.api_client import api_client
from ui.state import login_user


def _get_api_key():
    key = os.environ.get("FIREBASE_API_KEY", "")
    if not key:
        try:
            if hasattr(st, "secrets") and "FIREBASE_API_KEY" in st.secrets:
                key = str(st.secrets["FIREBASE_API_KEY"]).strip()
        except Exception:
            pass
    return key

def firebase_auth_request(endpoint: str, payload: dict) -> dict:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "FIREBASE_API_KEY is not configured. Please configure it in your .env file or Streamlit Secrets."
        )
        
    url = f"https://identitytoolkit.googleapis.com/v1/{endpoint}?key={api_key}"
    resp = httpx.post(url, json=payload, timeout=10.0)
    
    if resp.status_code != 200:
        error_data = resp.json().get("error", {})
        error_msg = error_data.get("message", "Authentication failed")
        raise Exception(error_msg)
        
    return resp.json()


def is_cookie_secure() -> bool:
    """Determine if Secure cookie flag should be enforced based on environment."""
    env = os.environ.get("ENVIRONMENT", "")
    cookie_secure = os.environ.get("COOKIE_SECURE", "")
    try:
        if hasattr(st, "secrets"):
            if not env and "ENVIRONMENT" in st.secrets:
                env = str(st.secrets["ENVIRONMENT"]).strip()
            if not cookie_secure and "COOKIE_SECURE" in st.secrets:
                cookie_secure = str(st.secrets["COOKIE_SECURE"]).strip()
    except Exception:
        pass
    env = env.lower()
    cookie_secure = cookie_secure.lower()
    if cookie_secure in ("true", "1", "yes"):
        return True
    if cookie_secure in ("false", "0", "no"):
        return False
    return env in ("production", "prod", "staging")


def get_set_cookie_script(token: str, max_age: int = 604800) -> str:
    """Generate script to persist session token in cookie, enabling Secure flag on HTTPS/production."""
    force_secure = "true" if is_cookie_secure() else "false"
    return f"""<script>
    (function() {{
        var isHttps = (window.location.protocol === 'https:') || (window.parent && window.parent.location.protocol === 'https:') || {force_secure};
        var secureFlag = isHttps ? '; Secure' : '';
        document.cookie = "lb_session_token={token}; path=/; max-age={max_age}; SameSite=Lax" + secureFlag;
    }})();
    </script>"""


def get_clear_cookie_script() -> str:
    """Generate script to clear session token cookie."""
    force_secure = "true" if is_cookie_secure() else "false"
    return f"""<script>
    (function() {{
        var isHttps = (window.location.protocol === 'https:') || (window.parent && window.parent.location.protocol === 'https:') || {force_secure};
        var secureFlag = isHttps ? '; Secure' : '';
        document.cookie = "lb_session_token=; path=/; max-age=0; SameSite=Lax" + secureFlag;
    }})();
    </script>"""


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
                            with st.spinner("Authenticating with LedgerBud security..."):
                                fb_res = firebase_auth_request(
                                    "accounts:signInWithPassword",
                                    {
                                        "email": email.strip(),
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
                                
                                # Persist session in browser cookie for seamless page reload
                                st.components.v1.html(get_set_cookie_script(access_token), height=0)
                                
                            st.success(f"Welcome back, {user_info.get('full_name', 'User')}!")
                            st.query_params.clear()
                            try:
                                st.switch_page("ui/pages/overview.py")
                            except Exception:
                                st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                        except Exception as exc:
                            err_msg = str(exc)
                            if any(k in err_msg for k in ("INVALID_LOGIN_CREDENTIALS", "INVALID_PASSWORD", "EMAIL_NOT_FOUND")):
                                st.error("Invalid email or password. Please check your credentials or reset your password.")
                            elif "USER_DISABLED" in err_msg:
                                st.error("This user account has been disabled. Please contact support.")
                            elif "TOO_MANY_ATTEMPTS_TRY_LATER" in err_msg:
                                st.error("Too many unsuccessful attempts. Access temporarily blocked. Please reset your password or try again later.")
                            else:
                                st.error(f"Authentication failed: {err_msg}")

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
                            with st.spinner("Creating your workspace..."):
                                fb_res = firebase_auth_request(
                                    "accounts:signUp",
                                    {
                                        "email": email.strip(),
                                        "password": password,
                                        "returnSecureToken": True
                                    }
                                )
                                access_token = fb_res["idToken"]
                                
                                # 2. Store token temporarily in session state
                                st.session_state.token = access_token
                                
                                # Update profile with full name
                                try:
                                    firebase_auth_request(
                                        "accounts:update",
                                        {
                                            "idToken": access_token,
                                            "displayName": full_name.strip(),
                                            "returnSecureToken": True
                                        }
                                    )
                                except Exception:
                                    pass
                                
                                # 3. Retrieve user profile info from FastAPI backend (auto-provisions)
                                user_info = api_client.get_me()
                                
                                # Complete registration login setup
                                login_user(access_token, user_info)
                                
                                # Persist session in browser cookie for seamless page reload
                                st.components.v1.html(get_set_cookie_script(access_token), height=0)
                                
                            st.success("Account successfully created!")
                            st.query_params.clear()
                            try:
                                st.switch_page("ui/pages/overview.py")
                            except Exception:
                                st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                        except Exception as exc:
                            err_msg = str(exc)
                            if "EMAIL_EXISTS" in err_msg:
                                st.error("An account with this email already exists. Please sign in instead.")
                            elif "WEAK_PASSWORD" in err_msg:
                                st.error("Password is too weak. Please choose a stronger password.")
                            else:
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
