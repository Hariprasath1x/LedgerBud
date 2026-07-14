"""Savings Goals Workspace — LedgerBud."""

import streamlit as st
from datetime import date
from ui.api_client import api_client
from ui.formatters import format_currency, format_percentage, format_date
from ui.components.error_banner import render_error_banner


@st.dialog("Create Savings Goal")
def show_create_dialog():
    """Native form to create a new savings goal."""
    with st.form("create_goal_form", clear_on_submit=True):
        name = st.text_input("Goal Name", placeholder="e.g. Downpayment for House")
        target_amount = st.number_input("Target Amount (INR)", min_value=100.0, format="%.2f", step=1000.0)
        current_amount = st.number_input("Starting Savings (INR)", min_value=0.0, format="%.2f", step=500.0)
        target_date = st.date_input("Target Date (Optional)", value=None)
        description = st.text_area("Description (Optional)", placeholder="Add context...")
        
        submit = st.form_submit_button("Save Goal", use_container_width=True)

        if submit:
            if not name:
                st.error("Name is required.")
            else:
                try:
                    # Convert target_date to str if not None
                    t_date_str = str(target_date) if target_date else None
                    api_client.create_goal(name, target_amount, current_amount, description, t_date_str)
                    st.success("Savings Goal created successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")


@st.dialog("Add Contribution")
def show_contribute_dialog(goal):
    """Directly increment target goal savings."""
    with st.form("contribute_goal_form"):
        st.write(f"Add a contribution to **{goal.get('name')}**")
        amount = st.number_input("Contribution Amount (INR)", min_value=1.0, format="%.2f", step=500.0)
        submit = st.form_submit_button("Save Contribution", use_container_width=True)

        if submit:
            try:
                api_client.contribute_goal(goal.get("id"), amount)
                st.success("Contribution recorded!")
                st.rerun()
            except Exception as exc:
                st.error(f"Error: {exc}")


@st.dialog("Edit Goal")
def show_edit_dialog(goal):
    """Update goal configurations."""
    with st.form("edit_goal_form"):
        name = st.text_input("Goal Name", value=goal.get("name", ""))
        target_amount = st.number_input("Target Amount (INR)", min_value=100.0, value=float(goal.get("target_amount", 0.0)), format="%.2f", step=1000.0)
        
        from datetime import datetime
        try:
            default_date = datetime.strptime(goal.get("target_date", ""), "%Y-%m-%d").date()
        except Exception:
            default_date = date.today()
            
        target_date = st.date_input("Target Date", value=default_date)
        status = st.selectbox("Status", ["active", "completed", "paused"], index=["active", "completed", "paused"].index(goal.get("status", "active")))
        description = st.text_area("Description", value=goal.get("description") or "")
        
        submit = st.form_submit_button("Update Goal", use_container_width=True)

        if submit:
            if not name:
                st.error("Name is required.")
            else:
                try:
                    payload = {
                        "name": name,
                        "target_amount": target_amount,
                        "target_date": str(target_date),
                        "status": status,
                        "description": description
                    }
                    api_client.update_goal(goal.get("id"), payload)
                    st.success("Savings Goal updated!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")


@st.dialog("Delete Goal")
def show_delete_dialog(goal):
    """Confirm savings goal deletion."""
    st.write(f"Are you sure you want to delete savings goal **{goal.get('name')}**?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete", type="primary", use_container_width=True):
            try:
                api_client.delete_goal(goal.get("id"))
                st.success("Deleted successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to delete: {exc}")
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


st.title("Savings Goals")
st.markdown("Plan future purchases, construct emergency funds, and monitor savings progress.")

# Action control
col_act, _ = st.columns([1, 4])
with col_act:
    if st.button("➕ Create Goal", use_container_width=True):
        show_create_dialog()

# Retrieve user savings goals
try:
    with st.spinner("Compiling savings goal reports..."):
        goals = api_client.list_goals()
except Exception as e:
    render_error_banner(e, "retrieving goals list")
    st.stop()

if not goals:
    st.info("No savings goals found. Create one to begin tracking progress.")
else:
    # Summarize savings milestones
    active_goals = [g for g in goals if g.get("status") == "active"]
    total_target = sum(float(g.get("target_amount", 0.0)) for g in active_goals)
    total_saved = sum(float(g.get("current_amount", 0.0)) for g in active_goals)
    
    col_tg, col_ts, col_pct = st.columns(3)
    with col_tg:
        st.metric("Consolidated Goals Target", format_currency(total_target))
    with col_ts:
        st.metric("Total Consolidated Savings", format_currency(total_saved))
    with col_pct:
        overall_pct = (total_saved / total_target * 100) if total_target > 0 else 0.0
        st.metric("Consolidated Progress", format_percentage(overall_pct))

    st.divider()

    # Loop through list
    for g in goals:
        target = float(g.get("target_amount", 0.0))
        saved = float(g.get("current_amount", 0.0))
        remaining = float(g.get("remaining_amount", 0.0))
        pct = float(g.get("progress_percentage", 0.0))
        status = g.get("status", "active")
        t_date = g.get("target_date")

        with st.container(border=True):
            col_info, col_progress, col_actions = st.columns([3, 2, 1])

            with col_info:
                st.markdown(f"#### **{g.get('name')}**")
                if g.get("description"):
                    st.write(g.get("description"))
                
                # Render metadata details
                st.caption(f"Status: **{status.title()}** | Target Date: {format_date(t_date)}")
                
                # Goal Projection Calculation
                if t_date and status == "active":
                    from datetime import datetime
                    try:
                        t_date_dt = datetime.strptime(t_date, "%Y-%m-%d").date()
                        days_left = (t_date_dt - date.today()).days
                        if days_left > 0:
                            monthly_needed = (remaining / (days_left / 30)) if days_left > 30 else remaining
                            st.caption(f"💡 Requires **{format_currency(monthly_needed)}/month** to complete on time.")
                        else:
                            st.caption("⏳ Target date has passed.")
                    except Exception:
                        pass

            with col_progress:
                st.write(f"Saved: **{format_currency(saved)}** of **{format_currency(target)}**")
                st.write(f"Remaining: **{format_currency(remaining)}**")
                # Normalize values
                norm_pct = min(1.0, pct / 100.0)
                st.progress(norm_pct)
                st.caption(f"Goal Completion: **{format_percentage(pct)}**")

            with col_actions:
                st.write("")
                if status == "active":
                    if st.button("💰 Contribute", key=f"contrib_{g.get('id')}", use_container_width=True):
                        show_contribute_dialog(g)
                if st.button("✏️ Edit Goal", key=f"edit_{g.get('id')}", use_container_width=True):
                    show_edit_dialog(g)
                if st.button("🗑️ Delete Goal", key=f"del_{g.get('id')}", use_container_width=True):
                    show_delete_dialog(g)
