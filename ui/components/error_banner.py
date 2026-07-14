"""Error banners and message components."""

import httpx
import streamlit as st


def render_error_banner(exc: Exception, context: str = "operation"):
    """Format and display API or connection errors."""
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            # Attempt to parse detailed FastAPI JSON error response
            err_detail = exc.response.json().get("detail", "HTTP Request Error")
        except Exception:
            err_detail = f"Status Code {exc.response.status_code}: {exc.response.text}"
        st.error(f"⚠️ Failed during {context}: {err_detail}")
    elif isinstance(exc, httpx.RequestError):
        st.error(f"🔌 Connection error during {context}: The API server appears offline or unreachable.")
    else:
        st.error(f"🚨 Unexpected error during {context}: {exc}")
