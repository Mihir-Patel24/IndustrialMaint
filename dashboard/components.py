"""
dashboard/components.py — Enterprise UI Component Library v4.0
All components use CSS variables. No hardcoded colors.
No backslashes in f-strings (Python 3.11 compatible).
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from typing import Any


# ── Internal color helpers ──────────────────────────────────────
def _health_color(pct: float) -> str:
    if pct >= 70: return "#16A34A"
    if pct >= 40: return "#F59E0B"
    return "#DC2626"

def _risk_color(pct: float) -> str:
    if pct >= 60: return "#DC2626"
    if pct >= 35: return "#F59E0B"
    return "#16A34A"

def _status_class(status: str) -> str:
    s = str(status).lower()
    if "critical" in s or "high" in s: return "status-critical"
    if "warn" in s or "medium" in s:   return "status-warning"
    return "status-healthy"


# ── Utility ─────────────────────────────────────────────────────
def spacer(px: int = 16) -> None:
    st.markdown(
        f'<div style="height:{px}px;flex-shrink:0"></div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    sub_html = ""
    if subtitle:
        sub_html = f'<div style="font-size:13px;color:#6B7280;margin-top:3px">{subtitle}</div>'
    st.markdown(
        f'<div style="margin-bottom:20px">'
        f'<div style="font-size:20px;font-weight:600;color:#111827">{title}</div>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    """Renders an uppercase section label. No background."""
    st.markdown(
        f'<div style="font-size:11px;font-weight:600;letter-spacing:0.08em;'
        f'text-transform:uppercase;color:#9CA3AF;margin:0 0 14px 0">'
        f'{text}</div>',
        unsafe_allow_html=True,
    )


# ── Status & Priority Badges ─────────────────────────────────────
def status_badge(status: str, size: str = "sm") -> str:
    s = str(status).strip()
    sl = s.lower()
    if "critical" in sl:
        bg, col = "#FEF2F2", "#B91C1C"
    elif "high" in sl or "warn" in sl:
        bg, col = "#FFFBEB", "#92400E"
    elif "healthy" in sl or "good" in sl or "ok" in sl:
        bg, col = "#F0FDF4", "#15803D"
    elif "medium" in sl:
        bg, col = "#EFF6FF", "#1D4ED8"
    else:
        bg, col = "#F3F4F6", "#374151"

    fs = "10px" if size == "sm" else "12px"
    pad = "2px 8px" if size == "sm" else "4px 12px"
    return (
        f'<span style="background:{bg};color:{col};font-size:{fs};'
        f'font-weight:600;padding:{pad};border-radius:20px;'
        f'white-space:nowrap;letter-spacing:0.02em">{s}</span>'
    )


def priority_badge(priority: str) -> str:
    pl = str(priority).lower()
    if "immediate" in pl or "critical" in pl:
        bg, col, dot = "#FEF2F2", "#B91C1C", "#DC2626"
    elif "high" in pl:
        bg, col, dot = "#FFFBEB", "#92400E", "#F59E0B"
    elif "medium" in pl or "mid" in pl:
        bg, col, dot = "#EFF6FF", "#1D4ED8", "#2563EB"
    else:
        bg, col, dot = "#F0FDF4", "#15803D", "#16A34A"

    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{bg};color:{col};font-size:11px;font-weight:600;'
        f'padding:3px 10px;border-radius:20px">'
        f'<span style="width:6px;height:6px;border-radius:50%;'
        f'background:{dot};flex-shrink:0"></span>{priority}</span>'
    )


# ── KPI Card (5-per-row, with progress bar) ──────────────────────
def kpi_card(label: str, value: str, unit: str = "",
             color: str = "#111827", delta: str = "") -> None:
    delta_html = ""
    if delta:
        is_pos = delta.startswith("+")
        dcol = "#16A34A" if is_pos else "#DC2626"
        delta_html = (
            f'<div style="font-size:11px;color:{dcol};font-weight:500;'
            f'margin-top:4px">{delta}</div>'
        )
    unit_html = ""
    if unit:
        unit_html = f'<span style="font-size:13px;font-weight:400;color:#6B7280;margin-left:3px">{unit}</span>'

    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
        f'padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        f'<div style="font-size:11px;font-weight:600;letter-spacing:0.07em;'
        f'text-transform:uppercase;color:#9CA3AF;margin-bottom:10px;'
        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{label}</div>'
        f'<div style="font-size:26px;font-weight:700;color:{color};line-height:1.1">'
        f'{value}{unit_html}</div>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def health_kpi_card(label: str, pct: float) -> None:
    col = _health_color(pct)
    if pct >= 70:
        status, stcol, stbg = "Healthy", "#15803D", "#F0FDF4"
    elif pct >= 40:
        status, stcol, stbg = "Warning", "#92400E", "#FFFBEB"
    else:
        status, stcol, stbg = "Critical", "#B91C1C", "#FEF2F2"

    bar_w = max(0, min(100, pct))

    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
        f'padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        f'<div style="font-size:11px;font-weight:600;letter-spacing:0.07em;'
        f'text-transform:uppercase;color:#9CA3AF;margin-bottom:10px">{label}</div>'
        f'<div style="font-size:26px;font-weight:700;color:{col};line-height:1.1">'
        f'{pct:.0f}%</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px">'
        f'<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;'
        f'background:{stbg};color:{stcol}">{status}</span>'
        f'</div>'
        f'<div style="height:3px;border-radius:2px;background:#E5E7EB;margin-top:10px">'
        f'<div style="height:100%;width:{bar_w:.0f}%;border-radius:2px;background:{col};'
        f'transition:width 0.4s ease"></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def risk_kpi_card(label: str, risk: float) -> None:
    col = _risk_color(risk)
    if risk >= 60:
        status, stcol, stbg = "High Risk", "#B91C1C", "#FEF2F2"
    elif risk >= 35:
        status, stcol, stbg = "Medium", "#92400E", "#FFFBEB"
    else:
        status, stcol, stbg = "Low Risk", "#15803D", "#F0FDF4"

    bar_w = max(0, min(100, risk))

    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
        f'padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        f'<div style="font-size:11px;font-weight:600;letter-spacing:0.07em;'
        f'text-transform:uppercase;color:#9CA3AF;margin-bottom:10px">{label}</div>'
        f'<div style="font-size:26px;font-weight:700;color:{col};line-height:1.1">'
        f'{risk:.0f}%</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px">'
        f'<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;'
        f'background:{stbg};color:{stcol}">{status}</span>'
        f'</div>'
        f'<div style="height:3px;border-radius:2px;background:#E5E7EB;margin-top:10px">'
        f'<div style="height:100%;width:{bar_w:.0f}%;border-radius:2px;background:{col};'
        f'transition:width 0.4s ease"></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Gauge Card (Plotly) ──────────────────────────────────────────
def gauge_card(value: float, title: str, invert: bool = False) -> None:
    if invert:
        color = _risk_color(value)
    else:
        color = _health_color(value)

    fig = go.Figure(go.Indicator(
        mode   = "gauge+number",
        value  = value,
        number = {"suffix": "%", "font": {"size": 28, "family": "Inter", "color": "#111827"}},
        gauge  = {
            "axis":  {"range": [0, 100], "tickwidth": 1, "tickcolor": "#E5E7EB",
                      "tickfont": {"size": 10, "color": "#9CA3AF"}},
            "bar":   {"color": color, "thickness": 0.22},
            "bgcolor":    "white",
            "bordercolor": "#E5E7EB",
            "borderwidth": 1,
            "steps": [
                {"range": [0,  35], "color": "#F0FDF4"},
                {"range": [35, 70], "color": "#FFFBEB"},
                {"range": [70,100], "color": "#FEF2F2"},
            ] if invert else [
                {"range": [0,  40], "color": "#FEF2F2"},
                {"range": [40, 70], "color": "#FFFBEB"},
                {"range": [70,100], "color": "#F0FDF4"},
            ],
        },
        title = {"text": title, "font": {"size": 12, "color": "#6B7280", "family": "Inter"}},
    ))
    fig.update_layout(
        height=200, margin=dict(t=30, b=10, l=20, r=20),
        paper_bgcolor="white", plot_bgcolor="white",
        font={"family": "Inter"},
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Alert Card ───────────────────────────────────────────────────
def alert_card(title: str, detail: str, time_str: str, level: str = "info") -> None:
    lvl = level.lower()
    if "critical" in lvl or "error" in lvl:
        border, bg, col, dot = "#FECACA", "#FEF9F9", "#B91C1C", "#DC2626"
    elif "warning" in lvl or "warn" in lvl:
        border, bg, col, dot = "#FDE68A", "#FFFDF5", "#92400E", "#F59E0B"
    elif "success" in lvl or "ok" in lvl:
        border, bg, col, dot = "#BBF7D0", "#F9FFFE", "#15803D", "#16A34A"
    else:
        border, bg, col, dot = "#BFDBFE", "#F5F9FF", "#1D4ED8", "#2563EB"

    st.markdown(
        f'<div style="background:{bg};border:1px solid {border};border-left:3px solid {dot};'
        f'border-radius:8px;padding:12px 14px;margin-bottom:8px">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
        f'<div style="font-size:13px;font-weight:600;color:{col};margin-bottom:3px">{title}</div>'
        f'<div style="font-size:11px;color:#9CA3AF;white-space:nowrap;margin-left:12px">{time_str}</div>'
        f'</div>'
        f'<div style="font-size:12px;color:#6B7280;line-height:1.5">{detail}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Recommendation Card ──────────────────────────────────────────
def recommendation_card(action: str, priority: str, eta: str = "") -> None:
    pl = priority.lower()
    if "immediate" in pl or "critical" in pl:
        icon, col = "🔴", "#B91C1C"
    elif "high" in pl:
        icon, col = "🟠", "#92400E"
    elif "medium" in pl:
        icon, col = "🔵", "#1D4ED8"
    else:
        icon, col = "🟢", "#15803D"

    eta_html = ""
    if eta:
        eta_html = f'<div style="font-size:11px;color:#9CA3AF;margin-top:4px">⏱ {eta}</div>'

    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;'
        f'padding:14px 16px;margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,0.04)">'
        f'<div style="display:flex;gap:10px;align-items:flex-start">'
        f'<span style="font-size:16px;flex-shrink:0;margin-top:1px">{icon}</span>'
        f'<div>'
        f'<div style="font-size:13px;font-weight:500;color:#111827;line-height:1.4">{action}</div>'
        f'{eta_html}'
        f'</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Risk Breakdown Bars ──────────────────────────────────────────
def risk_breakdown_bars(breakdown: dict[str, float]) -> None:
    if not breakdown:
        return
    items = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    rows = []
    for k, v in items:
        label = k.replace("_", " ").title()
        val   = max(0.0, min(100.0, float(v)))
        col   = _risk_color(val)
        pct   = f"{val:.1f}"
        rows.append(
            f'<div style="margin-bottom:14px">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
            f'<span style="font-size:12px;color:#6B7280">{label}</span>'
            f'<span style="font-size:12px;font-weight:600;color:{col}">{pct}</span>'
            f'</div>'
            f'<div style="height:4px;background:#F3F4F6;border-radius:2px">'
            f'<div style="height:100%;width:{val:.0f}%;background:{col};'
            f'border-radius:2px;transition:width 0.4s ease"></div>'
            f'</div></div>'
        )
    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
        'padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        '<div style="font-size:12px;font-weight:600;color:#374151;margin-bottom:16px">'
        'RISK FACTOR BREAKDOWN</div>' + "".join(rows) + "</div>",
        unsafe_allow_html=True,
    )


# ── AI Insight Card ──────────────────────────────────────────────
def ai_insight_card(machine_id: str, risk: float, message: str,
                    action: str, confidence: float = 88.0) -> None:
    risk_col = _risk_color(risk)
    if risk >= 60:
        border_col, bg_col = "#FECACA", "#FFFAFA"
        icon = "⚠️"
    elif risk >= 35:
        border_col, bg_col = "#FDE68A", "#FFFEF5"
        icon = "🔔"
    else:
        border_col, bg_col = "#BBF7D0", "#F7FFFA"
        icon = "✅"

    conf_bar = max(0, min(100, confidence))

    st.markdown(
        f'<div style="background:{bg_col};border:1px solid {border_col};'
        f'border-radius:12px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">'
        f'<span style="font-size:18px">{icon}</span>'
        f'<div style="font-size:11px;font-weight:600;letter-spacing:0.06em;'
        f'text-transform:uppercase;color:{risk_col}">AI INSIGHT</div>'
        f'<span style="margin-left:auto;font-size:11px;font-weight:600;'
        f'background:#F3F4F6;color:#374151;padding:2px 8px;border-radius:20px">'
        f'Machine {machine_id}</span>'
        f'</div>'
        f'<div style="font-size:13px;color:#374151;line-height:1.6;margin-bottom:14px">'
        f'{message}</div>'
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;'
        f'padding:10px 14px;font-size:12px;font-weight:500;color:#374151;margin-bottom:12px">'
        f'▶ {action}</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span style="font-size:11px;color:#9CA3AF">Confidence</span>'
        f'<span style="font-size:12px;font-weight:600;color:#374151">{confidence:.1f}%</span>'
        f'</div>'
        f'<div style="height:3px;background:#E5E7EB;border-radius:2px;margin-top:6px">'
        f'<div style="height:100%;width:{conf_bar:.0f}%;background:#2563EB;border-radius:2px"></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


# ── Decision Fusion Flow ─────────────────────────────────────────
def fusion_flow(
    tool_pred:   dict[str, Any],
    maint_pred:  dict[str, Any],
    decision:    dict[str, Any],
    recommendation: dict[str, Any],
) -> None:
    vb       = float(tool_pred.get("tool_wear",                0) or 0)
    rul      = float(tool_pred.get("remaining_useful_life",    0) or 0)
    fp       = float(maint_pred.get("failure_probability",     0) or 0)
    ft       = str(maint_pred.get("failure_type",   "—") or "—")
    risk     = float(decision.get("overall_risk",              0) or 0)
    status   = str(decision.get("overall_status",  "—") or "—")
    priority = str(decision.get("maintenance_priority", "—") or "—")
    actions  = recommendation.get("operator_actions", []) or []

    risk_col = _risk_color(risk)
    status_badge_html = status_badge(status)

    steps = [
        ("📡", "NASA Tool Wear Model",        f"VB = {vb:.4f} mm · RUL = {rul:.1f} min", "#2563EB"),
        ("🤖", "AI4I Failure Prediction",     f"Failure Prob = {fp:.1f}% · Type: {ft}",   "#7C3AED"),
        ("🔀", "Decision Fusion Engine",      f"Weighted risk fusion across both models",  "#0891B2"),
        ("📊", "Risk Assessment",             f"Overall Risk = {risk:.0f}% · {status_badge_html}", risk_col),
        ("🔧", "Maintenance Recommendation",  actions[0] if actions else "Monitor system", "#059669"),
    ]

    html = (
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
        'padding:24px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        '<div style="font-size:12px;font-weight:600;letter-spacing:0.07em;'
        'text-transform:uppercase;color:#9CA3AF;margin-bottom:20px">DECISION FUSION PIPELINE</div>'
    )
    for i, (icon, title, detail, col) in enumerate(steps):
        connector = ""
        if i < len(steps) - 1:
            connector = (
                '<div style="display:flex;justify-content:flex-start;padding-left:28px;'
                'margin:0 0 4px 0">'
                '<div style="width:2px;height:20px;background:#E5E7EB"></div></div>'
            )
        html += (
            f'<div style="display:flex;align-items:flex-start;gap:14px;margin-bottom:4px">'
            f'<div style="width:36px;height:36px;border-radius:10px;background:{col}18;'
            f'display:flex;align-items:center;justify-content:center;flex-shrink:0;'
            f'font-size:16px">{icon}</div>'
            f'<div style="padding-top:2px;flex:1;min-width:0">'
            f'<div style="font-size:13px;font-weight:600;color:#111827">{title}</div>'
            f'<div style="font-size:12px;color:#6B7280;margin-top:1px;line-height:1.4">'
            f'{detail}</div></div></div>'
        ) + connector
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── SHAP Explanation Panel ───────────────────────────────────────
def shap_panel(breakdown: dict[str, float], title: str = "Feature Influence") -> None:
    if not breakdown:
        return
    items = sorted(breakdown.items(), key=lambda x: abs(x[1]), reverse=True)[:6]
    max_val = max(abs(v) for _, v in items) or 1.0

    rows = []
    for k, v in items:
        label = k.replace("_", " ").title()
        val   = float(v)
        w     = abs(val) / max_val * 100.0
        col   = "#DC2626" if val > 0 else "#16A34A"
        dir_label = "+Risk" if val > 0 else "-Risk"
        rows.append(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
            f'<div style="width:130px;font-size:12px;color:#374151;'
            f'text-align:right;flex-shrink:0">{label}</div>'
            f'<div style="flex:1;background:#F3F4F6;border-radius:3px;height:16px;'
            f'position:relative;overflow:hidden">'
            f'<div style="height:100%;width:{w:.0f}%;background:{col};'
            f'border-radius:3px;opacity:0.7"></div></div>'
            f'<div style="width:50px;font-size:11px;font-weight:600;'
            f'color:{col}">{dir_label}</div>'
            f'</div>'
        )
    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
        f'padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        f'<div style="font-size:12px;font-weight:600;color:#374151;margin-bottom:16px">'
        f'{title.upper()}</div>'
        + "".join(rows) + "</div>",
        unsafe_allow_html=True,
    )


# ── Digital Twin Component Card ──────────────────────────────────
def digital_twin(components: dict[str, tuple[str, float]]) -> None:
    icons = {
        "Motor": "⚙️", "Tool": "🔩", "Spindle": "🔄",
        "Cooling": "❄️", "Power": "⚡",
    }
    cols = st.columns(len(components))
    for i, (comp_name, (status_str, health_pct)) in enumerate(components.items()):
        col      = _health_color(health_pct)
        sl       = status_str.lower()
        bg       = "#F0FDF4" if "healthy" in sl else "#FFFBEB" if "warning" in sl else "#FEF2F2"
        border   = "#BBF7D0" if "healthy" in sl else "#FDE68A" if "warning" in sl else "#FECACA"
        icon     = icons.get(comp_name, "📦")
        bar_col  = col
        bar_w    = max(0, min(100, health_pct))

        with cols[i]:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};'
                f'border-radius:12px;padding:18px 16px;text-align:center;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.05)">'
                f'<div style="font-size:24px;margin-bottom:8px">{icon}</div>'
                f'<div style="font-size:12px;font-weight:600;color:#374151;'
                f'margin-bottom:6px">{comp_name}</div>'
                f'<div style="font-size:22px;font-weight:700;color:{col};'
                f'line-height:1">{health_pct:.0f}%</div>'
                f'<div style="height:3px;background:#E5E7EB;border-radius:2px;margin:10px 0 8px">'
                f'<div style="height:100%;width:{bar_w:.0f}%;background:{bar_col};'
                f'border-radius:2px"></div></div>'
                f'<div style="font-size:10px;font-weight:600;padding:2px 8px;'
                f'border-radius:20px;background:#FFFFFF;color:{col};'
                f'display:inline-block">{status_str.title()}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Machine Card ─────────────────────────────────────────────────
def machine_card(machine_id: str, status: str, tool_health: float,
                 machine_health: float, risk: float, last_pred: str = "") -> None:
    th_col    = _health_color(tool_health)
    mh_col    = _health_color(machine_health)
    rk_col    = _risk_color(risk)
    last_html = (
        f'<div style="font-size:11px;color:#9CA3AF;margin-top:8px">Last: {last_pred}</div>'
        if last_pred else ""
    )
    badge_html = status_badge(status)

    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
        f'padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,0.06);margin-bottom:8px">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'margin-bottom:14px">'
        f'<span style="font-size:14px;font-weight:600;color:#111827">{machine_id}</span>'
        f'{badge_html}</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">'
        f'<div><div style="font-size:10px;color:#9CA3AF;text-transform:uppercase;'
        f'letter-spacing:0.05em;margin-bottom:4px">Tool</div>'
        f'<div style="font-size:18px;font-weight:700;color:{th_col}">{tool_health:.0f}%</div></div>'
        f'<div><div style="font-size:10px;color:#9CA3AF;text-transform:uppercase;'
        f'letter-spacing:0.05em;margin-bottom:4px">Machine</div>'
        f'<div style="font-size:18px;font-weight:700;color:{mh_col}">{machine_health:.0f}%</div></div>'
        f'<div><div style="font-size:10px;color:#9CA3AF;text-transform:uppercase;'
        f'letter-spacing:0.05em;margin-bottom:4px">Risk</div>'
        f'<div style="font-size:18px;font-weight:700;color:{rk_col}">{risk:.0f}%</div></div>'
        f'</div>{last_html}</div>',
        unsafe_allow_html=True,
    )


# ── Panel helpers ─────────────────────────────────────────────────
def panel(title: str, subtitle: str = "") -> str:
    sub = (
        f'<div style="font-size:12px;color:#9CA3AF;margin-top:2px">{subtitle}</div>'
        if subtitle else ""
    )
    return (
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
        'border-radius:12px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        f'<div style="font-size:14px;font-weight:600;color:#111827;'
        f'margin-bottom:16px">{title}{sub}</div>'
    )


def panel_end() -> str:
    return "</div>"
