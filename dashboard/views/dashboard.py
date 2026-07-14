"""
dashboard/views/dashboard.py — Operations Control Center
Clean 5-KPI layout, trend charts, AI insights, decision fusion.
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import random
from components import (
    section_title, spacer, health_kpi_card, risk_kpi_card, kpi_card,
    ai_insight_card, fusion_flow, alert_card, recommendation_card,
    risk_breakdown_bars,
)


def _sparkline(data: list, color: str = "#2563EB", height: int = 80) -> go.Figure:
    fig = go.Figure(go.Scatter(
        y=data, mode="lines+markers",
        line=dict(color=color, width=2, shape="spline"),
        marker=dict(size=4, color=color),
        fill="tozeroy",
        fillcolor=color.replace(")", ",0.08)").replace("rgb", "rgba")
                   if color.startswith("rgb") else color + "14",
    ))
    fig.update_layout(
        height=height, margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def _trend_card(title: str, value: str, data: list, color: str) -> None:
    fig = go.Figure(go.Scatter(
        y=data, mode="lines+markers",
        line=dict(color=color, width=2, shape="spline"),
        marker=dict(size=4, color=color),
        fill="tozeroy",
        fillcolor=color + "18",
    ))
    fig.update_layout(
        height=110, margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
        f'padding:16px 18px 8px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        f'<div style="font-size:11px;font-weight:600;letter-spacing:0.07em;'
        f'text-transform:uppercase;color:#9CA3AF;margin-bottom:6px">{title}</div>'
        f'<div style="font-size:22px;font-weight:700;color:{color};line-height:1">'
        f'{value}</div></div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render() -> None:
    pred = st.session_state.prediction

    # Pull values
    tool_pred   = pred.get("tool_prediction") or {}
    maint_pred  = pred.get("maintenance_prediction") or {}
    decision    = pred.get("decision") or {}
    rec         = pred.get("recommendation") or {}

    tool_health    = float(tool_pred.get("tool_health", 37.9) or 37.9)
    mach_health    = float(maint_pred.get("machine_health", 38.0) or 38.0)
    fail_prob      = float(maint_pred.get("failure_probability", 62.0) or 62.0)
    rul            = float(tool_pred.get("remaining_useful_life", 35.7) or 35.7)
    overall_risk   = float(decision.get("overall_risk", 62.0) or 62.0)
    priority       = str(decision.get("maintenance_priority", "Immediate"))
    failure_type   = str(maint_pred.get("failure_type", "Wear Failure"))
    alerts         = st.session_state.alerts
    n_crit         = sum(1 for a in alerts if a.get("level") == "critical")
    actions        = rec.get("operator_actions") or ["Monitor system"]
    risk_breakdown = decision.get("risk_breakdown") or {}

    # ── 5 KPI CARDS ──────────────────────────────────────────────
    spacer(8)
    section_title("Key Performance Indicators")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: health_kpi_card("Machine Health", mach_health)
    with c2: health_kpi_card("Tool Health", tool_health)
    with c3: risk_kpi_card("Failure Risk", fail_prob)
    with c4:
        kpi_card(
            "Remaining Useful Life",
            f"{rul:.1f}",
            unit=" min",
            color="#2563EB" if rul > 20 else "#F59E0B" if rul > 10 else "#DC2626",
        )
    with c5:
        kpi_card(
            "Critical Alerts",
            str(n_crit),
            color="#DC2626" if n_crit > 0 else "#16A34A",
            delta=f"{n_crit} Requires action" if n_crit else "All Clear",
        )

    spacer(32)

    # ── TREND MONITORING ──────────────────────────────────────────
    section_title("Trend Monitoring — Last 10 Readings")
    # Simulated trend data
    rng = random.Random(42)
    mh_data  = [max(10, mach_health + rng.uniform(-5, 3)) for _ in range(10)]
    fr_data  = [max(0, fail_prob  + rng.uniform(-4, 4)) for _ in range(10)]
    tw_data  = [max(0, 0.186     + rng.uniform(-0.01, 0.01)) for _ in range(10)]
    rul_data = [max(0, rul       + rng.uniform(-3, 3)) for _ in range(10)]

    tc1, tc2, tc3, tc4 = st.columns(4)
    with tc1: _trend_card("Machine Health Trend", f"{mach_health:.1f}%", mh_data,  "#F59E0B")
    with tc2: _trend_card("Failure Risk Trend",   f"{fail_prob:.1f}%",   fr_data,  "#DC2626")
    with tc3: _trend_card("Tool Wear Trend",       f"{0.186:.4f} mm",    tw_data,  "#F59E0B")
    with tc4: _trend_card("RUL Trend",             f"{rul:.1f} min",     rul_data, "#2563EB")

    spacer(32)

    # ── AI INSIGHTS + ACTIONS ────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        section_title("AI Insights")
        ai_insight_card(
            machine_id  = st.session_state.last_operator_input.get("machine_id", "CNC-03"),
            risk        = overall_risk,
            message     = (
                f"Machine is at <strong>{fail_prob:.0f}%</strong> failure risk with "
                f"predicted <strong>{failure_type}</strong>. "
                f"Tool health has dropped to <strong>{tool_health:.0f}%</strong>. "
                f"Remaining useful life: <strong>{rul:.1f} minutes</strong>."
            ),
            action      = actions[0] if actions else "Monitor system carefully",
            confidence  = pred.get("metadata", {}).get("pm_model_confidence", 91.2) or 91.2,
        )

    with col_right:
        section_title("Action Items")
        for a in actions[:3]:
            recommendation_card(a, priority)

        if not actions:
            recommendation_card("Continue normal operation", "Low")

    spacer(32)

    # ── DECISION FUSION ───────────────────────────────────────────
    section_title("Decision Fusion Pipeline")
    fusion_flow(
        tool_pred   = tool_pred,
        maint_pred  = maint_pred,
        decision    = decision,
        recommendation = rec,
    )

    spacer(32)

    # ── RISK BREAKDOWN + ALERTS ───────────────────────────────────
    col_rb, col_al = st.columns([1, 1])

    with col_rb:
        section_title("Risk Factor Breakdown")
        if risk_breakdown:
            risk_breakdown_bars(risk_breakdown)
        else:
            st.info("Run a prediction to see risk breakdown.")

    with col_al:
        section_title("Recent Alerts")
        for alert in alerts[:4]:
            alert_card(
                title    = alert.get("title", "Alert"),
                detail   = alert.get("detail", ""),
                time_str = alert.get("time", ""),
                level    = alert.get("level", "info"),
            )
        if not alerts:
            st.info("No active alerts.")
