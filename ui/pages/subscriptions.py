"""Subscription Intelligence Workspace — LedgerBud."""

import streamlit as st
import pandas as pd
from ui.api_client import api_client
from ui.formatters import format_currency, format_date, format_percentage
from ui.components.error_banner import render_error_banner

st.title("Subscription Intelligence")
st.markdown("Monitor confirmed recurring expenses and identify potential hidden subscriptions.")

# Quick controls
col_scan, _ = st.columns([1, 3])
with col_scan:
    if st.button("🔄 Scan for Subscriptions", use_container_width=True, help="Analyze transaction history to detect recurring payments."):
        with st.spinner("Analyzing transaction patterns..."):
            try:
                new_subs = api_client.detect_subscriptions()
                st.success(f"Subscription scanning complete. Synced {new_subs} new detections!")
                st.rerun()
            except Exception as e:
                render_error_banner(e, "detecting new subscriptions")

# Fetch confirmed vs unconfirmed subscriptions
try:
    with st.spinner("Retrieving subscription data..."):
        all_subs = api_client.list_subscriptions()
except Exception as e:
    render_error_banner(e, "retrieving subscriptions list")
    st.stop()

# Segment into confirmed and potential detections
confirmed = [s for s in all_subs if s.get("is_confirmed")]
detected = [s for s in all_subs if not s.get("is_confirmed")]

# KPI Summary
total_confirmed_monthly = sum(s.get("amount", 0.0) for s in confirmed)
total_confirmed_yearly = sum(s.get("yearly_cost", 0.0) for s in confirmed)

col_count, col_monthly, col_yearly = st.columns(3)
with col_count:
    st.metric("Confirmed Subscriptions", len(confirmed))
with col_monthly:
    st.metric("Monthly Recurring Cost", format_currency(total_confirmed_monthly))
with col_yearly:
    st.metric("Yearly Commitment", format_currency(total_confirmed_yearly))

st.divider()

# Section 1: Confirmed Subscriptions Workspace
st.subheader("✅ Confirmed Subscriptions")
if not confirmed:
    st.info("No confirmed subscriptions. Scan or confirm detected subscriptions below.")
else:
    df_conf = pd.DataFrame(confirmed)
    df_conf = df_conf[["name", "merchant_name", "amount", "frequency", "category", "next_expected", "yearly_cost"]]
    df_conf.columns = ["Name", "Merchant", "Amount", "Frequency", "Category", "Next Bill Date", "Yearly Cost"]
    
    # Format display columns
    df_conf["Amount"] = df_conf["Amount"].apply(format_currency)
    df_conf["Yearly Cost"] = df_conf["Yearly Cost"].apply(format_currency)
    df_conf["Next Bill Date"] = df_conf["Next Bill Date"].apply(format_date)
    df_conf["Frequency"] = df_conf["Frequency"].apply(lambda x: x.title())
    
    st.dataframe(df_conf, use_container_width=True, hide_index=True)

st.divider()

# Section 2: Detected Potential Recurring Payments
st.subheader("🕵️ Potential Recurring Detections")
if not detected:
    st.info("No unconfirmed recurring payments flagged currently.")
else:
    st.markdown("LedgerBud's intelligence engine detected regular payment intervals. Review and confirm or dismiss them.")
    
    for s in detected:
        sub_id = s.get("id")
        name = s.get("name")
        merchant = s.get("merchant_name") or name
        amount = float(s.get("amount", 0.0))
        freq = s.get("frequency", "monthly").title()
        conf_val = float(s.get("detection_confidence", 1.0)) * 100
        category = s.get("category", "General")
        next_exp = s.get("next_expected")
        yearly_est = s.get("yearly_cost", amount * 12)

        with st.container(border=True):
            col_info, col_vals, col_actions = st.columns([3, 2, 1])

            with col_info:
                st.markdown(f"#### **{merchant}**")
                st.caption(f"Category: **{category}** | Suggested Interval: **{freq}**")
                st.write(f"Estimated Yearly Commitment: **{format_currency(yearly_est)}**")
                st.caption(f"Confidence Indicator: **{format_percentage(conf_val)}**")

            with col_vals:
                st.write(f"Recurring Amount: **{format_currency(amount)}**")
                st.write(f"Estimated Next Billing: **{format_date(next_exp)}**")

            with col_actions:
                st.write("")
                if st.button("Confirm Sub", key=f"conf_{sub_id}", use_container_width=True, type="primary"):
                    try:
                        api_client.confirm_subscription(sub_id)
                        st.success(f"Confirmed {name}!")
                        st.rerun()
                    except Exception as exc:
                        render_error_banner(exc, "confirming subscription")
                
                if st.button("Dismiss", key=f"dism_{sub_id}", use_container_width=True):
                    try:
                        api_client.dismiss_subscription(sub_id)
                        st.success("Dismissed detection.")
                        st.rerun()
                    except Exception as exc:
                        render_error_banner(exc, "dismissing subscription")
