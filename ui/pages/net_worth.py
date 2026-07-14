"""Net Worth Tracking Workspace — LedgerBud."""

import streamlit as st
import pandas as pd
from ui.api_client import api_client
from ui.components.error_banner import render_error_banner
from ui.formatters import format_currency
import plotly.express as px

st.title("Net Worth Tracker")
st.markdown("Track your assets, liabilities, and overall net worth over time.")


@st.dialog("Add Net Worth Item")
def show_add_item_dialog():
    with st.form("add_nw_item"):
        name = st.text_input("Name", placeholder="e.g. HDFC Home Loan, Fixed Deposit")
        item_type = st.segmented_control("Type", ["Asset", "Liability"], default="Asset")
        
        asset_cats = ["Cash & Savings", "Fixed Deposit", "Stocks & Equity", "Mutual Funds", "Real Estate", "Gold & Commodities", "Provident Fund", "Other Asset"]
        liab_cats = ["Home Loan", "Car Loan", "Personal Loan", "Credit Card Debt", "Education Loan", "Other Liability"]
        
        category = st.selectbox("Category", asset_cats if item_type == "Asset" else liab_cats)
        amount = st.number_input("Amount (INR)", min_value=0.0, format="%.2f", step=1000.0)
        notes = st.text_input("Notes (Optional)")
        
        if st.form_submit_button("Save Item", use_container_width=True):
            if not name:
                st.error("Name is required.")
            else:
                try:
                    api_client.create_net_worth_item(
                        name=name,
                        item_type=item_type.lower(),
                        category=category,
                        amount=amount,
                        notes=notes
                    )
                    st.success("Saved.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


@st.dialog("Delete Item")
def show_delete_item_dialog(item):
    st.warning(f"Are you sure you want to remove '{item['name']}'? It will no longer be included in future snapshots.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Remove", type="primary", use_container_width=True):
            try:
                api_client.delete_net_worth_item(item['id'])
                st.success("Removed.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


try:
    with st.spinner("Loading net worth data..."):
        summary = api_client.get_net_worth_summary()
        history = api_client.list_net_worth_snapshots()
except Exception as e:
    render_error_banner(e, "loading net worth data")
    st.stop()

# Header Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Net Worth", format_currency(summary.get("net_worth", 0)))
with col2:
    st.metric("Total Assets", format_currency(summary.get("total_assets", 0)))
with col3:
    st.metric("Total Liabilities", format_currency(summary.get("total_liabilities", 0)))

st.divider()

col_chart, col_act = st.columns([3, 1])

with col_act:
    st.markdown("### Actions")
    if st.button("➕ Add Asset / Liability", use_container_width=True):
        show_add_item_dialog()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("Snapshots capture your net worth at a specific point in time to build your historical chart.")
    if st.button("📸 Take Snapshot Now", use_container_width=True):
        try:
            api_client.take_net_worth_snapshot()
            st.success("Snapshot saved.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed: {e}")

with col_chart:
    st.markdown("### Historical Trend")
    if not history:
        st.info("No historical snapshots found. Click 'Take Snapshot Now' to start tracking.")
    else:
        df = pd.DataFrame(history)
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
        fig = px.area(
            df, 
            x="snapshot_date", 
            y="net_worth", 
            title="Net Worth Over Time",
            labels={"snapshot_date": "Date", "net_worth": "Net Worth (₹)"},
            template="plotly_white"
        )
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300)
        st.plotly_chart(fig, use_container_width=True)

st.divider()

col_asset, col_liab = st.columns(2)

items = summary.get("items", [])
assets = [i for i in items if i["item_type"] == "asset"]
liabs = [i for i in items if i["item_type"] == "liability"]

with col_asset:
    st.subheader("Assets")
    if not assets:
        st.caption("No assets recorded.")
    for a in assets:
        with st.container(border=True):
            ac1, ac2 = st.columns([3, 1])
            with ac1:
                st.write(f"**{a['name']}**")
                st.caption(a['category'])
            with ac2:
                st.write(f"**{format_currency(a['amount'])}**")
                if st.button("Delete", key=f"del_a_{a['id']}", use_container_width=True):
                    show_delete_item_dialog(a)

with col_liab:
    st.subheader("Liabilities")
    if not liabs:
        st.caption("No liabilities recorded.")
    for L in liabs:
        with st.container(border=True):
            lc1, lc2 = st.columns([3, 1])
            with lc1:
                st.write(f"**{L['name']}**")
                st.caption(L['category'])
            with lc2:
                st.write(f"**{format_currency(L['amount'])}**")
                if st.button("Delete", key=f"del_l_{L['id']}", use_container_width=True):
                    show_delete_item_dialog(L)
