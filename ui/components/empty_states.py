"""Empty state representation builders to instruct the user gracefully."""

import streamlit as st


def render_empty_state(title: str, description: str, icon: str = "info", action_label: str | None = None):
    """Render a clean, centered empty state container."""
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            st.markdown(f"### {title}")
            st.write(description)
            if action_label:
                st.caption(f"💡 Get started by selecting '{action_label}' above.")
