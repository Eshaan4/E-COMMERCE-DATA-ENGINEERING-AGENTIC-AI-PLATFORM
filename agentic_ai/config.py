"""
config.py – Centralized configuration for the Agentic AI Data Intelligence Platform.
Reuses existing db_utils for database connectivity.
"""
import os
import sys
from pathlib import Path
from sqlalchemy import text

# ── Ensure project root is on sys.path ──────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

# ── Reuse existing database utilities ───────────────────────────
from src.utils.db_utils import get_engine, read_sql, get_connection_string

# ── Gemini Configuration ────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.6-flash"

# ── Application Constants ───────────────────────────────────────
APP_TITLE = "Agentic AI Data Intelligence Platform"
APP_SUBTITLE = "Business Intelligence \u2022 Data Engineering \u2022 AI-Powered Analytics"

# Gold schema tables used by the Data Agent
GOLD_TABLES = [
    "gold.fact_sales",
    "gold.dim_customer",
    "gold.dim_product",
    "gold.dim_seller",
    "gold.dim_date",
    "gold.revenue_mart",
    "gold.kpi_summary",
]

METADATA_TABLES = [
    "metadata.pipeline_runs",
    "metadata.dq_results",
    "metadata.error_log",
    "metadata.watermarks",
    "metadata.schema_changes",
]


def get_gold_schema_context(engine=None) -> str:
    """
    Retrieve actual Gold + Metadata schema from PostgreSQL information_schema.
    Returns a formatted string for injecting into LLM prompts.
    """
    _engine = engine or get_engine()
    query = """
        SELECT 
            table_schema || '.' || table_name AS full_table,
            column_name, 
            data_type
        FROM information_schema.columns
        WHERE table_schema IN ('gold', 'metadata')
        ORDER BY table_schema, table_name, ordinal_position
    """
    try:
        df = read_sql(query, _engine)
        if df.empty:
            return "No schema metadata found."
        
        schema_dict = {}
        for _, r in df.iterrows():
            tbl = r["full_table"]
            col = r["column_name"]
            dtype = r["data_type"]
            schema_dict.setdefault(tbl, []).append(f"  - {col} ({dtype})")
            
        context_lines = ["Actual Database Schema Context:"]
        for tbl, cols in schema_dict.items():
            context_lines.append(f"Table: {tbl}")
            context_lines.extend(cols)
            context_lines.append("")
        return "\n".join(context_lines)
    except Exception as e:
        return f"Error retrieving database schema metadata: {e}"


def check_database_connection(engine=None) -> bool:
    """Safely check if the PostgreSQL database is connected and responding."""
    _engine = engine or get_engine()
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def check_gemini_connection() -> bool:
    """Check if the Gemini API key is configured and valid."""
    if not GEMINI_API_KEY:
        return False
    # Verify API key structure and presence
    return len(GEMINI_API_KEY) > 10 and not GEMINI_API_KEY.startswith("YOUR_")
