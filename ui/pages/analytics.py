"""Analytics and What-If Wealth Simulator — LedgerBud."""

import streamlit as st
import pandas as pd
from ui.api_client import api_client
from ui.components.charts import render_cash_flow_trend, render_savings_trend
from ui.components.error_banner import render_error_banner
from ui.formatters import format_currency, format_percentage

st.title("Analytics & Simulations")
st.markdown("Detailed trend breakdowns and projection forecasting calculations.")

# Retrieve filters
col_m, _ = st.columns([1, 3])
with col_m:
    months_limit = st.selectbox("Trend Interval Range", [6, 12, 24], index=0)

try:
    with st.spinner("Compiling trend timeline..."):
        trends = api_client.get_trends(months=months_limit)
        categories = api_client.get_categories()
except Exception as e:
    render_error_banner(e, "compiling trends")
    st.stop()

# Analytical Visualizations
col_ch1, col_ch2 = st.columns([1, 1])

with col_ch1:
    render_cash_flow_trend(trends)

with col_ch2:
    render_savings_trend(trends)

st.divider()

# What-If Wealth Simulator Section
st.subheader("🔮 What-If Wealth projection Simulator")
st.markdown("Compute the compounded growth impact of saving and investing discretionary spending reductions.")

# Extract categories for simulation options
cat_list = ["All Category Spending"]
if categories:
    cat_list += [c.get("category") for c in categories]

col_sim1, col_sim2 = st.columns([2, 3])

with col_sim1:
    st.markdown("##### **Simulation Assumptions**")
    
    sim_category = st.selectbox("Target Category to Optimize", cat_list)
    
    # Let user select monthly reduction
    reduce_by = st.slider(
        "Monthly Spend Reduction (₹)",
        min_value=0.0,
        max_value=50000.0,
        value=5000.0,
        step=500.0,
        help="Amount in INR to reduce spending by each month."
    )
    
    years = st.slider("Investment Horizon (Years)", min_value=1, max_value=40, value=10)
    interest_rate = st.number_input("Projected Annual Return / Interest Rate (% p.a.)", min_value=1.0, max_value=30.0, value=12.0, step=0.5)

with col_sim2:
    st.markdown("##### **Projected Investment Value**")
    
    # Run the simulation via FastAPI What-If endpoint
    try:
        category_param = sim_category if sim_category != "All Category Spending" else None
        sim_res = api_client.run_whatif(
            category=category_param,
            reduce_by=reduce_by,
            years=years,
            interest_rate=interest_rate
        )
        
        # Display projection findings
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric(
                label="New Monthly Savings",
                value=format_currency(sim_res.get("new_savings", 0.0)),
                delta=f"+{format_currency(reduce_by)}/mo Saved"
            )
            st.metric(
                label="Adjusted Savings Rate",
                value=format_percentage(sim_res.get("new_savings_rate", 0.0))
            )
        with col_res2:
            st.metric(
                label="Wealth Projected (Future Value)",
                value=format_currency(sim_res.get("investment_value", 0.0)),
                help=f"Value after {years} years compounding at {interest_rate}% p.a. assuming monthly contributions."
            )
            st.metric(
                label="Incremental Yearly Savings",
                value=format_currency(sim_res.get("yearly_savings", 0.0))
            )
            
        # Explanatory card
        with st.container(border=True):
            st.write(
                f"Investing **{format_currency(reduce_by)}** per month instead of spending it on **{sim_category}** "
                f"grows into **{format_currency(sim_res.get('investment_value', 0.0))}** over a **{years}-year** horizon "
                f"assuming a compound return rate of **{interest_rate}% per annum**."
            )
            
    except Exception as e:
        render_error_banner(e, "executing What-If simulation projections")
