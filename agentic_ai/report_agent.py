"""
report_agent.py – Summarizes dashboard state using real data from Gold + Metadata layers.
"""
import os
import json
from google import genai
from agentic_ai.config import GEMINI_API_KEY, GEMINI_MODEL
from agentic_ai.prompts import REPORT_AGENT_PROMPT
from src.utils.db_utils import read_sql


def _fetch_dashboard_summary(engine) -> str:
    """Gather key metrics from the database to build a dashboard summary context."""
    sections = []

    # 1. Revenue KPIs
    try:
        kpi_df = read_sql("""
            SELECT
                COALESCE(SUM(total_item_value), 0) AS total_revenue,
                COUNT(DISTINCT order_id) AS total_orders,
                COALESCE(AVG(total_item_value), 0) AS avg_order_value,
                COUNT(DISTINCT customer_key) AS total_customers,
                COUNT(DISTINCT product_key) AS total_products
            FROM gold.fact_sales
        """, engine)
        if not kpi_df.empty:
            r = kpi_df.iloc[0]
            sections.append(
                f"Sales Overview: Total Revenue R${float(r['total_revenue']):,.2f}, "
                f"Total Orders {int(r['total_orders']):,}, "
                f"Avg Order Value R${float(r['avg_order_value']):,.2f}, "
                f"Unique Customers {int(r['total_customers']):,}, "
                f"Unique Products {int(r['total_products']):,}"
            )
    except Exception:
        sections.append("Sales Overview: Data unavailable")

    # 2. Top categories
    try:
        cat_df = read_sql("""
            SELECT p.product_category_english AS category, SUM(f.total_item_value) AS revenue
            FROM gold.fact_sales f
            JOIN gold.dim_product p ON f.product_key = p.product_key
            GROUP BY p.product_category_english
            ORDER BY revenue DESC LIMIT 5
        """, engine)
        if not cat_df.empty:
            lines = [f"  {row['category']}: R${float(row['revenue']):,.2f}" for _, row in cat_df.iterrows()]
            sections.append("Top 5 Categories by Revenue:\n" + "\n".join(lines))
    except Exception:
        pass

    # 3. Top regions
    try:
        reg_df = read_sql("""
            SELECT c.region, SUM(f.total_item_value) AS revenue
            FROM gold.fact_sales f
            JOIN gold.dim_customer c ON f.customer_key = c.customer_key
            WHERE c.region IS NOT NULL
            GROUP BY c.region
            ORDER BY revenue DESC
        """, engine)
        if not reg_df.empty:
            lines = [f"  {row['region']}: R${float(row['revenue']):,.2f}" for _, row in reg_df.iterrows()]
            sections.append("Revenue by Region:\n" + "\n".join(lines))
    except Exception:
        pass

    # 4. Revenue trend (last 6 months from revenue_mart)
    try:
        trend_df = read_sql("""
            SELECT year, month, month_name, SUM(total_revenue) AS revenue,
                   AVG(mom_growth_pct) AS avg_growth
            FROM gold.revenue_mart
            GROUP BY year, month, month_name
            ORDER BY year DESC, month DESC
            LIMIT 6
        """, engine)
        if not trend_df.empty:
            lines = [
                f"  {row['month_name'].strip()} {row['year']}: R${float(row['revenue']):,.2f} "
                f"(MoM: {float(row['avg_growth'] or 0):+.1f}%)"
                for _, row in trend_df.iterrows()
            ]
            sections.append("Recent Revenue Trend (last 6 months):\n" + "\n".join(lines))
    except Exception:
        pass

    # 5. Pipeline health
    try:
        pipe_df = read_sql("""
            SELECT pipeline_name, status, start_time, total_records_read, records_rejected
            FROM metadata.pipeline_runs
            ORDER BY start_time DESC LIMIT 3
        """, engine)
        if not pipe_df.empty:
            lines = [
                f"  {row['pipeline_name']}: {row['status']} ({row['start_time']})"
                for _, row in pipe_df.iterrows()
            ]
            sections.append("Recent Pipeline Runs:\n" + "\n".join(lines))
    except Exception:
        pass

    # 6. Data quality
    try:
        dq_df = read_sql("""
            SELECT COUNT(*) AS total, SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS passed,
                   AVG(success_pct) AS avg_score
            FROM metadata.dq_results
        """, engine)
        if not dq_df.empty:
            r = dq_df.iloc[0]
            sections.append(
                f"Data Quality: {int(r['passed'] or 0)}/{int(r['total'] or 0)} checks passed, "
                f"Avg Score {float(r['avg_score'] or 0):.1f}%"
            )
    except Exception:
        pass

    return "\n\n".join(sections) if sections else "Dashboard data is currently unavailable."


def run_report_agent(question: str, engine=None) -> dict:
    """
    Summarize the dashboard / report state using real data.
    """
    steps = [("Report Agent activated", True)]

    # Fetch real dashboard data
    summary_context = _fetch_dashboard_summary(engine)
    steps.append(("Dashboard data gathered", True))

    if not GEMINI_API_KEY:
        # Return raw summary without LLM formatting
        return {
            "answer": summary_context,
            "steps": steps,
        }

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""{REPORT_AGENT_PROMPT}

User Question: {question}

Current Dashboard Data:
{summary_context}
"""
    try:
        response = client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt,
        )
        text = response.output_text.strip()

        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        elif text.startswith("```"):
            text = text.split("```")[1].split("```")[0].strip()

        res = json.loads(text)
        steps.append(("Report summary generated", True))

        return {
            "answer": res.get("summary", ""),
            "insight": res.get("key_finding", ""),
            "action": res.get("management_focus", ""),
            "steps": steps,
        }
    except Exception as e:
        steps.append(("LLM summarization failed, returning raw data", True))
        return {
            "answer": summary_context,
            "error": str(e),
            "steps": steps,
        }
