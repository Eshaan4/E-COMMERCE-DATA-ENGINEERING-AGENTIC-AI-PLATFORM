"""
agent_dashboard.py – Agentic AI Data Intelligence Platform
Main Streamlit application: Overview | AI Analyst | Pipeline Monitor | Data Quality | ML Insights
Run with:  streamlit run agent_dashboard.py
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# ── Path setup ──────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── Agentic AI imports ──────────────────────────────────────────
from agentic_ai.config import (
    APP_TITLE, APP_SUBTITLE,
    check_database_connection, check_gemini_connection,
    get_gold_schema_context,
)
from agentic_ai.tools import (
    COLORS, PLOTLY_LAYOUT, create_chart, format_number, execute_safe_sql,
)
from agentic_ai.router_agent import route_question, AGENT_INFO
from agentic_ai.data_agent import run_data_agent
from agentic_ai.pipeline_agent import run_pipeline_agent, get_pipeline_status
from agentic_ai.ml_agent import run_ml_agent, run_full_analysis
from agentic_ai.insight_agent import run_insight_agent
from agentic_ai.action_agent import run_action_agent
from agentic_ai.report_agent import run_report_agent
from agentic_ai.forecast_agent import run_forecast_agent
from agentic_ai.prompts import GENERAL_AGENT_PROMPT

from src.utils.db_utils import get_engine, read_sql

# ── Page Config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Data Intelligence Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Professional CSS ────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp { font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
        border-right: 1px solid rgba(99,102,241,0.2) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label {
        color: #CBD5E1 !important;
    }

    /* KPI Card */
    .kpi-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99,102,241,0.4);
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 4px 0;
    }
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-delta {
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 4px;
    }
    .delta-up { color: #10B981; }
    .delta-down { color: #EF4444; }

    /* Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .status-connected {
        background: rgba(16,185,129,0.1);
        color: #10B981;
        border: 1px solid rgba(16,185,129,0.2);
    }
    .status-disconnected {
        background: rgba(239,68,68,0.1);
        color: #EF4444;
        border: 1px solid rgba(239,68,68,0.2);
    }
    .status-warning {
        background: rgba(245,158,11,0.1);
        color: #F59E0B;
        border: 1px solid rgba(245,158,11,0.2);
    }

    /* Section Card */
    .section-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid rgba(99,102,241,0.12);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #F8FAFC;
        margin-bottom: 16px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        padding-bottom: 8px;
    }

    /* Activity Panel */
    .activity-step {
        font-size: 0.82rem;
        color: #CBD5E1;
        padding: 6px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .activity-check { color: #10B981; font-weight: bold; }
    .activity-fail { color: #EF4444; font-weight: bold; }

    /* Insight Card */
    .insight-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.08));
        border-left: 3px solid #6366F1;
        border-radius: 0 8px 8px 0;
        padding: 16px;
        margin: 8px 0;
    }
    .action-card {
        background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(20,184,166,0.08));
        border-left: 3px solid #10B981;
        border-radius: 0 8px 8px 0;
        padding: 16px;
        margin: 8px 0;
    }

    /* Agent badge */
    .agent-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(99,102,241,0.12);
        color: #A5B4FC;
        border: 1px solid rgba(99,102,241,0.25);
    }

    /* Quality badge */
    .quality-good     { background: rgba(16,185,129,0.12); color: #10B981; border: 1px solid rgba(16,185,129,0.3); padding: 6px 14px; border-radius: 8px; font-weight: 600; }
    .quality-warning  { background: rgba(245,158,11,0.12); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); padding: 6px 14px; border-radius: 8px; font-weight: 600; }
    .quality-critical { background: rgba(239,68,68,0.12); color: #EF4444; border: 1px solid rgba(239,68,68,0.3); padding: 6px 14px; border-radius: 8px; font-weight: 600; }

    /* Agent Card styling in Sidebar */
    .agent-card {
        padding: 12px 14px;
        border-radius: 8px;
        margin-bottom: 8px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    .agent-card:hover {
        background: rgba(99, 102, 241, 0.05);
        border-color: rgba(99, 102, 241, 0.2);
    }
    .agent-card-active {
        background: rgba(99, 102, 241, 0.12) !important;
        border: 1px solid rgba(99, 102, 241, 0.5) !important;
    }
    .agent-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #F8FAFC;
        margin-bottom: 2px;
    }
    .agent-desc {
        font-size: 0.72rem;
        color: #94A3B8;
        line-height: 1.25;
        margin-bottom: 4px;
    }
    .agent-status {
        font-size: 0.68rem;
        font-weight: 500;
    }
    .status-dot-active { color: #10B981; }
    .status-dot-available { color: #10B981; }
    .status-dot-processing { color: #F59E0B; }
    .status-dot-error { color: #EF4444; }
    .status-dot-notconfig { color: #64748B; }

    /* Quick Question Button */
    .quick-question-btn {
        display: block;
        width: 100%;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #CBD5E1;
        padding: 6px 10px;
        margin-bottom: 5px;
        border-radius: 6px;
        font-size: 0.75rem;
        text-align: left;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .quick-question-btn:hover {
        background: rgba(99, 102, 241, 0.08);
        border-color: rgba(99, 102, 241, 0.25);
        color: #F8FAFC;
    }

    /* Hide default Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Responsive adjustments */
    .block-container { padding-top: 1rem; max-width: 1400px; }
</style>
""", unsafe_allow_html=True)


# ── Cached DB Engine ────────────────────────────────────────────
@st.cache_resource
def get_db_engine():
    """Cached database engine (singleton)."""
    try:
        return get_engine()
    except Exception:
        return None


# ── Helper Functions ────────────────────────────────────────────
def render_kpi_card(label: str, value: str, delta: str = "", delta_direction: str = ""):
    """Render a styled KPI card."""
    delta_html = ""
    if delta:
        css_class = "delta-up" if delta_direction == "up" else "delta-down"
        arrow = "▲" if delta_direction == "up" else "▼"
        delta_html = f'<div class="kpi-delta {css_class}">{arrow} {delta}</div>'
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


def render_status_badge(label: str, connected: bool, warning: bool = False):
    """Render a status badge."""
    if warning:
        css = "status-warning"
        dot = "🟡"
        text = "Warning"
    elif connected:
        css = "status-connected"
        dot = "🟢"
        text = "Connected"
    else:
        css = "status-disconnected"
        dot = "🔴"
        text = "Disconnected"
    return f'<span class="status-badge {css}">{dot} {label}: {text}</span>'


def render_activity_panel(steps: list):
    """Render the agent activity panel."""
    html = '<div style="padding: 8px 0;">'
    for step_text, success in steps:
        icon_class = "activity-check" if success else "activity-fail"
        icon = "✓" if success else "✗"
        html += f'<div class="activity-step"><span class="{icon_class}">{icon}</span> {step_text}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Header ──────────────────────────────────────────────────────
def render_header():
    """Render the main application header with status indicators."""
    engine = get_db_engine()
    db_ok = check_database_connection(engine) if engine else False
    gemini_ok = check_gemini_connection()

    # Pipeline health from metadata
    pipeline_ok = False
    if db_ok:
        try:
            r = read_sql("""
                SELECT status FROM metadata.pipeline_runs 
                ORDER BY start_time DESC LIMIT 1
            """, engine)
            if not r.empty:
                pipeline_ok = r["status"].iloc[0] in ("SUCCESS", "PARTIAL", "RUNNING")
            else:
                pipeline_ok = True
        except Exception:
            pipeline_ok = True

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(f"### {APP_TITLE}")
        st.caption(APP_SUBTITLE)
    with col2:
        badges = " &nbsp; ".join([
            render_status_badge("Gemini", gemini_ok),
            render_status_badge("Database", db_ok),
            render_status_badge("Pipeline", pipeline_ok, warning=not pipeline_ok and db_ok),
        ])
        st.markdown(f'<div style="text-align:right; padding-top:12px;">{badges}</div>',
                     unsafe_allow_html=True)

    # ── Active Agent Indicator ──────────────────────────────────
    active_agent = st.session_state.get("selected_agent", "router")
    agent_names = {
        "router": "🤖 AUTO ROUTER",
        "data": "📊 DATA AGENT",
        "pipeline": "⚙️ PIPELINE AGENT",
        "ml": "🧠 ML AGENT",
        "forecast": "🔮 FORECAST AGENT",
        "insight": "💡 INSIGHT AGENT",
        "action": "🎯 ACTION AGENT",
        "report": "📋 REPORT AGENT",
        "general": "💬 GENERAL AGENT",
    }
    disp_name = agent_names.get(active_agent, "🤖 AUTO ROUTER")
    
    st.markdown(f"""
        <div style="background:rgba(99,102,241,0.08); border-left:4px solid #6366F1; padding:10px 16px; margin: 10px 0; border-radius: 0 6px 6px 0;">
            <span style="font-size:0.75rem; font-weight:600; color:#94A3B8; text-transform:uppercase; letter-spacing:1px; display:block; margin-bottom:2px;">Active Agent Mode</span>
            <span style="font-size:1.1rem; font-weight:700; color:#F8FAFC;"><span style="color:#10B981; margin-right:6px;">●</span>{disp_name}</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")


# ── Page 1: Overview ────────────────────────────────────────────
def page_overview():
    """Business Intelligence Dashboard with real data from Gold layer."""
    engine = get_db_engine()
    if not engine:
        st.error("Database connection unavailable. Please check PostgreSQL configuration.")
        return

    # ── BI Filters ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("#### Filters")

        # Get available categories
        try:
            cats = read_sql("SELECT DISTINCT product_category_english FROM gold.dim_product WHERE product_category_english IS NOT NULL", engine)
            cat_list = ["All"] + sorted(cats["product_category_english"].tolist())
        except Exception:
            cat_list = ["All"]

        # Get available regions
        try:
            regions = read_sql("SELECT DISTINCT region FROM gold.dim_customer WHERE region IS NOT NULL", engine)
            reg_list = ["All"] + sorted(regions["region"].tolist())
        except Exception:
            reg_list = ["All"]

        # Render filter selects
        sel_cat = st.selectbox("Category", cat_list)
        sel_reg = st.selectbox("Region", reg_list)

        # Date range defaults
        try:
            dates = read_sql("SELECT MIN(full_date) as start_d, MAX(full_date) as end_d FROM gold.dim_date", engine)
            min_date = dates["start_d"].iloc[0] or datetime(2017,1,1).date()
            max_date = dates["end_d"].iloc[0] or datetime(2025,12,31).date()
        except Exception:
            min_date = datetime(2017,1,1).date()
            max_date = datetime(2025,12,31).date()

        date_sel = st.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    # Save filters in session_state for access in chat context
    st.session_state["bi_filters"] = {
        "category": sel_cat,
        "region": sel_reg,
        "date_range": date_sel
    }

    # Build SQL clauses based on filters
    where_clauses = []
    if sel_cat != "All":
        where_clauses.append(f"p.product_category_english = '{sel_cat}'")
    if sel_reg != "All":
        where_clauses.append(f"c.region = '{sel_reg}'")
    if isinstance(date_sel, tuple) and len(date_sel) == 2:
        where_clauses.append(f"d.full_date BETWEEN '{date_sel[0]}' AND '{date_sel[1]}'")

    where_sql = " AND ".join(where_clauses)
    where_prefix = f"WHERE {where_sql}" if where_sql else ""

    # ── Fetch KPI metrics from gold.fact_sales
    try:
        kpis_df = read_sql(f"""
            SELECT 
                COALESCE(SUM(f.total_item_value), 0) AS total_revenue,
                COUNT(DISTINCT f.order_id) AS total_orders,
                COALESCE(AVG(f.total_item_value), 0) AS aov,
                COUNT(DISTINCT f.customer_key) AS total_customers,
                COUNT(DISTINCT f.product_key) AS total_products
            FROM gold.fact_sales f
            LEFT JOIN gold.dim_product p ON f.product_key = p.product_key
            LEFT JOIN gold.dim_customer c ON f.customer_key = c.customer_key
            LEFT JOIN gold.dim_date d ON f.order_date_key = d.date_key
            {where_prefix}
        """, engine)

        # Growth MoM
        growth_pct = 0.0
        growth_direction = "up"
        try:
            gr_df = read_sql("SELECT kpi_value FROM gold.kpi_summary WHERE kpi_name = 'latest_mom_revenue_growth_pct' ORDER BY computed_at DESC LIMIT 1", engine)
            if not gr_df.empty:
                growth_pct = float(gr_df["kpi_value"].iloc[0])
                growth_direction = "up" if growth_pct >= 0 else "down"
        except Exception:
            pass

        total_rev = kpis_df["total_revenue"].iloc[0]
        total_ord = kpis_df["total_orders"].iloc[0]
        total_cust = kpis_df["total_customers"].iloc[0]
        total_prod = kpis_df["total_products"].iloc[0]
        avg_order = kpis_df["aov"].iloc[0]

        # ── KPI Cards Row
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            render_kpi_card("Total Revenue", format_number(total_rev))
        with c2:
            render_kpi_card("Total Orders", format_number(total_ord))
        with c3:
            render_kpi_card("Total Customers", format_number(total_cust))
        with c4:
            render_kpi_card("Total Products", format_number(total_prod))
        with c5:
            render_kpi_card("Avg Order Value", f"R${avg_order:,.2f}")
        with c6:
            render_kpi_card("Revenue Growth", f"{growth_pct:+.1f}%", f"{abs(growth_pct):.1f}% MoM", growth_direction)

    except Exception as e:
        st.error(f"Failed to load KPIs: {e}")
        return

    st.markdown("---")

    # ── Charts Row 1
    col1, col2 = st.columns(2)
    with col1:
        try:
            # Revenue trend (Monthly)
            rev_trend = read_sql(f"""
                SELECT d.month_name, d.year, d.month, SUM(f.total_item_value) AS revenue
                FROM gold.fact_sales f
                LEFT JOIN gold.dim_product p ON f.product_key = p.product_key
                LEFT JOIN gold.dim_customer c ON f.customer_key = c.customer_key
                LEFT JOIN gold.dim_date d ON f.order_date_key = d.date_key
                {where_prefix}
                GROUP BY d.year, d.month, d.month_name
                ORDER BY d.year, d.month
            """, engine)

            if not rev_trend.empty:
                rev_trend["period"] = rev_trend["month_name"].str.strip() + " " + rev_trend["year"].astype(str)
                fig = px.line(rev_trend, x="period", y="revenue", 
                              title="Revenue Trend", 
                              color_discrete_sequence=[COLORS["primary"]])
                fig.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sales trend data available.")
        except Exception as e:
            st.error(f"Revenue chart error: {e}")

    with col2:
        try:
            # Top categories
            cat_rev = read_sql(f"""
                SELECT p.product_category_english AS category, SUM(f.total_item_value) AS revenue
                FROM gold.fact_sales f
                LEFT JOIN gold.dim_product p ON f.product_key = p.product_key
                LEFT JOIN gold.dim_customer c ON f.customer_key = c.customer_key
                LEFT JOIN gold.dim_date d ON f.order_date_key = d.date_key
                {where_prefix}
                GROUP BY p.product_category_english
                ORDER BY revenue DESC LIMIT 10
            """, engine)

            if not cat_rev.empty:
                fig = px.bar(cat_rev, x="revenue", y="category", orientation="h",
                             title="Top 10 Categories by Revenue",
                             color_discrete_sequence=[COLORS["primary"]])
                fig.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category sales data available.")
        except Exception as e:
            st.error(f"Category chart error: {e}")

    # ── Charts Row 2
    col3, col4 = st.columns(2)

    with col3:
        try:
            region_data = read_sql(f"""
                SELECT c.region, SUM(f.total_item_value) AS revenue,
                       COUNT(DISTINCT f.order_id) AS orders
                FROM gold.fact_sales f
                LEFT JOIN gold.dim_customer c ON f.customer_key = c.customer_key
                LEFT JOIN gold.dim_product p ON f.product_key = p.product_key
                LEFT JOIN gold.dim_date d ON f.order_date_key = d.date_key
                {where_prefix}
                {"AND" if where_sql else "WHERE"} c.region IS NOT NULL
                GROUP BY c.region
                ORDER BY revenue DESC
            """, engine)

            if not region_data.empty:
                fig = px.bar(region_data, x="region", y="revenue",
                             title="Revenue by Region",
                             color_discrete_sequence=[COLORS["primary"]])
                fig.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No regional distribution data available.")
        except Exception as e:
            st.error(f"Region chart error: {e}")

    with col4:
        try:
            status_data = read_sql(f"""
                SELECT f.order_status, COUNT(DISTINCT f.order_id) AS count
                FROM gold.fact_sales f
                LEFT JOIN gold.dim_product p ON f.product_key = p.product_key
                LEFT JOIN gold.dim_customer c ON f.customer_key = c.customer_key
                LEFT JOIN gold.dim_date d ON f.order_date_key = d.date_key
                {where_prefix}
                {"AND" if where_sql else "WHERE"} f.order_status IS NOT NULL
                GROUP BY f.order_status
            """, engine)

            if not status_data.empty:
                fig = px.pie(status_data, names="order_status", values="count",
                             title="Order Status Distribution",
                             hole=0.4,
                             color_discrete_sequence=[COLORS["primary"], COLORS["secondary"], COLORS["success"]])
                fig.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No order status data available.")
        except Exception as e:
            st.error(f"Status chart error: {e}")

    # ── Business Highlights
    st.markdown("")
    st.markdown('<div class="section-title">Business Highlights</div>', unsafe_allow_html=True)
    try:
        highlights = []

        # Top category
        if 'cat_rev' in dir() and not cat_rev.empty:
            top_cat = cat_rev.iloc[0]
            highlights.append(f"**Highest-performing category**: {top_cat['category']} "
                              f"(R${float(top_cat['revenue']):,.2f})")

        # Top region
        if 'region_data' in dir() and not region_data.empty:
            top_reg = region_data.iloc[0]
            highlights.append(f"**Top region**: {top_reg['region']} with "
                              f"R${float(top_reg['revenue']):,.2f} revenue")

        # Growth
        if growth_pct > 0:
            highlights.append(f"**Revenue growth**: +{growth_pct:.1f}% month-over-month")
        elif growth_pct < 0:
            highlights.append(f"**Revenue trend**: {growth_pct:.1f}% month-over-month decline")

        # Orders
        highlights.append(f"**Total orders**: {total_ord:,} across {total_cust:,} customers")

        if highlights:
            for h in highlights:
                st.markdown(f"- {h}")
        else:
            st.info("No highlights available with current filters.")
    except Exception:
        pass


# ── Page 2: AI Analyst ──────────────────────────────────────────
def page_ai_analyst():
    """Agentic AI chat interface with multi-agent routing and specialist agents."""
    engine = get_db_engine()

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ── Clear Chat Button ──
    col_clear1, col_clear2 = st.columns([6, 1])
    with col_clear2:
        if st.button("🗑️ Clear Chat", key="clear_chat_btn"):
            st.session_state.chat_history = []
            st.rerun()

    # Build filter context from BI filters
    filters_context = ""
    bi_filters = st.session_state.get("bi_filters", {})
    if bi_filters:
        parts = []
        if bi_filters.get("category") and bi_filters["category"] != "All":
            parts.append(f"Category filter: {bi_filters['category']}")
        if bi_filters.get("region") and bi_filters["region"] != "All":
            parts.append(f"Region filter: {bi_filters['region']}")
        if bi_filters.get("date_range"):
            dr = bi_filters["date_range"]
            if isinstance(dr, tuple) and len(dr) == 2:
                parts.append(f"Date range: {dr[0]} to {dr[1]}")
        if parts:
            filters_context = "\n".join(parts)

    # Show active filters
    if filters_context:
        st.markdown(f"""
            <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2);
                        border-radius:8px; padding:8px 14px; font-size:0.8rem; color:#A5B4FC; margin-bottom:12px;">
                Active Filters: {filters_context.replace(chr(10), ' | ')}
            </div>
        """, unsafe_allow_html=True)

    # ── Suggested Questions (only when no chat history) ──
    if not st.session_state.chat_history:
        st.markdown("""
            <div style="text-align:center; padding:20px 0 10px 0;">
                <div style="font-size:1.4rem; font-weight:700; color:#F8FAFC; margin-bottom:4px;">
                    🧠 AI Data Analyst
                </div>
                <div style="font-size:0.85rem; color:#94A3B8; margin-bottom:16px;">
                    Ask questions about your data, sales, profit and forecast.
                </div>
            </div>
        """, unsafe_allow_html=True)

        suggested = [
            ("📊", "What are total sales?"),
            ("🏆", "Top 10 products by revenue?"),
            ("🌍", "Which region is most profitable?"),
            ("📉", "Why did profit decrease?"),
            ("🔮", "What is the sales forecast?"),
            ("🎯", "What should we focus on?"),
            ("📋", "Summarize the dashboard."),
            ("📈", "Show monthly sales trend."),
        ]

        # Render as 4-column grid
        cols = st.columns(4)
        for i, (icon, q) in enumerate(suggested):
            with cols[i % 4]:
                if st.button(f"{icon} {q}", key=f"suggest_{i}", use_container_width=True):
                    st.session_state["quick_question_trigger"] = q
                    st.rerun()

        st.markdown("---")

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Render stored results
            if msg.get("agent_results"):
                for ar in msg["agent_results"]:
                    _render_agent_result(ar["result"], ar["agent"])

    # Chat input
    user_input = st.chat_input("Ask a question about your data...")

    # Handle quick question triggers
    if "quick_question_trigger" in st.session_state:
        user_input = st.session_state.pop("quick_question_trigger")

    if user_input:
        # Guard empty input
        user_input = user_input.strip()
        if not user_input:
            return

        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Process with multi-agent orchestration
        with st.chat_message("assistant"):
            with st.spinner("Analyzing question..."):
                # Step 1: Route to agents
                routing = route_question(user_input)
                agent_list = routing.get("agents", ["general"])

                steps = [("Request received", True)]

                # Show agent pipeline
                agent_badges = " → ".join([
                    f"{AGENT_INFO.get(a, {}).get('icon', '🤖')} {AGENT_INFO.get(a, {}).get('name', a)}"
                    for a in agent_list
                ])
                st.markdown(f"""
                    <div style="background:rgba(99,102,241,0.08); border-left:4px solid #6366F1;
                                padding:10px 16px; margin-bottom:12px; border-radius:0 8px 8px 0;">
                        <span style="font-size:0.72rem; font-weight:600; color:#94A3B8; text-transform:uppercase;
                                     letter-spacing:1px; display:block; margin-bottom:4px;">Agent Pipeline</span>
                        <span style="font-size:0.9rem; font-weight:600; color:#F8FAFC;">{agent_badges}</span>
                    </div>
                """, unsafe_allow_html=True)

                steps.append((f"Router selected: {', '.join(agent_list)}", True))

                # Step 2: Execute agents in sequence, passing context forward
                all_results = []
                data_context = ""  # context passed from data agent to insight/action
                insight_context = ""  # context passed from insight agent to action

                for agent_key in agent_list:
                    agent_info = AGENT_INFO.get(agent_key, {})
                    agent_name = agent_info.get("name", agent_key)

                    # Show status for each agent
                    status_placeholder = st.empty()
                    status_placeholder.markdown(f"""
                        <div style="font-size:0.8rem; color:#A5B4FC; padding:4px 0;">
                            ⏳ {agent_info.get('icon', '🤖')} <b>{agent_name}</b> processing...
                        </div>
                    """, unsafe_allow_html=True)

                    agent_result = {}

                    try:
                        if agent_key == "data":
                            agent_result = run_data_agent(
                                user_input, engine, filters_context,
                                st.session_state.chat_history
                            )
                            # Build data context for downstream agents
                            df = agent_result.get("dataframe")
                            if df is not None and not df.empty:
                                data_context = (
                                    f"SQL Query: {agent_result.get('sql', '')}\n"
                                    f"Results ({len(df)} rows):\n{df.head(10).to_string()}"
                                )
                            if agent_result.get("explanation"):
                                data_context += f"\nExplanation: {agent_result['explanation']}"

                        elif agent_key == "pipeline":
                            agent_result = run_pipeline_agent(user_input, engine)

                        elif agent_key == "ml":
                            agent_result = run_ml_agent(user_input, engine)
                            df = agent_result.get("dataframe")
                            if df is not None and not df.empty:
                                data_context = f"ML Analysis Results:\n{df.head(10).to_string()}"

                        elif agent_key == "forecast":
                            agent_result = run_forecast_agent(user_input, engine)

                        elif agent_key == "insight":
                            ctx = data_context or f"User question: {user_input}"
                            agent_result = run_insight_agent(user_input, ctx, engine)
                            insight_context = agent_result.get("insight", "")

                        elif agent_key == "action":
                            ctx = insight_context or data_context or f"User question: {user_input}"
                            agent_result = run_action_agent(user_input, ctx, engine)

                        elif agent_key == "report":
                            agent_result = run_report_agent(user_input, engine)

                        else:  # general
                            from google import genai as genai_client
                            try:
                                client = genai_client.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
                                interaction = client.interactions.create(
                                    model="gemini-3.6-flash",
                                    input=f"{GENERAL_AGENT_PROMPT}\n\n{user_input}",
                                )
                                agent_result = {
                                    "answer": interaction.output_text,
                                    "steps": [("Response generated", True)],
                                }
                            except Exception as e:
                                agent_result = {
                                    "answer": "I can help you explore business data, pipeline health, and ML insights. Try asking a specific question.",
                                    "error": str(e),
                                }

                        steps.extend(agent_result.get("steps", []))

                    except Exception as e:
                        agent_result = {"error": f"{agent_name} failed: {str(e)}"}
                        steps.append((f"{agent_name} error", False))

                    # Clear status and render result
                    status_placeholder.empty()
                    all_results.append({"agent": agent_key, "result": agent_result})

                    # Render this agent's results
                    _render_agent_result(agent_result, agent_key)

                # Activity panel
                with st.expander("Agent Activity", expanded=False):
                    render_activity_panel(steps)

                # Build assistant message content for history
                content_parts = []
                for ar in all_results:
                    r = ar["result"]
                    if r.get("error") and not r.get("answer") and not r.get("insight"):
                        content_parts.append(r["error"])
                    elif ar["agent"] == "data":
                        if r.get("explanation"):
                            content_parts.append(r["explanation"])
                    elif ar["agent"] in ("pipeline", "ml", "forecast", "report", "general"):
                        if r.get("answer"):
                            content_parts.append(r["answer"])
                    elif ar["agent"] == "insight":
                        if r.get("insight"):
                            content_parts.append(f"**Insight:** {r['insight']}")
                    elif ar["agent"] == "action":
                        if r.get("action"):
                            content_parts.append(f"**Recommended Action:** {r['action']}")

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "\n\n".join(content_parts) or "Analysis complete.",
                    "agent_results": all_results,
                })


def _render_agent_result(result: dict, category: str):
    """Render agent results in the chat."""
    if not result:
        return

    if result.get("error") and not result.get("answer") and not result.get("insight") and not result.get("action"):
        st.error(result["error"])
        return

    if category == "data":
        # Explanation text
        if result.get("explanation"):
            st.markdown(result["explanation"])

        df = result.get("dataframe")
        if df is not None and not df.empty:
            st.markdown(f"**Query Result** — {len(df)} rows, {len(df.columns)} columns")

            # Show chart
            viz = result.get("visualization", "table")
            x_col = result.get("x_column", "")
            y_col = result.get("y_column", "")
            title = result.get("title", "")

            if viz != "table":
                try:
                    fig = create_chart(df, viz, x_col, y_col, title)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    pass

            # Expandable data table
            with st.expander("View Data Table", expanded=False):
                st.dataframe(df, use_container_width=True, height=300)

            # Expandable SQL
            if result.get("sql"):
                with st.expander("View Generated SQL", expanded=False):
                    st.code(result["sql"], language="sql")

        # Insight card
        if result.get("insight"):
            st.markdown(f"""
                <div class="insight-card">
                    <strong>📊 Insight</strong><br>{result['insight']}
                </div>
            """, unsafe_allow_html=True)

        # Action card
        if result.get("action"):
            st.markdown(f"""
                <div class="action-card">
                    <strong>🎯 Suggested Action</strong><br>{result['action']}
                </div>
            """, unsafe_allow_html=True)

        # Source
        st.markdown('<div style="font-size:0.7rem; color:#64748B; margin-top:8px;">Source: Database (Gold Layer)</div>',
                    unsafe_allow_html=True)

    elif category == "pipeline":
        if result.get("answer"):
            st.markdown(result["answer"])
        if result.get("insight"):
            st.markdown(f"""
                <div class="insight-card">
                    <strong>⚙️ Pipeline Insight</strong><br>{result['insight']}
                </div>
            """, unsafe_allow_html=True)
        if result.get("action"):
            st.markdown(f"""
                <div class="action-card">
                    <strong>🎯 Suggested Action</strong><br>{result['action']}
                </div>
            """, unsafe_allow_html=True)
            
        # SQL Expandable
        if result.get("sql"):
            with st.expander("View Generated SQL", expanded=False):
                st.code(result["sql"], language="sql")
        
        # Raw records
        df = result.get("dataframe")
        if df is not None and not df.empty:
            with st.expander("View Metadata Details", expanded=False):
                st.dataframe(df, use_container_width=True)

        st.markdown('<div style="font-size:0.7rem; color:#64748B; margin-top:8px;">Source: Metadata Schema</div>',
                    unsafe_allow_html=True)

    elif category == "ml":
        if result.get("answer"):
            st.markdown(result["answer"])
        
        # Plotly anomaly or regression chart
        df = result.get("dataframe")
        if df is not None and not df.empty and "trend_line" in df.columns:
            try:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.iloc[:,0], y=df.iloc[:,1], name="Actual Value", mode="lines+markers"))
                fig.add_trace(go.Scatter(x=df.iloc[:,0], y=df["trend_line"], name="Linear Trend Line", line=dict(dash="dash")))
                
                # Check for anomalies
                if "is_anomaly" in df.columns:
                    anom = df[df["is_anomaly"]]
                    if not anom.empty:
                        fig.add_trace(go.Scatter(x=anom.iloc[:,0], y=anom.iloc[:,1], name="Anomaly", mode="markers", marker=dict(size=10, color=COLORS["danger"])))
                
                fig.update_layout(**PLOTLY_LAYOUT, title="ML Statistical Analysis")
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

        # Expandable analysis details
        if df is not None and not df.empty:
            with st.expander("View Statistical Details", expanded=False):
                st.dataframe(df, use_container_width=True)

        if result.get("action"):
            st.markdown(f"""
                <div class="action-card">
                    <strong>🎯 Suggested Action</strong><br>{result['action']}
                </div>
            """, unsafe_allow_html=True)

        # SQL Expandable
        if result.get("sql"):
            with st.expander("View Generated SQL", expanded=False):
                st.code(result["sql"], language="sql")

        st.markdown('<div style="font-size:0.7rem; color:#64748B; margin-top:8px;">Source: ML Statistical Analysis</div>',
                    unsafe_allow_html=True)

    elif category == "forecast":
        if result.get("answer"):
            st.markdown(result["answer"])

        # Forecast chart: historical + predicted
        df = result.get("dataframe")
        if df is not None and not df.empty:
            try:
                fig = go.Figure()

                # Historical
                hist = df[df.get("type", "") == "Historical"] if "type" in df.columns else df
                if not hist.empty:
                    fig.add_trace(go.Scatter(
                        x=hist["period"], y=hist["revenue"],
                        name="Historical", mode="lines+markers",
                        line=dict(color=COLORS["primary"], width=2),
                        marker=dict(size=5),
                    ))

                # Forecast
                fc = df[df.get("type", "") == "Forecast"] if "type" in df.columns else pd.DataFrame()
                if not fc.empty:
                    fig.add_trace(go.Scatter(
                        x=fc["period"], y=fc["revenue"],
                        name="Forecast", mode="lines+markers",
                        line=dict(color=COLORS["warning"], width=2, dash="dash"),
                        marker=dict(size=8, symbol="diamond"),
                    ))

                # Trend line
                if "trend_line" in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df["period"], y=df["trend_line"],
                        name="Trend Line", mode="lines",
                        line=dict(color=COLORS["danger"], width=1.5, dash="dot"),
                    ))

                fig.update_layout(**PLOTLY_LAYOUT, title="Revenue Forecast",
                                  legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

        if result.get("insight"):
            st.markdown(f"""
                <div class="insight-card">
                    <strong>🔮 Forecast Insight</strong><br>{result['insight']}
                </div>
            """, unsafe_allow_html=True)

        if result.get("action"):
            st.markdown(f"""
                <div class="action-card">
                    <strong>🎯 Recommended Action</strong><br>{result['action']}
                </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.7rem; color:#64748B; margin-top:8px;">Source: Forecast Model (Linear Extrapolation)</div>',
                    unsafe_allow_html=True)

    elif category == "insight":
        if result.get("insight"):
            st.markdown(f"""
                <div class="insight-card">
                    <strong>💡 Business Insight</strong><br>{result['insight']}
                </div>
            """, unsafe_allow_html=True)

        # Evidence
        evidence = result.get("evidence", [])
        if evidence:
            with st.expander("Supporting Evidence", expanded=False):
                for ev in evidence:
                    st.markdown(f"- {ev}")

    elif category == "action":
        if result.get("action"):
            st.markdown(f"""
                <div class="action-card">
                    <strong>🎯 Recommended Action</strong><br>{result['action']}
                </div>
            """, unsafe_allow_html=True)

        if result.get("rationale"):
            st.markdown(f"""
                <div style="font-size:0.82rem; color:#94A3B8; padding:4px 0 0 16px; font-style:italic;">
                    Rationale: {result['rationale']}
                </div>
            """, unsafe_allow_html=True)

    elif category == "report":
        if result.get("answer"):
            st.markdown(result["answer"])

        if result.get("insight"):
            st.markdown(f"""
                <div class="insight-card">
                    <strong>📋 Key Finding</strong><br>{result['insight']}
                </div>
            """, unsafe_allow_html=True)

        if result.get("action"):
            st.markdown(f"""
                <div class="action-card">
                    <strong>🎯 Management Focus</strong><br>{result['action']}
                </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.7rem; color:#64748B; margin-top:8px;">Source: Dashboard Report Data</div>',
                    unsafe_allow_html=True)

    elif category == "general":
        if result.get("answer"):
            st.markdown(result["answer"])


# ── Page 3: Pipeline Monitor ────────────────────────────────────
def page_pipeline_monitor():
    """Visualizes ETL metrics, watermarks, executions, and schema evolutions."""
    engine = get_db_engine()
    if not engine:
        st.error("Database connection unavailable.")
        return

    # Fetch stats
    stats = get_pipeline_status(engine)

    # ── KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card("Pipeline Status", stats["status"])
    with col2:
        render_kpi_card("Last Execution Run", stats["last_run"])
    with col3:
        render_kpi_card("Records Processed", format_number(stats["records"]))
    with col4:
        render_kpi_card("Failed / Rejected", format_number(stats["failed"]))

    st.markdown("---")

    # ── Pipeline Flow chart
    st.markdown('<div class="section-title">Medallion Ingestion Architecture Flow</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style="background:#1E293B; border-radius:12px; padding:16px; border:1px solid rgba(255,255,255,0.06); text-align:center;">
            <div style="display:inline-flex; align-items:center; gap:16px; font-weight:600; font-size:0.95rem; color:#CBD5E1;">
                <span style="background:rgba(99,102,241,0.12); padding:10px 18px; border-radius:8px; border:1px solid rgba(99,102,241,0.3);">📥 SOURCE FILES</span>
                <span style="color:#6366F1;">➜</span>
                <span style="background:rgba(245,158,11,0.1); padding:10px 18px; border-radius:8px; border:1px solid rgba(245,158,11,0.3); color:#F59E0B;">🟫 BRONZE (RAW)</span>
                <span style="color:#6366F1;">➜</span>
                <span style="background:rgba(16,185,129,0.1); padding:10px 18px; border-radius:8px; border:1px solid rgba(16,185,129,0.3); color:#10B981;">🥈 SILVER (CLEANSED)</span>
                <span style="color:#6366F1;">➜</span>
                <span style="background:rgba(139,92,246,0.1); padding:10px 18px; border-radius:8px; border:1px solid rgba(139,92,246,0.3); color:#A78BFA;">🥇 GOLD (ANALYTICS)</span>
            </div>
            <div style="font-size:0.75rem; color:#94A3B8; margin-top:10px;">
                ● Watermarks, schemas, and expectations are automatically audited.
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Executions Table
    st.markdown('<div class="section-title">Recent Run Logs (metadata.pipeline_runs)</div>', unsafe_allow_html=True)
    try:
        runs = read_sql("""
            SELECT run_id, pipeline_name, layer, status, start_time, duration_seconds,
                   total_records_read, records_inserted, records_rejected
            FROM metadata.pipeline_runs
            ORDER BY start_time DESC
            LIMIT 10
        """, engine)
        if not runs.empty:
            st.dataframe(runs, use_container_width=True)
        else:
            st.info("No execution runs logged in database metadata.")
    except Exception as e:
        st.error(f"Failed to load run logs: {e}")


# ── Page 4: Data Quality ────────────────────────────────────────
def page_data_quality():
    """Renders data quality metrics, warnings, and null percentages."""
    engine = get_db_engine()
    if not engine:
        st.error("Database connection unavailable.")
        return

    st.markdown('<div class="section-title">Data Validation Quality Summary (metadata.dq_results)</div>', unsafe_allow_html=True)
    
    # KPIs
    try:
        dq_stats = read_sql("""
            SELECT 
                COUNT(*) AS total_checks,
                SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS passed_checks,
                SUM(CASE WHEN NOT passed THEN 1 ELSE 0 END) AS failed_checks,
                AVG(success_pct) AS avg_score
            FROM metadata.dq_results
        """, engine)

        total_checks = dq_stats["total_checks"].iloc[0] or 0
        passed = dq_stats["passed_checks"].iloc[0] or 0
        failed = dq_stats["failed_checks"].iloc[0] or 0
        score = dq_stats["avg_score"].iloc[0] or 100.0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_kpi_card("Total Checks Run", format_number(total_checks))
        with col2:
            render_kpi_card("Passed Rules", format_number(passed))
        with col3:
            render_kpi_card("Failed/Warnings", format_number(failed))
        with col4:
            render_kpi_card("Average DQ Score", f"{score:.2f}%")

    except Exception as e:
        st.error(f"Error loading DQ KPIs: {e}")
        return

    st.markdown("---")

    # Table details
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown('##### DQ Check Detailed Records')
        try:
            details = read_sql("""
                SELECT table_name, check_name, check_type, passed, total_records, failed_records, success_pct
                FROM metadata.dq_results
                ORDER BY checked_at DESC
                LIMIT 15
            """, engine)
            if not details.empty:
                st.dataframe(details, use_container_width=True)
            else:
                st.info("No data quality checks recorded. Run the pipeline ingestion first.")
        except Exception as e:
            st.error(f"DQ table load error: {e}")

    with col_right:
        st.markdown('##### DQ Failures by Table')
        try:
            fail_table = read_sql("""
                SELECT table_name, COUNT(*) AS count
                FROM metadata.dq_results
                WHERE NOT passed
                GROUP BY table_name
                ORDER BY count DESC
            """, engine)
            if not fail_table.empty:
                fig = px.bar(fail_table, x="table_name", y="count", title="Failures count", color_discrete_sequence=[COLORS["danger"]])
                fig.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("No validation failures detected across active ingestion tables.")
        except Exception as e:
            st.error(f"DQ chart load error: {e}")


# ── Page 5: ML Insights ─────────────────────────────────────────
def page_ml_insights():
    """Renders statistical trend lines, moving averages, and z-score anomalies."""
    engine = get_db_engine()
    if not engine:
        st.error("Database connection unavailable.")
        return

    from agentic_ai.ml_agent import get_revenue_time_series
    
    # Fetch historical sales time-series
    ts = get_revenue_time_series(engine)
    
    if ts.empty or len(ts) < 2:
        st.warning("Insufficient historical business data in gold.revenue_mart to calculate statistical trends. Execute the ETL pipeline run first.")
        return

    # Run ML analysis
    analysis = run_full_analysis(ts, "trend")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card("Current Trend Direction", str(analysis.get("direction", "unknown")).upper())
    with col2:
        render_kpi_card("Trend Slope (MoM)", format_number(analysis.get("slope", 0)))
    with col3:
        render_kpi_card("Anomalies Detected", format_number(analysis.get("anomalies_detected", 0)))
    with col4:
        render_kpi_card("Highest Deviation Z", f"{analysis.get('highest_deviation', 0):.2f}")

    st.markdown("---")

    # Visualizations row
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        # Line + trend
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts["period"], y=ts["revenue"],
                                  mode="lines+markers", name="Revenue",
                                  line=dict(color=COLORS["primary"], width=2),
                                  marker=dict(size=5)))
        
        if "ma_3" in ts.columns:
            fig.add_trace(go.Scatter(x=ts["period"], y=ts["ma_3"],
                                      mode="lines", name="3-Period MA",
                                      line=dict(color=COLORS["warning"], width=2, dash="dash")))
            
        if "trend_line" in ts.columns:
            fig.add_trace(go.Scatter(x=ts["period"], y=ts["trend_line"],
                                      mode="lines", name="Linear Trend",
                                      line=dict(color=COLORS["danger"], width=1.5, dash="dot")))
            
        # Mark anomalies
        anomalies = ts[ts.get("is_anomaly", False)] if "is_anomaly" in ts.columns else pd.DataFrame()
        if not anomalies.empty:
            fig.add_trace(go.Scatter(x=anomalies["period"], y=anomalies["revenue"],
                                      mode="markers", name="Anomaly",
                                      marker=dict(color=COLORS["danger"], size=12,
                                                  symbol="diamond-open", line=dict(width=2))))

        fig.update_layout(**PLOTLY_LAYOUT, title="Revenue Trend Analysis",
                           legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, use_container_width=True)

    with col_v2:
        if "growth_pct" in ts.columns:
            growth_df = ts.dropna(subset=["growth_pct"])
            if not growth_df.empty:
                colors = [COLORS["success"] if v >= 0 else COLORS["danger"]
                          for v in growth_df["growth_pct"]]
                fig = go.Figure()
                fig.add_trace(go.Bar(x=growth_df["period"], y=growth_df["growth_pct"],
                                      marker_color=colors, name="Growth %"))
                fig.update_layout(**PLOTLY_LAYOUT, title="Month-over-Month Growth Rate (%)")
                st.plotly_chart(fig, use_container_width=True)

    # ── Distribution + Z-Score
    col3, col4 = st.columns(2)
    
    with col3:
        fig = px.histogram(ts, x="revenue", nbins=15, title="Revenue Distribution",
                            color_discrete_sequence=[COLORS["primary"]])
        fig.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        if "z_score" in ts.columns:
            fig = go.Figure()
            colors = [COLORS["danger"] if abs(z) > 2 else COLORS["primary"]
                      for z in ts["z_score"]]
            fig.add_trace(go.Bar(x=ts["period"], y=ts["z_score"],
                                  marker_color=colors, name="Z-Score"))
            fig.add_hline(y=2, line_dash="dash", line_color=COLORS["danger"],
                           annotation_text="Upper threshold")
            fig.add_hline(y=-2, line_dash="dash", line_color=COLORS["danger"],
                           annotation_text="Lower threshold")
            fig.update_layout(**PLOTLY_LAYOUT, title="Z-Score Anomaly Detection")
            st.plotly_chart(fig, use_container_width=True)

    # ── Anomaly Details
    anomalies = analysis.get("anomalies", pd.DataFrame())
    if not anomalies.empty:
        with st.expander(f"Anomaly Details ({len(anomalies)} detected)", expanded=False):
            display_cols = [c for c in ["period", "revenue", "z_score", "growth_pct"] 
                            if c in anomalies.columns]
            st.dataframe(anomalies[display_cols], use_container_width=True)


# ── 🤖 AI AGENTS SIDEBAR CONTROLS ──────────────────────────────────
def render_agents_sidebar():
    """Render the AI agents cards selection block inside Streamlit sidebar."""
    st.sidebar.markdown("### 🤖 AI AGENTS")
    
    # Selected agent selection state
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent = "router"

    # Agent card renderer helper
    def render_agent_card(key: str, icon: str, name: str, desc: str, status_lbl: str, status_class: str):
        active_class = "agent-card-active" if st.session_state.selected_agent == key else ""
        card_html = f"""
        <div class="agent-card {active_class}">
            <div class="agent-title">{icon} {name}</div>
            <div class="agent-desc">{desc}</div>
            <div class="agent-status">Status: <span class="{status_class}">●</span> {status_lbl}</div>
        </div>
        """
        st.sidebar.markdown(card_html, unsafe_allow_html=True)
        if st.sidebar.button(f"Activate {name}", key=f"btn_{key}"):
            st.session_state.selected_agent = key
            st.rerun()

    # Route cards
    render_agent_card(
        "router", "🤖", "Auto Router", 
        "Routes requests dynamically using semantic classification.", 
        "Active" if st.session_state.selected_agent == "router" else "Idle",
        "status-dot-active" if st.session_state.selected_agent == "router" else "status-dot-available"
    )
    
    render_agent_card(
        "data", "📊", "Data Agent", 
        "Queries and visualizes Gold Layer business metrics.", 
        "Active" if st.session_state.selected_agent == "data" else "Idle",
        "status-dot-active" if st.session_state.selected_agent == "data" else "status-dot-available"
    )
    
    render_agent_card(
        "pipeline", "⚙️", "Pipeline Agent", 
        "Audit metadata and data quality runs logs.", 
        "Active" if st.session_state.selected_agent == "pipeline" else "Idle",
        "status-dot-active" if st.session_state.selected_agent == "pipeline" else "status-dot-available"
    )
    
    render_agent_card(
        "ml", "🧠", "ML Agent", 
        "Calculates z-score anomalies and trends regressions.", 
        "Active" if st.session_state.selected_agent == "ml" else "Idle",
        "status-dot-active" if st.session_state.selected_agent == "ml" else "status-dot-available"
    )

    render_agent_card(
        "forecast", "🔮", "Forecast Agent", 
        "Predicts future revenue using trend extrapolation.", 
        "Active" if st.session_state.selected_agent == "forecast" else "Idle",
        "status-dot-active" if st.session_state.selected_agent == "forecast" else "status-dot-available"
    )

    render_agent_card(
        "insight", "💡", "Insight Agent", 
        "Generates deep business insights from data.", 
        "Active" if st.session_state.selected_agent == "insight" else "Idle",
        "status-dot-active" if st.session_state.selected_agent == "insight" else "status-dot-available"
    )

    render_agent_card(
        "action", "🎯", "Action Agent", 
        "Recommends business actions based on insights.", 
        "Active" if st.session_state.selected_agent == "action" else "Idle",
        "status-dot-active" if st.session_state.selected_agent == "action" else "status-dot-available"
    )

    render_agent_card(
        "report", "📋", "Report Agent", 
        "Summarizes dashboard and provides executive overviews.", 
        "Active" if st.session_state.selected_agent == "report" else "Idle",
        "status-dot-active" if st.session_state.selected_agent == "report" else "status-dot-available"
    )
    
    render_agent_card(
        "general", "💬", "General Agent", 
        "Provides architectural & tech support.", 
        "Active" if st.session_state.selected_agent == "general" else "Idle",
        "status-dot-active" if st.session_state.selected_agent == "general" else "status-dot-available"
    )

    st.sidebar.markdown("---")

    # Quick Questions
    st.sidebar.markdown("❓ QUICK QUESTIONS")
    
    quick_queries = [
        ("data", "What are the top 5 product categories by revenue?", "Top Categories"),
        ("data", "Which region generated the most profit?", "Regional Profit"),
        ("forecast", "What will sales be next month?", "Sales Forecast"),
        ("insight", "Why did profit decrease?", "Profit Analysis"),
        ("action", "What actions can improve profit?", "Improve Profit"),
        ("report", "Summarize the dashboard.", "Dashboard Summary"),
        ("pipeline", "Show recent pipeline execution runs.", "ETL Runs"),
        ("ml", "Are there any revenue anomalies?", "Revenue Anomalies"),
    ]

    for agent_target, question_text, btn_label in quick_queries:
        if st.sidebar.button(f"💬 {btn_label}", key=f"qq_{btn_label.replace(' ', '_').lower()}"):
            st.session_state.selected_agent = agent_target
            # Force user query text entry to trigger analyst block
            st.session_state["quick_question_trigger"] = question_text
            st.rerun()


# ═════════════════════════════════════════════════════════════════
# NAVIGATION & MAIN
# ═════════════════════════════════════════════════════════════════

def main():
    """Main application with sidebar navigation."""
    # Build persistent left sidebar controls
    render_agents_sidebar()
    
    render_header()

    # Sidebar navigation
    with st.sidebar:
        st.markdown("")
        page = st.radio(
            "Navigation",
            ["AI Analyst", "Overview", "Pipeline Monitor", "Data Quality", "ML Insights"],
            index=0
        )
        st.markdown("---")
        st.markdown(
            '<div style="font-size:0.7rem; color:#475569; text-align:center; padding-top:12px;">'
            'Data Engineering PoC<br>Agentic AI Platform v1.0</div>',
            unsafe_allow_html=True
        )

    # Route to page
    if page == "Overview":
        page_overview()
    elif page == "AI Analyst":
        page_ai_analyst()
    elif page == "Pipeline Monitor":
        page_pipeline_monitor()
    elif page == "Data Quality":
        page_data_quality()
    elif page == "ML Insights":
        page_ml_insights()


if __name__ == "__main__":
    main()
