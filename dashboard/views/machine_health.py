"""
dashboard/views/machine_health.py — Fleet Status & Digital Twin
Premium cards for each CNC machine component. No blue-block issue.
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from components import (
    section_title, spacer, health_kpi_card, risk_kpi_card,
    digital_twin, machine_card, alert_card, shap_panel,
)


def _gauge(value: float, title: str, invert: bool = False, h: int = 200) -> go.Figure:
    col = (
        "#DC2626" if (invert and value >= 60) or (not invert and value < 40) else
        "#F59E0B" if (invert and value >= 35) or (not invert and value < 70) else
        "#16A34A"
    )
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 26, "family": "Inter", "color": "#111827"}},
        gauge={
            "axis":  {"range": [0, 100], "tickwidth": 1, "tickcolor": "#E5E7EB",
                      "tickfont": {"size": 10, "color": "#9CA3AF"}},
            "bar":   {"color": col, "thickness": 0.22},
            "bgcolor": "white", "bordercolor": "#E5E7EB", "borderwidth": 1,
            "steps": [
                {"range": [0, 40],  "color": "#FEF2F2"},
                {"range": [40, 70], "color": "#FFFBEB"},
                {"range": [70, 100],"color": "#F0FDF4"},
            ] if not invert else [
                {"range": [0, 35],  "color": "#F0FDF4"},
                {"range": [35, 60], "color": "#FFFBEB"},
                {"range": [60, 100],"color": "#FEF2F2"},
            ],
        },
        title={"text": title, "font": {"size": 11, "color": "#6B7280", "family": "Inter"}},
    ))
    fig.update_layout(
        height=h, margin=dict(t=28, b=8, l=16, r=16),
        paper_bgcolor="white", plot_bgcolor="white",
        font={"family": "Inter"},
    )
    return fig


def render() -> None:
    pred       = st.session_state.prediction
    tool_pred  = pred.get("tool_prediction") or {}
    maint_pred = pred.get("maintenance_prediction") or {}
    decision   = pred.get("decision") or {}
    alerts     = st.session_state.alerts

    tool_health  = float(tool_pred.get("tool_health",             37.9) or 37.9)
    mach_health  = float(maint_pred.get("machine_health",         38.0) or 38.0)
    fail_prob    = float(maint_pred.get("failure_probability",    62.0) or 62.0)
    rul          = float(tool_pred.get("remaining_useful_life",   35.7) or 35.7)
    status       = str(decision.get("overall_status",           "Critical"))
    priority     = str(decision.get("maintenance_priority",     "Immediate"))
    failure_type = str(maint_pred.get("failure_type",           "Wear Failure"))
    breakdown    = decision.get("risk_breakdown") or {}
    machine_id   = st.session_state.last_operator_input.get("machine_id", "CNC-03")

    # ── Top KPI Row ───────────────────────────────────────────────
    spacer(8)
    section_title("Fleet Status Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1: health_kpi_card("Machine Health",  mach_health)
    with c2: health_kpi_card("Tool Health",     tool_health)
    with c3: risk_kpi_card("Failure Risk",       fail_prob)
    with c4:
        rul_col = "#2563EB" if rul > 20 else "#F59E0B" if rul > 10 else "#DC2626"
        from components import kpi_card
        kpi_card("Remaining Useful Life", f"{rul:.1f}", unit=" min", color=rul_col)

    spacer(32)

    # ── Left: Gauges | Right: Alerts ─────────────────────────────
    col_g, col_a = st.columns([3, 2])

    with col_g:
        section_title("Health Gauges")
        g1, g2, g3 = st.columns(3)
        with g1:
            st.markdown(
                '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
                'border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">',
                unsafe_allow_html=True,
            )
            fig = _gauge(mach_health, "Machine Health")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with g2:
            st.markdown(
                '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
                'border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">',
                unsafe_allow_html=True,
            )
            fig = _gauge(tool_health, "Tool Health")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with g3:
            st.markdown(
                '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
                'border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">',
                unsafe_allow_html=True,
            )
            fig = _gauge(fail_prob, "Failure Risk", invert=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

    with col_a:
        section_title("Active Alerts")
        for alert in alerts[:4]:
            alert_card(
                title    = alert.get("title", "Alert"),
                detail   = alert.get("detail", ""),
                time_str = alert.get("time", ""),
                level    = alert.get("level", "info"),
            )
        if not alerts:
            st.info("No active alerts.")

    spacer(32)

    # ── Digital Twin ──────────────────────────────────────────────
    section_title(f"Digital Twin — Machine {machine_id}")

    def _comp_status(h: float) -> str:
        return "Healthy" if h >= 70 else "Warning" if h >= 40 else "Critical"

    components = {
        "Motor":   (_comp_status(mach_health),      mach_health),
        "Tool":    (_comp_status(tool_health),       tool_health),
        "Spindle": (_comp_status(max(30, tool_health - 5)), max(30, tool_health - 5)),
        "Cooling": (_comp_status(min(85, mach_health + 15)), min(85, mach_health + 15)),
        "Power":   (_comp_status(min(90, mach_health + 20)), min(90, mach_health + 20)),
    }
    digital_twin(components)

    spacer(32)

    # ── Machine List + SHAP Panel ─────────────────────────────────
    col_m, col_s = st.columns([2, 3])

    with col_m:
        section_title("Fleet Overview")
        machines = [
            (machine_id, status, tool_health, mach_health, fail_prob),
            ("CNC-01", "Healthy", 88.0, 91.0, 12.0),
            ("CNC-07", "Warning", 52.0, 58.0, 41.0),
            ("CNC-12", "Healthy", 79.0, 83.0, 18.0),
        ]
        for mid, stat, th, mh, rk in machines:
            machine_card(
                machine_id     = mid,
                status         = stat,
                tool_health    = th,
                machine_health = mh,
                risk           = rk,
                last_pred      = "14 Jul 2026, 15:39" if mid == machine_id else "",
            )

    with col_s:
        section_title("AI Feature Influence (SHAP-style)")
        if breakdown:
            shap_panel(breakdown, f"Risk Factors — {machine_id}")
        else:
            st.info("Run a prediction to see feature influence analysis.")

        spacer(16)
        section_title("Prediction Details")
        detail_rows = [
            ("Failure Type",     failure_type),
            ("Priority",         priority),
            ("Overall Status",   status),
            ("Tool Wear (VB)",   f"{float(tool_pred.get('tool_wear',0.186) or 0.186):.4f} mm"),
            ("Machine Failure",  str(maint_pred.get("machine_failure", "Yes"))),
        ]
        rows_html = "".join(
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:8px 0;border-bottom:1px solid #F3F4F6">'
            f'<span style="font-size:12px;color:#6B7280">{label}</span>'
            f'<span style="font-size:12px;font-weight:600;color:#111827">{val}</span>'
            f'</div>'
            for label, val in detail_rows
        )
        st.markdown(
            f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
            f'padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">{rows_html}</div>',
            unsafe_allow_html=True,
        )
