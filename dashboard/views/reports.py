"""
views/reports.py — Prediction History, Analytics & Export (Phase 4)
=====================================================================
• DB-backed prediction history (persistent across sessions)
• Analytics charts: risk trend, status distribution, health over time
• Scheduled report generator (weekly / monthly summary PDF)
• Batch CSV export for all DB predictions
• Per-prediction PDF/TXT export (existing, preserved)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_client import get_model_info
from components import kpi_card, spacer, status_badge, section_title
from auth.auth_service import auth
from auth.rbac import has_permission

try:
    from database.db_client import db
    from utils.pdf_generator import generate_pdf_report, generate_summary_report
except Exception:
    db = None
    generate_pdf_report = None
    generate_summary_report = None

_SLATE  = "#1e293b"
_GRAY   = "#64748b"
_LGRAY  = "#94a3b8"
_BORDER = "#e2e8f0"
_WHITE  = "#ffffff"
_GREEN  = "#16a34a"
_AMBER  = "#d97706"
_RED    = "#dc2626"
_BLUE   = "#111827"

_STATUS_COLORS = {
    "Critical": _RED, "Warning": _AMBER,
    "Healthy": _GREEN, "Normal": _GREEN,
}


def _build_txt_report(pred: dict, info: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "=" * 65,
        "  INDUSTRIALMAINT — PREDICTIVE MAINTENANCE REPORT",
        "=" * 65,
        f"  Generated      : {now}",
        f"  Report ID      : RPT-{datetime.now().strftime('%Y%m%d%H%M')}",
        f"  Data Source    : {pred.get('source', '—')}",
        "",
        "MODEL INFORMATION",
        "-" * 40,
        f"  Model          : {info.get('model_name', '—')}",
        f"  Features       : {info.get('feature_count', '—')}",
        f"  VB R²          : {info.get('vb_r2', '—')}",
        f"  VB MAE         : {info.get('vb_mae_mm', '—')} mm",
        f"  RUL R²         : {info.get('rul_r2', '—')}",
        f"  RUL MAE        : {info.get('rul_mae_min', '—')} min",
        "",
        "PREDICTION SUMMARY",
        "-" * 40,
        f"  Tool Health        : {pred['tool_health']:.1f}%",
        f"  Machine Health     : {pred.get('machine_health', 0):.1f}%",
        f"  Failure Risk       : {pred['failure_risk']}%",
        f"  Failure Probability: {pred.get('failure_probability', 0):.1f}%",
        f"  Tool Wear (VB)     : {pred['vb']:.4f} mm",
        f"  Remaining Useful Life: {pred['rul']:.2f} min",
        f"  Wear Level         : {pred.get('wear_level', '—')}",
        f"  Machine Status     : {pred['machine_status']}",
        f"  Failure Type       : {pred.get('failure_type', '—')}",
        f"  Severity           : {pred.get('severity_level', '—')}",
        f"  Maintenance Priority: {pred.get('maintenance_priority', '—')}",
        "",
        "RECOMMENDATIONS",
        "-" * 40,
        f"  Actions    : {'; '.join(pred.get('recommended_actions', []) or ['—'])}",
        f"  Components : {'; '.join(pred.get('recommended_components', []) or ['—'])}",
        f"  Schedule   : {pred.get('maintenance_schedule', '—')}",
        f"  Replace Tool   : {'Yes' if pred.get('should_replace_tool') else 'No'}",
        f"  Inspect Spindle: {'Yes' if pred.get('should_inspect_spindle') else 'No'}",
        "",
        "METADATA",
        "-" * 40,
        f"  Prediction Time : {pred.get('metadata', {}).get('prediction_time', '—')}",
        f"  Processing Time : {pred.get('metadata', {}).get('processing_time_ms', 0)} ms",
        f"  Tool Model      : {pred.get('metadata', {}).get('tool_model_version', '—')}",
        f"  PM Model        : {pred.get('metadata', {}).get('pm_model_version', '—')}",
        "", "=" * 65,
    ]
    return "\n".join(lines)


def _pred_to_row(p: dict, ts: str = "") -> dict:
    meta = p.get("metadata") or {}
    pt = meta.get("prediction_time", ts) or ts
    if "T" in str(pt):
        pt = str(pt).replace("T", " ")[:19]
    return {
        "Timestamp":               pt or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Machine ID":              p.get("machine_id", "—"),
        "Machine Status":          p.get("machine_status", "—"),
        "Tool Health (%)":         round(p.get("tool_health", 0), 1),
        "Machine Health (%)":      round(p.get("machine_health", 0), 1),
        "Tool Wear (mm)":          round(p.get("tool_wear", p.get("vb", 0)), 4),
        "RUL (min)":               round(p.get("remaining_rul", p.get("rul", 0)), 2),
        "Failure Risk (%)":        p.get("failure_risk", 0),
        "Failure Probability (%)": round(p.get("failure_prob", p.get("failure_probability", 0)), 1),
        "Failure Type":            p.get("failure_type", "—"),
        "Severity":                p.get("severity_level", "—"),
        "Wear Level":              p.get("wear_level", "—"),
        "Maintenance Priority":    p.get("maintenance_priority", "—"),
        "Source":                  p.get("source", "—"),
    }


def _db_pred_to_row(p: dict) -> dict:
    """Convert a DB prediction row to a display row."""
    ts = str(p.get("created_at", ""))[:16].replace("T", " ")
    return {
        "Timestamp":               ts,
        "Machine ID":              p.get("machine_id", "—"),
        "Machine Status":          p.get("machine_status", "—"),
        "Tool Health (%)":         round(float(p.get("tool_health", 0) or 0), 1),
        "Machine Health (%)":      round(float(p.get("machine_health", 0) or 0), 1),
        "Tool Wear (mm)":          round(float(p.get("tool_wear", 0) or 0), 4),
        "RUL (min)":               round(float(p.get("remaining_rul", 0) or 0), 2),
        "Failure Risk (%)":        float(p.get("failure_risk", 0) or 0),
        "Failure Probability (%)": round(float(p.get("failure_prob", 0) or 0), 1),
        "Failure Type":            p.get("failure_type", "—") or "—",
        "Maintenance Priority":    p.get("maintenance_priority", "—"),
        "Source":                  p.get("source", "db"),
    }


# ─────────────────────────────────────────────────────────────────
#  ANALYTICS CHARTS
# ─────────────────────────────────────────────────────────────────

def _chart_risk_trend(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Timestamp"], y=df["Failure Risk (%)"],
        mode="lines+markers",
        name="Failure Risk",
        line=dict(color="#DC2626", width=2),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(220,38,38,0.08)",
    ))
    fig.add_hline(y=60, line_dash="dash", line_color="#D97706",
                  annotation_text="Alert threshold (60%)",
                  annotation_position="top right")
    fig.update_layout(
        title=None, height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white", plot_bgcolor="#F8FAFC",
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", title="Risk %", range=[0, 105]),
        font=dict(family="Inter, sans-serif", size=11),
        legend=dict(orientation="h", y=1.05),
    )
    return fig


def _chart_health_trend(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Timestamp"], y=df["Tool Health (%)"],
        mode="lines+markers", name="Tool Health",
        line=dict(color="#2563EB", width=2), marker=dict(size=5),
    ))
    fig.add_trace(go.Scatter(
        x=df["Timestamp"], y=df["Machine Health (%)"],
        mode="lines+markers", name="Machine Health",
        line=dict(color="#16A34A", width=2, dash="dot"), marker=dict(size=5),
    ))
    fig.update_layout(
        title=None, height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white", plot_bgcolor="#F8FAFC",
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", title="Health %", range=[0, 105]),
        font=dict(family="Inter, sans-serif", size=11),
        legend=dict(orientation="h", y=1.05),
    )
    return fig


def _chart_status_dist(df: pd.DataFrame) -> go.Figure:
    counts = df["Machine Status"].value_counts()
    colors = [_STATUS_COLORS.get(s, _GRAY) for s in counts.index]
    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11),
    ))
    fig.update_layout(
        title=None, height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        legend=dict(orientation="h", y=-0.1),
        showlegend=True,
    )
    return fig


def _chart_failure_bar(df: pd.DataFrame) -> go.Figure:
    ft_counts = df["Failure Type"].value_counts().reset_index()
    ft_counts.columns = ["Failure Type", "Count"]
    fig = px.bar(
        ft_counts, x="Failure Type", y="Count",
        color="Count",
        color_continuous_scale=[[0, "#BFDBFE"], [0.5, "#2563EB"], [1, "#1E3A5F"]],
    )
    fig.update_layout(
        title=None, height=260, showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white", plot_bgcolor="#F8FAFC",
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", title="Count"),
        font=dict(family="Inter, sans-serif", size=11),
        coloraxis_showscale=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────
#  MAIN RENDER
# ─────────────────────────────────────────────────────────────────

def render():
    pred    = st.session_state.prediction
    history = st.session_state.get("prediction_history", [])
    info    = get_model_info()
    user    = auth.current_user() or {}
    uid     = user.get("id", "")

    # ── Load DB predictions ───────────────────────────────────────
    db_preds: list[dict] = []
    db_available = False
    if db is not None and uid:
        try:
            db_preds = db.get_user_predictions(uid, limit=200)
            db_available = True
        except Exception:
            db_preds = []

    # Merge session + DB (DB is primary when available)
    if db_available and db_preds:
        all_rows = [_db_pred_to_row(p) for p in db_preds]
    elif history:
        all_rows = [_pred_to_row(p) for p in history]
    else:
        all_rows = [_pred_to_row(pred)]

    total_count = len(all_rows)
    avg_risk    = sum(r.get("Failure Risk (%)", 0) for r in all_rows) / total_count if total_count else 0
    avg_health  = sum(r.get("Tool Health (%)", 0) for r in all_rows) / total_count if total_count else 0
    critical_n  = sum(1 for r in all_rows if r.get("Machine Status") == "Critical")

    # ── KPI strip ─────────────────────────────────────────────────
    section_title("Report Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("Total Predictions", str(total_count),
                      "DB" if db_available else "Session", color=_BLUE)
    with c2: kpi_card("Avg Failure Risk", f"{avg_risk:.1f}%",
                      "Across all runs",
                      color=_RED if avg_risk >= 60 else _AMBER if avg_risk >= 30 else _GREEN)
    with c3: kpi_card("Avg Tool Health", f"{avg_health:.1f}%", "Across all runs",
                      color=_GREEN if avg_health >= 60 else _AMBER)
    with c4: kpi_card("Critical Events", str(critical_n), "Machine status",
                      color=_RED if critical_n > 0 else _GREEN)
    with c5: kpi_card("Model VB R²", str(info.get("vb_r2", "—")), "Tool wear accuracy")

    spacer(16)

    # ── Filters ───────────────────────────────────────────────────
    section_title("Search & Filters")
    f0, f1, f2, f3 = st.columns([2, 1, 1, 1])
    with f0:
        search_q = st.text_input("🔍 Search predictions…",
                                 placeholder="Machine ID, Status, Failure Type",
                                 key="rpt_search", label_visibility="collapsed")
    with f1:
        status_filter = st.selectbox("Status", ["All", "Critical", "Warning", "Healthy"], key="rpt_status")
    with f2:
        risk_filter = st.selectbox("Risk Level", ["All", "High (≥60%)", "Medium (30-60%)", "Low (<30%)"], key="rpt_risk")
    with f3:
        machine_ids = ["All"] + sorted({r.get("Machine ID", "—") for r in all_rows if r.get("Machine ID", "—") != "—"})
        machine_filter = st.selectbox("Machine", machine_ids, key="rpt_machine")

    spacer(8)

    # ── Build filtered dataframe ──────────────────────────────────
    df = pd.DataFrame(all_rows)
    if not df.empty:
        if search_q:
            mask = df.apply(lambda row: search_q.lower() in str(row.values).lower(), axis=1)
            df = df[mask]
        if status_filter != "All":
            df = df[df["Machine Status"] == status_filter]
        if risk_filter == "High (≥60%)":
            df = df[df["Failure Risk (%)"] >= 60]
        elif risk_filter == "Medium (30-60%)":
            df = df[(df["Failure Risk (%)"] >= 30) & (df["Failure Risk (%)"] < 60)]
        elif risk_filter == "Low (<30%)":
            df = df[df["Failure Risk (%)"] < 30]
        if machine_filter != "All":
            df = df[df["Machine ID"] == machine_filter]

    spacer(8)

    # ── History table + Export panel ─────────────────────────────
    col_tbl, col_dl = st.columns([3, 1])

    with col_tbl:
        section_title(f"Prediction History  ({len(df)} records)")
        st.dataframe(df, width='stretch', hide_index=True, height=320)

    with col_dl:
        section_title("Export")
        ts_str = datetime.now().strftime("%Y%m%d_%H%M")

        st.markdown(
            f'<div style="background:{_WHITE};border:1px solid {_BORDER};'
            f'border-radius:10px;padding:18px 18px">',
            unsafe_allow_html=True,
        )

        # CSV — filtered view
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download CSV (filtered)",
            csv_bytes, f"predictions_{ts_str}.csv", "text/csv",
            width='stretch', key="dl_csv",
        )
        spacer(6)

        # CSV — all DB predictions
        if db_available and db_preds:
            all_df = pd.DataFrame([_db_pred_to_row(p) for p in db_preds])
            st.download_button(
                "📦 Batch Export — All Predictions",
                all_df.to_csv(index=False).encode("utf-8"),
                f"all_predictions_{ts_str}.csv", "text/csv",
                width='stretch', key="dl_batch",
            )
            spacer(6)

        # TXT report (latest prediction)
        txt_report = _build_txt_report(pred, info)
        st.download_button(
            "📄 Download Report (TXT)",
            txt_report.encode("utf-8"),
            f"report_{ts_str}.txt", "text/plain",
            width='stretch', key="dl_txt",
        )
        spacer(6)

        # PDF report (latest prediction)
        if generate_pdf_report is not None and has_permission("export_reports"):
            machine_id = st.session_state.get("last_operator_input", {}).get("machine_id", "CNC-00")
            pdf_bytes  = generate_pdf_report(pred, user, machine_id)
            ext        = "pdf" if pdf_bytes[:4] == b"%PDF" else "txt"
            st.download_button(
                "📋 Download PDF Report",
                pdf_bytes,
                f"report_{ts_str}.{ext}",
                "application/pdf" if ext == "pdf" else "text/plain",
                width='stretch', key="dl_pdf",
            )

        # Full test-set CSV
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "tool-wear-ai", "outputs", "predictions", "predictions_enhanced.csv",
        )
        if os.path.exists(csv_path):
            spacer(6)
            df_hist = pd.read_csv(csv_path)
            st.download_button(
                "📊 Full Test-Set CSV",
                df_hist.to_csv(index=False).encode("utf-8"),
                "predictions_enhanced.csv", "text/csv",
                width='stretch', key="dl_hist",
            )

        st.markdown("</div>", unsafe_allow_html=True)

    spacer(20)

    # ── Analytics Charts ──────────────────────────────────────────
    if len(df) >= 2:
        section_title("Analytics — Trend & Distribution")
        ch1, ch2 = st.columns(2)

        with ch1:
            st.markdown(
                '<div style="background:var(--bg-card);border:1px solid var(--border);'
                'border-radius:10px;padding:14px 16px;margin-bottom:14px">'
                '<div style="font-size:12px;font-weight:700;color:var(--text-secondary);'
                'text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">'
                'Failure Risk Trend</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(_chart_risk_trend(df), width='stretch', config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with ch2:
            st.markdown(
                '<div style="background:var(--bg-card);border:1px solid var(--border);'
                'border-radius:10px;padding:14px 16px;margin-bottom:14px">'
                '<div style="font-size:12px;font-weight:700;color:var(--text-secondary);'
                'text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">'
                'Tool & Machine Health Trend</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(_chart_health_trend(df), width='stretch', config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        ch3, ch4 = st.columns(2)

        with ch3:
            st.markdown(
                '<div style="background:var(--bg-card);border:1px solid var(--border);'
                'border-radius:10px;padding:14px 16px">'
                '<div style="font-size:12px;font-weight:700;color:var(--text-secondary);'
                'text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">'
                'Machine Status Distribution</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(_chart_status_dist(df), width='stretch', config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with ch4:
            st.markdown(
                '<div style="background:var(--bg-card);border:1px solid var(--border);'
                'border-radius:10px;padding:14px 16px">'
                '<div style="font-size:12px;font-weight:700;color:var(--text-secondary);'
                'text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">'
                'Failure Type Breakdown</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(_chart_failure_bar(df), width='stretch', config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        spacer(20)
    else:
        st.info("Run at least 2 predictions to see analytics charts.")
        spacer(16)

    # ── Scheduled Report Generator ────────────────────────────────
    section_title("Scheduled Report Generator")
    st.markdown(
        f'<div style="background:{_WHITE};border:1px solid {_BORDER};'
        f'border-radius:12px;padding:22px 24px">',
        unsafe_allow_html=True,
    )

    sg1, sg2, sg3 = st.columns([2, 1, 1])
    with sg1:
        period_choice = st.selectbox(
            "Report Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"],
            key="rpt_period",
        )
    with sg2:
        report_fmt = st.selectbox("Format", ["PDF", "TXT"], key="rpt_fmt")
    with sg3:
        spacer(22)
        gen_btn = st.button("Generate Summary Report", type="primary",
                            width='stretch', key="rpt_gen_btn")

    if gen_btn:
        # Filter DB predictions by chosen period
        if db_available and db_preds:
            now_dt = datetime.utcnow()
            delta_map = {
                "Last 7 Days":  7,
                "Last 30 Days": 30,
                "Last 90 Days": 90,
                "All Time":     36500,
            }
            delta_days = delta_map.get(period_choice, 30)
            cutoff = now_dt - timedelta(days=delta_days)

            period_preds = [
                p for p in db_preds
                if str(p.get("created_at", "")) >= cutoff.isoformat()[:10]
            ] or db_preds  # fallback: all

            if generate_summary_report is not None:
                with st.spinner("Generating summary report…"):
                    summary_bytes = generate_summary_report(period_preds, user, period_choice)
                ext = "pdf" if summary_bytes[:4] == b"%PDF" else "txt"
                mime = "application/pdf" if ext == "pdf" else "text/plain"
                ts_str = datetime.now().strftime("%Y%m%d_%H%M")
                st.download_button(
                    f"⬇️ Download {period_choice} Summary ({ext.upper()})",
                    summary_bytes,
                    f"summary_{period_choice.replace(' ', '_')}_{ts_str}.{ext}",
                    mime,
                    width='stretch',
                    key="dl_summary",
                )
                st.success(f"✅ Summary report generated — {len(period_preds)} predictions included.")
            else:
                st.error("PDF generator not available.")
        else:
            st.warning("No DB predictions found. Run predictions first to enable scheduled reports.")

    st.markdown("</div>", unsafe_allow_html=True)

    spacer(20)

    # ── Full dataset preview ──────────────────────────────────────
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ai4i2020.csv")
    if os.path.exists(csv_path):
        section_title("Full Dataset Preview")
        st.dataframe(
            pd.read_csv(csv_path).head(50),
            width='stretch', hide_index=True, height=280,
        )
        spacer(16)

    # ── Model info panel ──────────────────────────────────────────
    section_title("Model Information")
    model_items = [
        ("Model Name",    info.get("model_name", "Gradient Boosting")),
        ("Feature Count", str(info.get("feature_count", "56"))),
        ("VB R² Score",   str(info.get("vb_r2", "—"))),
        ("VB MAE",        f"{info.get('vb_mae_mm', '—')} mm"),
        ("RUL R² Score",  str(info.get("rul_r2", "—"))),
        ("RUL MAE",       f"{info.get('rul_mae_min', '—')} min"),
        ("Wear Limit",    f"{info.get('wear_limit_mm', 0.3)} mm"),
        ("Dataset",       "NASA Milling + AI4I 2020"),
    ]
    rows_html = "".join(
        f'<div><div style="font-size:11px;font-weight:600;color:{_GRAY};text-transform:uppercase;'
        f'letter-spacing:0.05em;margin-bottom:3px">{lbl}</div>'
        f'<div style="font-size:15px;font-weight:700;color:{_SLATE}">{val}</div></div>'
        for lbl, val in model_items
    )
    st.markdown(
        f'<div style="background:{_WHITE};border:1px solid {_BORDER};border-radius:12px;'
        f'padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px">'
        f'{rows_html}</div></div>',
        unsafe_allow_html=True,
    )
