"""Financial Intelligence Advisor — LedgerBud."""

import streamlit as st
import pandas as pd
from ui.api_client import api_client
from ui.components.error_banner import render_error_banner

st.title("Financial Intelligence Workspace")
st.markdown("Automated insights and portfolio intelligence findings compiled by the LedgerBud engine.")

try:
    with st.spinner("Analyzing intelligence indicators..."):
        health_score_data = api_client.get_health_score()
        insights = api_client.get_insights()
except Exception as e:
    render_error_banner(e, "retrieving financial intelligence data")
    st.stop()

score = health_score_data.get("score", 0)
grade = health_score_data.get("grade", "F")
label = health_score_data.get("label", "Poor")
breakdown = health_score_data.get("breakdown", {})
suggestions = health_score_data.get("suggestions", [])

# Financial Health Assessment Dashboard
col_score_card, col_breakdown_card = st.columns([1, 2])

with col_score_card:
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>Health Score</h3>", unsafe_allow_html=True)
        # Large text styling is acceptable for simple values without HTML CSS hacks, but keeping it clean
        st.metric(label="Overall Assessment", value=f"{score}/100", delta=f"{label} (Grade {grade})", delta_color="normal" if score >= 50 else "inverse")
        st.progress(score / 100.0)
        st.caption("Aggregated assessment of savings, budget discipline, and spending patterns.")

with col_breakdown_card:
    with st.container(border=True):
        st.markdown("### 📊 Score Breakdown")
        
        # Display breakdown values in three sub-columns
        col_sb1, col_sb2, col_sb3 = st.columns(3)
        with col_sb1:
            st.metric(
                label="Savings Ratio Score",
                value=f"{breakdown.get('savings_ratio', 0)}/40",
                help="Points based on monthly savings rate. Target >= 30% savings for maximum points."
            )
        with col_sb2:
            st.metric(
                label="Budget Discipline",
                value=f"{breakdown.get('budget_discipline', 0)}/30",
                help="Points based on overall expense ratios compared to income."
            )
        with col_sb3:
            st.metric(
                label="Spending Behavior",
                value=f"{breakdown.get('spending_behavior', 0)}/30",
                help="Points based on category dominance and discretionary shopping habits."
            )

st.divider()

# Grid: Actionable Suggestions & Spending Insights
col_sug, col_ins = st.columns([1, 1])

with col_sug:
    st.subheader("💡 Strategic Recommendations")
    if not suggestions:
        st.info("No recommendations triggered. Your financial habits look steady.")
    else:
        for sug in suggestions:
            st.markdown(f"- {sug}")

with col_ins:
    st.subheader("🔍 Portfoliowide Intelligence Logs")
    if not insights:
        st.info("No anomalies or major changes observed.")
    else:
        for item in insights:
            title = item.get("title", "Observation")
            msg = item.get("explanation", item.get("message", ""))
            itype = item.get("severity", item.get("type", "info"))
            
            with st.container(border=True):
                st.markdown(f"**{title}**")
                if itype == "high" or itype == "warning":
                    st.warning(msg)
                elif itype == "medium":
                    st.warning(msg, icon="⚠️")
                elif itype == "success":
                    st.success(msg)
                else:
                    st.info(msg)

