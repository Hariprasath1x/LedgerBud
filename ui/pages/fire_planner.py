"""🔥 FIRE Planner — Financial Independence, Retire Early Intelligence Engine."""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from ui.api_client import api_client
from ui.components.error_banner import render_error_banner
from ui.formatters import format_currency, format_percentage

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _cr(value: float) -> str:
    """Format large INR values as Cr/L shorthand for hero display."""
    if abs(value) >= 1_00_00_000:
        return f"₹{value / 1_00_00_000:.2f} Cr"
    elif abs(value) >= 1_00_000:
        return f"₹{value / 1_00_000:.1f} L"
    else:
        return format_currency(value)


def _score_color(score: float) -> str:
    if score >= 75:
        return "#22c55e"
    elif score >= 50:
        return "#f59e0b"
    elif score >= 25:
        return "#f97316"
    else:
        return "#ef4444"


def _donut_chart(value: float, max_val: float, label: str, color: str) -> go.Figure:
    pct = min(value / max_val * 100, 100) if max_val > 0 else 0
    remaining = max(100 - pct, 0)
    fig = go.Figure(go.Pie(
        values=[pct, remaining],
        hole=0.72,
        marker_colors=[color, "#1e293b"],
        textinfo="none",
        hoverinfo="skip",
        showlegend=False,
        direction="clockwise",
        sort=False,
    ))
    fig.add_annotation(
        text=f"<b>{pct:.1f}%</b>",
        x=0.5, y=0.55, font_size=26, showarrow=False,
        font=dict(color="white", family="Inter, sans-serif"),
        xanchor="center",
    )
    fig.add_annotation(
        text=label,
        x=0.5, y=0.38, font_size=11, showarrow=False,
        font=dict(color="#94a3b8", family="Inter, sans-serif"),
        xanchor="center",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=200,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _wealth_projection_chart(projection: list[dict], target_corpus: float) -> go.Figure:
    if not projection:
        return go.Figure()

    years = [p["year"] for p in projection]
    ages = [p["age"] for p in projection]
    nominal = [p["nominal_wealth"] for p in projection]
    real = [p["real_wealth"] for p in projection]
    targets = [target_corpus] * len(projection)

    fig = go.Figure()

    # Projected nominal wealth — filled area
    fig.add_trace(go.Scatter(
        x=ages, y=nominal,
        name="Projected Wealth (Nominal)",
        fill="tozeroy",
        fillcolor="rgba(99, 102, 241, 0.15)",
        line=dict(color="#6366f1", width=3),
        mode="lines+markers",
        marker=dict(size=8, color="#6366f1"),
        hovertemplate="Age %{x}: %{customdata}<extra>Nominal</extra>",
        customdata=[_cr(v) for v in nominal],
    ))

    # Real wealth (inflation-adjusted)
    fig.add_trace(go.Scatter(
        x=ages, y=real,
        name="Real Wealth (Inflation-Adjusted)",
        line=dict(color="#22d3ee", width=2, dash="dot"),
        mode="lines+markers",
        marker=dict(size=6, color="#22d3ee"),
        hovertemplate="Age %{x}: %{customdata}<extra>Real</extra>",
        customdata=[_cr(v) for v in real],
    ))

    # Target corpus line
    fig.add_trace(go.Scatter(
        x=ages, y=targets,
        name="FIRE Target Corpus",
        line=dict(color="#f59e0b", width=2, dash="dash"),
        mode="lines",
        hovertemplate=f"Target: {_cr(target_corpus)}<extra>Target</extra>",
    ))

    fig.update_layout(
        title=dict(text="Wealth Projection", font=dict(size=16, color="#f1f5f9")),
        xaxis=dict(
            title="Age",
            tickfont=dict(color="#94a3b8"),
            gridcolor="#1e293b",
            title_font=dict(color="#94a3b8"),
        ),
        yaxis=dict(
            title="Wealth (₹)",
            tickfont=dict(color="#94a3b8"),
            gridcolor="#1e293b",
            title_font=dict(color="#94a3b8"),
            tickformat=",",
        ),
        legend=dict(font=dict(color="#cbd5e1"), bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.5)",
        height=380,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
    )
    return fig


def _fire_score_gauge(score: float) -> go.Figure:
    color = _score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(color="white", size=36), suffix="/100"),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickfont=dict(color="#94a3b8"),
                tickcolor="#94a3b8",
            ),
            bar=dict(color=color),
            bgcolor="#1e293b",
            bordercolor="#334155",
            steps=[
                dict(range=[0, 25], color="#0f172a"),
                dict(range=[25, 50], color="#1e293b"),
                dict(range=[50, 75], color="#1e293b"),
                dict(range=[75, 100], color="#0f172a"),
            ],
            threshold=dict(
                line=dict(color="#f59e0b", width=3),
                thickness=0.8,
                value=score,
            ),
        ),
        title=dict(text="FIRE Readiness Score", font=dict(color="#94a3b8", size=14)),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=220,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig


def _score_breakdown_chart(breakdown: dict) -> go.Figure:
    labels = [
        "Savings Rate (30)",
        "Health Score (25)",
        "Debt Ratio (15)",
        "NW Growth (15)",
        "Invest. Discipline (10)",
        "Budget Discipline (5)",
    ]
    max_vals = [30, 25, 15, 15, 10, 5]
    actual = [
        breakdown.get("savings_rate_score", 0),
        breakdown.get("health_score_contribution", 0),
        breakdown.get("debt_ratio_score", 0),
        breakdown.get("net_worth_growth_score", 0),
        breakdown.get("investment_discipline_score", 0),
        breakdown.get("budget_discipline_score", 0),
    ]
    pcts = [round(a / m * 100, 1) if m > 0 else 0 for a, m in zip(actual, max_vals)]
    colors = ["#22c55e" if p >= 70 else "#f59e0b" if p >= 40 else "#ef4444" for p in pcts]

    fig = go.Figure(go.Bar(
        x=actual,
        y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{a:.1f}/{m}" for a, m in zip(actual, max_vals)],
        textposition="outside",
        textfont=dict(color="#cbd5e1", size=11),
        hovertemplate="%{y}: %{x:.1f}<extra></extra>",
    ))
    # Max-value ghost bars
    for i, (label, mx) in enumerate(zip(labels, max_vals)):
        fig.add_trace(go.Bar(
            x=[mx],
            y=[label],
            orientation="h",
            marker=dict(color="rgba(255,255,255,0.05)", line=dict(width=0)),
            showlegend=False,
            hoverinfo="skip",
        ))

    fig.update_layout(
        title=dict(text="Score Breakdown", font=dict(color="#f1f5f9", size=14)),
        barmode="overlay",
        xaxis=dict(range=[0, 32], tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        yaxis=dict(tickfont=dict(color="#cbd5e1")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.5)",
        height=280,
        margin=dict(l=10, r=60, t=40, b=10),
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Page entry
# ─────────────────────────────────────────────────────────────────────────────

st.title("🔥 FIRE Intelligence Engine")
st.markdown(
    "**Financial Independence, Retire Early** — powered by your live financial data."
)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN PAGE — Settings
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("⚙️ FIRE Settings", expanded=True):
    st.caption("Only these four values need your input — everything else is auto-fetched.")

    # Restore from session state if previously calculated
    prev = st.session_state.get("fire_settings", {})
    
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        current_age = st.number_input(
            "Current Age",
            min_value=18, max_value=80,
            value=prev.get("current_age", 25),
            step=1,
            key="fire_current_age",
        )
    with col2:
        retirement_target_age = st.number_input(
            "Target Retirement Age",
            min_value=25, max_value=90,
            value=prev.get("retirement_target_age", 45),
            step=1,
            key="fire_retirement_age",
        )
    with col3:
        investment_return = st.slider(
            "Expected Annual Return (%)",
            min_value=6.0, max_value=18.0,
            value=float(prev.get("investment_return", 12.0)),
            step=0.5,
            key="fire_return",
        )
    with col4:
        inflation_rate = st.slider(
            "Expected Inflation Rate (%)",
            min_value=2.0, max_value=10.0,
            value=float(prev.get("inflation_rate", 6.0)),
            step=0.5,
            key="fire_inflation",
        )
    with col5:
        lifestyle = st.selectbox(
            "Desired Retirement Lifestyle",
            options=["Lean", "Moderate", "Comfortable", "Luxury"],
            index=["Lean", "Moderate", "Comfortable", "Luxury"].index(
                prev.get("lifestyle", "Moderate")
            ),
            key="fire_lifestyle",
            help="Adjusts target corpus: Lean=0.8×, Moderate=1×, Comfortable=1.25×, Luxury=1.6×",
        )

    calculate_btn = st.button(
        "🔥 Calculate FIRE",
        type="primary",
        use_container_width=True,
        key="fire_calculate_btn",
    )

# ─────────────────────────────────────────────────────────────────────────────
# Run calculation on button press
# ─────────────────────────────────────────────────────────────────────────────

if calculate_btn:
    settings_payload = {
        "current_age": current_age,
        "retirement_target_age": retirement_target_age,
        "investment_return": investment_return,
        "inflation_rate": inflation_rate,
        "lifestyle": lifestyle,
    }
    with st.spinner("Running FIRE Intelligence Engine..."):
        try:
            result = api_client.calculate_fire(settings_payload)
            st.session_state["fire_result"] = result
            st.session_state["fire_settings"] = settings_payload
            st.session_state["fire_context_for_ai"] = None  # reset AI context cache
            st.success("✅ FIRE analysis complete!")
        except Exception as e:
            render_error_banner(e, "calculating FIRE")

# ─────────────────────────────────────────────────────────────────────────────
# Load data — prefer session result, fallback to latest stored
# ─────────────────────────────────────────────────────────────────────────────

result: dict | None = st.session_state.get("fire_result")

if result is None:
    with st.spinner("Loading FIRE dashboard..."):
        try:
            dashboard = api_client.get_fire_dashboard()
            if dashboard.get("has_data") and dashboard.get("result"):
                result = dashboard["result"]
                st.session_state["fire_result"] = result
        except Exception as e:
            render_error_banner(e, "loading FIRE dashboard")

# ─────────────────────────────────────────────────────────────────────────────
# Empty state
# ─────────────────────────────────────────────────────────────────────────────

if result is None:
    st.info(
        "👆 **Set your FIRE parameters in the sidebar and click 'Calculate FIRE'** to begin.\n\n"
        "The engine will automatically fetch your income, expenses, net worth, budgets and goals "
        "to compute your Financial Independence score and retirement projection."
    )
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# HERO WIDGET — Full-width dashboard banner
# ─────────────────────────────────────────────────────────────────────────────

settings_disp = result.get("settings", {})
fire_score = result.get("fire_score", 0)
net_worth = result.get("current_net_worth", 0)
target_corpus = result.get("fire_target_corpus", 0)
fire_progress = result.get("fire_progress", 0)
est_fire_age = result.get("estimated_fire_age", 0)
years_remaining = result.get("years_remaining", 0)
req_monthly = result.get("required_monthly_investment", 0)
status_label = result.get("status_label", "")

hero_color = _score_color(fire_score)

st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
">
    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px;">
        <div>
            <div style="font-size:13px; color:#94a3b8; letter-spacing:2px; text-transform:uppercase; font-weight:600;">
                🔥 FIRE Dashboard
            </div>
            <div style="font-size:38px; font-weight:800; color:{hero_color}; margin-top:4px;">
                {fire_score:.0f} <span style="font-size:20px; color:#94a3b8;">/ 100</span>
            </div>
            <div style="font-size:14px; color:#cbd5e1; margin-top:4px;">FIRE Readiness Score</div>
        </div>
        <div style="display:flex; gap:32px; flex-wrap:wrap;">
            <div style="text-align:center;">
                <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">Net Worth</div>
                <div style="font-size:20px; font-weight:700; color:#f1f5f9;">{_cr(net_worth)}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">Target Corpus</div>
                <div style="font-size:20px; font-weight:700; color:#f59e0b;">{_cr(target_corpus)}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">Progress</div>
                <div style="font-size:20px; font-weight:700; color:#6366f1;">{fire_progress:.1f}%</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">FIRE Age</div>
                <div style="font-size:20px; font-weight:700; color:#22d3ee;">{est_fire_age:.1f}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">Years Left</div>
                <div style="font-size:20px; font-weight:700; color:#f1f5f9;">{years_remaining:.1f}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">Monthly SIP</div>
                <div style="font-size:20px; font-weight:700; color:#22c55e;">{_cr(req_monthly)}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">Status</div>
                <div style="font-size:16px; font-weight:700; color:#f1f5f9;">{status_label}</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Key Metrics Cards
# ─────────────────────────────────────────────────────────────────────────────

annual_income = result.get("annual_income", 0)
annual_expenses = result.get("annual_expenses", 0)
annual_savings = result.get("annual_savings", 0)
savings_rate = result.get("savings_rate", 0)
debt_ratio = result.get("debt_ratio", 0)
health_score = result.get("financial_health_score", 0)

st.subheader("📊 Financial Overview")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Annual Income", _cr(annual_income))
with c2:
    st.metric("Annual Expenses", _cr(annual_expenses))
with c3:
    st.metric("Annual Savings", _cr(annual_savings))
with c4:
    sr_delta = "✅ FIRE Ready" if savings_rate >= 30 else "⚠️ Below 30%"
    st.metric("Savings Rate", f"{savings_rate:.1f}%", delta=sr_delta)
with c5:
    st.metric("Debt Ratio", f"{debt_ratio:.1f}%", delta="Low" if debt_ratio < 20 else "High", delta_color="normal" if debt_ratio < 20 else "inverse")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — FIRE Progress Ring + Score Gauge
# ─────────────────────────────────────────────────────────────────────────────

col_donut, col_gauge, col_score_break = st.columns([1, 1.2, 1.5])

with col_donut:
    st.markdown("##### FIRE Progress")
    st.plotly_chart(
        _donut_chart(fire_progress, 100, "towards Financial Independence", hero_color),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.caption(f"**{_cr(net_worth)}** of **{_cr(target_corpus)}**")

with col_gauge:
    st.markdown("##### Readiness Score")
    st.plotly_chart(
        _fire_score_gauge(fire_score),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with col_score_break:
    st.markdown("##### Score Components")
    breakdown = result.get("score_breakdown", {})
    if any(v > 0 for v in breakdown.values()):
        st.plotly_chart(
            _score_breakdown_chart(breakdown),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        # Simplified display from stored data
        st.metric("Overall FIRE Score", f"{fire_score:.0f}/100")
        st.metric("Financial Health", f"{health_score:.0f}/100")
        st.metric("Savings Rate", f"{savings_rate:.1f}%")
        st.metric("Debt Ratio", f"{debt_ratio:.1f}%")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Wealth Projection Chart
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("📈 Wealth Projection")
projection = result.get("wealth_projection", [])
if projection:
    st.plotly_chart(
        _wealth_projection_chart(projection, target_corpus),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # Projection table
    proj_df = pd.DataFrame(projection)
    proj_df = proj_df.rename(columns={
        "year": "Year",
        "age": "Age",
        "nominal_wealth": "Projected Wealth (Nominal)",
        "real_wealth": "Real Wealth (Inflation-Adj.)",
        "target_corpus": "Target Corpus",
    })
    for col in ["Projected Wealth (Nominal)", "Real Wealth (Inflation-Adj.)", "Target Corpus"]:
        proj_df[col] = proj_df[col].apply(lambda v: _cr(v))

    with st.expander("View Projection Table", expanded=False):
        st.dataframe(proj_df, use_container_width=True, hide_index=True)
else:
    st.info("No projection data available. Click 'Calculate FIRE' to generate.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Scenario Comparison
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("🎯 Scenario Analysis")

scenarios = result.get("scenarios", [])
if scenarios:
    scenario_data = []
    for s in scenarios:
        scenario_data.append({
            "Scenario": s.get("name", ""),
            "Expected Return": f"{s.get('expected_return', 0):.1f}%",
            "Inflation Rate": f"{s.get('inflation_rate', 0):.1f}%",
            "Target Corpus": _cr(s.get("fire_target_corpus", 0)),
            "Est. FIRE Age": f"{s.get('estimated_fire_age', 0):.1f}",
            "Years Remaining": f"{s.get('years_remaining', 0):.1f}",
            "Monthly SIP Required": _cr(s.get("monthly_investment_required", 0)),
        })

    df = pd.DataFrame(scenario_data)

    # Style the table with row colors
    def highlight_row(row):
        scenario = row["Scenario"]
        if scenario == "Conservative":
            return ["background-color: rgba(239,68,68,0.1)"] * len(row)
        elif scenario == "Moderate":
            return ["background-color: rgba(245,158,11,0.1)"] * len(row)
        else:
            return ["background-color: rgba(34,197,94,0.1)"] * len(row)

    st.dataframe(
        df.style.apply(highlight_row, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    # Visual comparison
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        fire_ages = [s.get("estimated_fire_age", 0) for s in scenarios]
        names = [s.get("name", "") for s in scenarios]
        colors_bar = ["#ef4444", "#f59e0b", "#22c55e"]
        fig_ages = go.Figure(go.Bar(
            x=names, y=fire_ages,
            marker=dict(color=colors_bar),
            text=[f"{a:.1f}" for a in fire_ages],
            textposition="outside",
            textfont=dict(color="#f1f5f9"),
        ))
        fig_ages.update_layout(
            title="Estimated FIRE Age by Scenario",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.5)",
            font=dict(color="#94a3b8"),
            height=260,
            margin=dict(l=10, r=10, t=40, b=10),
            yaxis=dict(gridcolor="#1e293b"),
        )
        st.plotly_chart(fig_ages, use_container_width=True, config={"displayModeBar": False})

    with col_s2:
        sips = [s.get("monthly_investment_required", 0) for s in scenarios]
        fig_sip = go.Figure(go.Bar(
            x=names, y=sips,
            marker=dict(color=colors_bar),
            text=[_cr(s) for s in sips],
            textposition="outside",
            textfont=dict(color="#f1f5f9"),
        ))
        fig_sip.update_layout(
            title="Monthly SIP Required by Scenario",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.5)",
            font=dict(color="#94a3b8"),
            height=260,
            margin=dict(l=10, r=10, t=40, b=10),
            yaxis=dict(gridcolor="#1e293b"),
        )
        st.plotly_chart(fig_sip, use_container_width=True, config={"displayModeBar": False})

else:
    st.info("Scenario data will appear after running a FIRE calculation.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Monthly Investment Recommendation
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("💰 Monthly Investment Recommendation")

col_rec, col_extra = st.columns([1.2, 1])

with col_rec:
    ret_age = settings_disp.get("retirement_target_age", "—")
    lifestyle_val = settings_disp.get("lifestyle", "—")
    yrs = (ret_age - settings_disp.get("current_age", 0)) if isinstance(ret_age, int) else "—"

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
        border: 1px solid #059669;
        border-radius: 12px;
        padding: 24px 28px;
        text-align: center;
    ">
        <div style="font-size:13px; color:#6ee7b7; text-transform:uppercase; letter-spacing:2px; margin-bottom:8px;">
            Recommended Monthly SIP
        </div>
        <div style="font-size:44px; font-weight:800; color:#10b981; margin:8px 0;">
            {_cr(req_monthly)}
        </div>
        <div style="font-size:14px; color:#a7f3d0; margin-top:8px;">
            to retire at age <b>{ret_age}</b> with a <b>{lifestyle_val}</b> lifestyle
        </div>
        <div style="font-size:13px; color:#6ee7b7; margin-top:6px;">
            Investment horizon: <b>{yrs} years</b> &nbsp;|&nbsp; 
            Target: <b>{_cr(target_corpus)}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_extra:
    current_monthly_savings = result.get("monthly_savings", 0)
    gap = max(req_monthly - current_monthly_savings, 0)
    current_annual = annual_savings

    st.metric("Current Monthly Savings", _cr(current_monthly_savings))
    st.metric(
        "Additional Savings Needed",
        _cr(gap),
        delta="Gap to close" if gap > 0 else "Surplus!",
        delta_color="inverse" if gap > 0 else "normal",
    )
    st.metric("Annual Savings Required", _cr(req_monthly * 12))
    st.metric("Current Annual Savings", _cr(current_annual))

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 & 7 — Strengths & Weaknesses
# ─────────────────────────────────────────────────────────────────────────────

strengths = result.get("strengths", [])
weaknesses = result.get("weaknesses", [])

col_str, col_weak = st.columns(2)

with col_str:
    st.subheader("✅ Strengths")
    if strengths:
        for s in strengths:
            st.markdown(f"""
            <div style="
                background: rgba(34,197,94,0.08);
                border-left: 3px solid #22c55e;
                border-radius: 6px;
                padding: 10px 14px;
                margin-bottom: 8px;
                font-size: 14px;
                color: #d1fae5;
            ">✅ {s}</div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No specific strengths detected yet.")

with col_weak:
    st.subheader("⚠️ Areas to Improve")
    if weaknesses:
        for w in weaknesses:
            st.markdown(f"""
            <div style="
                background: rgba(245,158,11,0.08);
                border-left: 3px solid #f59e0b;
                border-radius: 6px;
                padding: 10px 14px;
                margin-bottom: 8px;
                font-size: 14px;
                color: #fef3c7;
            ">⚠️ {w}</div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No major weaknesses detected.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — FIRE AI Coach (chat interface)
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("🤖 FIRE AI Coach")
st.caption("Powered by Groq LLaMA 3.1 · Uses your live FIRE data for personalized advice.")

# Initialize chat history (separate from generic advisor)
if "fire_coach_messages" not in st.session_state:
    st.session_state.fire_coach_messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm your **FIRE Coach** 🔥\n\n"
                "I've analyzed your financial profile and I'm ready to help you achieve "
                "Financial Independence faster. What would you like to know?"
            ),
        }
    ]

# Pre-built FIRE context (built once per session after calculation)
def _get_fire_context() -> dict | None:
    if "fire_context_for_ai" not in st.session_state or st.session_state.fire_context_for_ai is None:
        if result:
            ctx = {
                "current_age": settings_disp.get("current_age"),
                "retirement_target_age": settings_disp.get("retirement_target_age"),
                "current_net_worth": round(net_worth, 2),
                "annual_income": round(annual_income, 2),
                "annual_expenses": round(annual_expenses, 2),
                "savings_rate_percent": round(savings_rate, 1),
                "fire_score": round(fire_score, 1),
                "fire_progress_percent": round(fire_progress, 1),
                "fire_target_corpus": round(target_corpus, 2),
                "estimated_fire_age": round(est_fire_age, 1),
                "years_remaining": round(years_remaining, 1),
                "required_monthly_investment": round(req_monthly, 2),
                "lifestyle": settings_disp.get("lifestyle"),
                "top_expense_category": result.get("top_expense_category", "N/A"),
                "subscription_monthly_total": result.get("subscription_monthly_total", 0),
                "goal_progress_avg_percent": result.get("goal_progress_avg", 0),
                "strengths": strengths[:3],
                "weaknesses": weaknesses[:3],
            }
            st.session_state.fire_context_for_ai = ctx
    return st.session_state.get("fire_context_for_ai")


# Suggested questions
st.markdown("**Suggested questions:**")
suggestions = [
    "Can I retire before 45?",
    "How can I reach FIRE faster?",
    "How much should I invest every month?",
    "What is slowing my FIRE progress?",
    "Which expense category should I reduce first?",
    "Can I achieve FIRE before age 40?",
]
suggestion_cols = st.columns(3)
for i, suggestion in enumerate(suggestions):
    with suggestion_cols[i % 3]:
        if st.button(suggestion, key=f"fire_suggestion_{i}", use_container_width=True):
            st.session_state.fire_coach_messages.append({"role": "user", "content": suggestion})
            with st.spinner("FIRE Coach is thinking..."):
                try:
                    fire_ctx = _get_fire_context()
                    history = st.session_state.fire_coach_messages[1:-1]
                    response = api_client.ask_fire_coach(
                        question=suggestion, history=history, fire_context=fire_ctx
                    )
                    answer = response.get("answer", "Unable to process request.")
                    st.session_state.fire_coach_messages.append(
                        {"role": "assistant", "content": answer}
                    )
                except Exception as e:
                    st.session_state.fire_coach_messages.append(
                        {"role": "assistant", "content": f"Error: {e}"}
                    )
            st.rerun()

st.markdown("---")

# Chat message history
for message in st.session_state.fire_coach_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask your FIRE Coach anything about your financial independence journey..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.fire_coach_messages.append({"role": "user", "content": prompt})

    history = st.session_state.fire_coach_messages[1:-1]

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking...")

        try:
            fire_ctx = _get_fire_context()
            response = api_client.ask_fire_coach(
                question=prompt, history=history, fire_context=fire_ctx
            )
            answer = response.get("answer", "I couldn't process that. Please try again.")
            placeholder.markdown(answer)

            with st.expander("View FIRE Context Sent to AI", expanded=False):
                ctx_display = response.get("context_summary", {})
                st.json(ctx_display)
                st.caption(f"Provider: {response.get('provider', 'unknown')}")

        except Exception as e:
            answer = f"Error communicating with FIRE Coach: {e}"
            placeholder.error(answer)

        st.session_state.fire_coach_messages.append({"role": "assistant", "content": answer})

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION — FIRE History
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("📜 FIRE Analysis History", expanded=False):
    try:
        history_records = api_client.get_fire_history(limit=10)
        if not history_records:
            st.caption("No historical analyses yet. Each time you click 'Calculate FIRE', a record is saved.")
        else:
            hist_df = pd.DataFrame(history_records)
            display_cols = {
                "created_at": "Date",
                "current_age": "Age",
                "retirement_target_age": "Target Age",
                "fire_score": "FIRE Score",
                "fire_progress": "Progress %",
                "savings_rate": "Savings Rate %",
                "estimated_fire_age": "Est. FIRE Age",
                "required_monthly_investment": "Monthly SIP",
            }
            hist_display = hist_df[[c for c in display_cols if c in hist_df.columns]].copy()
            hist_display.columns = [display_cols[c] for c in hist_display.columns]

            if "Monthly SIP" in hist_display.columns:
                hist_display["Monthly SIP"] = hist_display["Monthly SIP"].apply(lambda v: _cr(float(v)))

            st.dataframe(hist_display, use_container_width=True, hide_index=True)

            # Score trend chart
            if "fire_score" in hist_df.columns and len(hist_df) > 1:
                hist_df["created_at"] = pd.to_datetime(hist_df["created_at"])
                hist_df = hist_df.sort_values("created_at")
                fig_hist = px.line(
                    hist_df,
                    x="created_at",
                    y="fire_score",
                    title="FIRE Score Over Time",
                    labels={"created_at": "Date", "fire_score": "FIRE Score"},
                    markers=True,
                )
                fig_hist.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(15,23,42,0.5)",
                    font=dict(color="#94a3b8"),
                    height=250,
                    margin=dict(l=10, r=10, t=40, b=10),
                )
                st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

    except Exception as e:
        st.warning(f"Could not load history: {e}")
