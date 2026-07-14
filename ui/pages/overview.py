"""Financial Overview Workspace — LedgerBud."""

import streamlit as st
import pandas as pd
from ui.api_client import api_client
from ui.components.metrics import render_overview_metrics
from ui.components.charts import render_cash_flow_trend, render_category_pie
from ui.components.error_banner import render_error_banner
from ui.formatters import format_currency

st.title("Financial Overview")
st.markdown("Consolidated view of your income, spending, and intelligence observations.")

try:
    with st.spinner("Aggregating financial data..."):
        # Fetch consolidated dashboard data from FastAPI
        dashboard_data = api_client.get_dashboard()

    summary = dashboard_data.get("summary", {})
    health = dashboard_data.get("health_score", {})
    trends = dashboard_data.get("monthly_trends", [])
    categories = dashboard_data.get("category_breakdown", [])
    merchants = dashboard_data.get("top_merchants", [])
    insights = dashboard_data.get("insights", [])

    # Row 1: KPI Metrics
    render_overview_metrics(summary, health.get("score", 0), health.get("grade", "N/A"))

    st.divider()

    # Row 2: Analytical Visualizations
    col_chart1, col_chart2 = st.columns([3, 2])
    with col_chart1:
        render_cash_flow_trend(trends)

    with col_chart2:
        render_category_pie(categories)

    st.divider()

    # Row 3: Insights & Top Merchants
    col_ins, col_merch = st.columns([3, 2])

    with col_ins:
        st.subheader("💡 Financial Intelligence")
        try:
            insights = api_client.get_insights()
        except Exception:
            insights = []
            
        if not insights:
            st.info("No immediate observations or warnings. Keep tracking your expenses.")
        else:
            for item in insights:
                title = item.get("title", "Observation")
                msg = item.get("explanation", item.get("message", ""))
                itype = item.get("severity", item.get("type", "info"))

                with st.container(border=True):
                    st.write(f"**{title}**")
                    if itype == "high" or itype == "warning":
                        st.warning(msg)
                        if item.get("recommended_action"):
                            st.caption(f"**Action:** {item['recommended_action']}")
                    elif itype == "medium":
                        st.warning(msg, icon="⚠️")
                    elif itype == "success":
                        st.success(msg)
                    else:
                        st.info(msg)

    with col_merch:
        st.subheader("🛒 Top Merchants")
        if not merchants:
            st.info("No merchant transactions detected this month.")
        else:
            m_df = pd.DataFrame(merchants)
            # Re-label columns for human viewing
            m_df.columns = ["Merchant", "Amount", "Transactions Count"]
            m_df["Amount"] = m_df["Amount"].apply(format_currency)
            st.dataframe(
                m_df,
                use_container_width=True,
                hide_index=True
            )

except Exception as e:
    render_error_banner(e, "aggregating Financial Overview dashboard")
