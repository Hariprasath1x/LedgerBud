"""Welcome Page — LedgerBud Showcase and Entry."""

from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

WELCOME_HTML_PATH = Path(__file__).parent / "ledgerbud-welcome-page.html"


def render_welcome_page(is_authenticated: bool = False):
    """Render the responsive LedgerBud Welcome HTML page."""
    if not WELCOME_HTML_PATH.exists():
        st.error("Welcome page template not found.")
        return

    # Top Action Bar for guaranteed 1-click workspace entry
    col_bar_l, col_bar_r = st.columns([3, 1])
    with col_bar_l:
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:12px; padding: 4px 0;">
                <span style="font-size: 22px; font-weight: 800; color: #3fb56b; letter-spacing: -0.02em;">💼 LedgerBud</span>
                <span style="font-size: 13px; color: #8b93a7; border-left: 1px solid rgba(255,255,255,0.15); padding-left: 12px;">
                    Personal Finance &amp; Intelligent Wealth OS
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_bar_r:
        if not is_authenticated:
            if st.button("🚀 Open Workspace / Sign In", type="primary", use_container_width=True, key="welcome_top_auth_btn"):
                st.session_state.show_auth = True
                st.query_params["auth"] = "true"
                try:
                    st.switch_page("ui/pages/auth_page.py")
                except Exception:
                    st.rerun()
        else:
            if st.button("📊 Go to Financial Overview", type="primary", use_container_width=True, key="welcome_top_overview_btn"):
                st.switch_page("ui/pages/overview.py")

    with open(WELCOME_HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    # If already authenticated, tweak the CTA button text to return to workspace
    if is_authenticated:
        html_content = html_content.replace(
            '>Sign in<', '>Workspace<'
        ).replace(
            'href="?auth=true"', 'href="/" target="_top"'
        )

    # Render full-bleed HTML iframe with ample height and scrolling enabled
    components.html(html_content, height=1150, scrolling=True)


def main():
    auth_status = st.session_state.get("authenticated", False)
    if auth_status:
        user_name = (st.session_state.get("user") or {}).get("full_name", "User")
        st.caption(f"Connected: **{user_name}** | [Go to Financial Overview](/)")
    render_welcome_page(is_authenticated=auth_status)


# Only execute when run directly by Streamlit page runner, NOT when imported
if __name__ != "ui.pages.welcome" or __name__ == "__main__":
    main()
