"""
tools.py – Shared helper utilities for visualization, color palettes, and query execution.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from src.utils.db_utils import get_engine

# Theme color palette matching Sleek Dark Mode theme
COLORS = {
    "primary": "#6366F1",    # Indigo accent
    "secondary": "#8B5CF6",  # Violet accent
    "success": "#10B981",    # Emerald green
    "warning": "#F59E0B",    # Amber warning
    "danger": "#EF4444",     # Rose alert
    "background": "#0F172A",  # Dark slate background
    "card": "#1E293B",        # Light card color
}

PLOTLY_LAYOUT = {
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "font_color": "#CBD5E1",
    "font_family": "Inter, sans-serif",
    "margin": dict(l=40, r=20, t=40, b=40),
}


def create_chart(df: pd.DataFrame, chart_type: str, x: str, y: str, title: str = ""):
    """Create a Plotly chart styled according to the enterprise design guidelines."""
    chart_type = chart_type.lower()
    
    if chart_type == "line":
        fig = px.line(df, x=x, y=y, title=title, color_discrete_sequence=[COLORS["primary"]])
        fig.update_traces(line=dict(width=2.5))
    elif chart_type == "bar":
        fig = px.bar(df, x=x, y=y, title=title, color_discrete_sequence=[COLORS["primary"]])
    elif chart_type == "pie":
        fig = px.pie(df, names=x, values=y, title=title, hole=0.4,
                     color_discrete_sequence=[COLORS["primary"], COLORS["secondary"], COLORS["success"], COLORS["warning"]])
    else:
        # Fallback table visual (handled separately)
        fig = go.Figure()
        
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


def format_number(val) -> str:
    """Helper to format numbers professionally."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        val_float = float(val)
        if val_float >= 1_000_000:
            return f"R${val_float/1_000_000:.1f}M"
        elif val_float >= 1_000:
            return f"{val_float/1_000:.1f}K"
        elif val_float.is_integer():
            return f"{int(val_float):,}"
        else:
            return f"{val_float:,.2f}"
    except ValueError:
        return str(val)


def execute_safe_sql(sql: str, engine=None) -> tuple[pd.DataFrame, str]:
    """
    Validate and execute a read-only PostgreSQL query.
    Returns:
        (DataFrame, error_message)
    """
    error_msg = ""
    df = pd.DataFrame()
    
    # 1. SQL security check
    sql_upper = sql.upper().strip()
    
    # Block multiple statements (semicolons)
    if ";" in sql_upper and sql_upper.find(";") < len(sql_upper) - 1:
        return df, "Execution blocked: Multiple SQL statements detected."
        
    blocked_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
    for word in blocked_keywords:
        # Check matching word boundary
        if f" {word} " in f" {sql_upper} " or sql_upper.startswith(word):
            return df, f"Security violation: Keyword '{word}' is not allowed in read-only mode."
            
    # Verify it starts with allowed keywords
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return df, "Security violation: Only SELECT and WITH queries are allowed."

    # 2. Run query
    _engine = engine or get_engine()
    try:
        with _engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            cols = result.keys()
            df = pd.DataFrame(rows, columns=list(cols))
    except Exception as e:
        error_msg = f"Database query execution error: {e}"
        
    return df, error_msg
