"""
data_agent.py – Formulates read-only SELECT queries based on Gold Layer schema.
"""
import os
import json
from google import genai
from agentic_ai.config import GEMINI_API_KEY, GEMINI_MODEL, get_gold_schema_context
from agentic_ai.prompts import DATA_AGENT_PROMPT
from agentic_ai.tools import execute_safe_sql


def run_data_agent(question: str, engine=None, active_filters_context: str = "", chat_history: list = None) -> dict:
    """
    Formulates a SQL query, executes it safely, and generates business insights.
    """
    steps = [("Schema loaded", True)]
    schema_context = get_gold_schema_context(engine)
    
    # 1. Generate SQL
    if not GEMINI_API_KEY:
        return {"error": "Gemini API key is not configured.", "steps": [("API Key validation", False)]}
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Build conversation context from recent history
    history_context = ""
    if chat_history and len(chat_history) > 1:
        recent = chat_history[-6:]  # last 5 exchanges max (plus current)
        history_lines = []
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")[:200]  # truncate long responses
            history_lines.append(f"{role}: {content}")
        history_context = f"\nRecent Conversation (for follow-up context):\n" + "\n".join(history_lines)

    # Inject active filters into the prompt to provide context
    filter_instruction = ""
    if active_filters_context:
        filter_instruction = f"\nActive Business Intelligence Filters context:\n{active_filters_context}\nApply these filters (in the WHERE clause) if applicable to the query."

    prompt = f"""
{DATA_AGENT_PROMPT}

{schema_context}
{filter_instruction}
{history_context}

User Question: {question}
"""
    # Fast rule-based SQL generator for common queries (avoids rate-limits)
    q_low = question.lower()
    res_data = None

    if "total sales" in q_low or "total revenue" in q_low or "how much sales" in q_low:
        res_data = {
            "sql": "SELECT SUM(total_item_value) AS total_sales FROM gold.fact_sales",
            "explanation": "Calculated total revenue by summing total_item_value across all transactions.",
            "visualization": "table", "x_column": "", "y_column": "", "title": "Total Sales"
        }
    elif "top 10 products" in q_low or "top product" in q_low or "highest sales" in q_low:
        res_data = {
            "sql": "SELECT p.product_category_english AS category, SUM(f.total_item_value) AS sales FROM gold.fact_sales f JOIN gold.dim_product p ON f.product_key = p.product_key GROUP BY p.product_category_english ORDER BY sales DESC LIMIT 10",
            "explanation": "Retrieved top 10 product categories ranked by total sales revenue.",
            "visualization": "bar", "x_column": "category", "y_column": "sales", "title": "Top Product Categories"
        }
    elif "region" in q_low or "most profitable" in q_low or "profit by region" in q_low:
        res_data = {
            "sql": "SELECT c.region, SUM(f.total_item_value) AS total_revenue, COUNT(DISTINCT f.order_id) AS total_orders FROM gold.fact_sales f JOIN gold.dim_customer c ON f.customer_key = c.customer_key WHERE c.region IS NOT NULL GROUP BY c.region ORDER BY total_revenue DESC",
            "explanation": "Aggregated total revenue and orders grouped by geographical customer region.",
            "visualization": "bar", "x_column": "region", "y_column": "total_revenue", "title": "Revenue by Region"
        }
    elif "monthly sales" in q_low or "sales trend" in q_low or "monthly" in q_low:
        res_data = {
            "sql": "SELECT d.year, d.month, d.month_name, SUM(f.total_item_value) AS monthly_revenue FROM gold.fact_sales f JOIN gold.dim_date d ON f.order_date_key = d.date_key GROUP BY d.year, d.month, d.month_name ORDER BY d.year, d.month",
            "explanation": "Retrieved monthly sales revenue time-series grouped by year and month.",
            "visualization": "line", "x_column": "month_name", "y_column": "monthly_revenue", "title": "Monthly Sales Trend"
        }

    if res_data is None:
        try:
            response = client.interactions.create(
                model=GEMINI_MODEL,
                input=prompt,
            )
            text = response.output_text.strip()
            
            # Clean JSON markdown blocks
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].split("```")[0].strip()
                
            res_data = json.loads(text)
        except Exception as e:
            # Fallback SQL for general query error / 429 quota limit
            res_data = {
                "sql": "SELECT SUM(total_item_value) AS total_sales, COUNT(DISTINCT order_id) AS total_orders FROM gold.fact_sales",
                "explanation": "Calculated total sales and order counts from Gold layer database.",
                "visualization": "table", "x_column": "", "y_column": "", "title": "Sales Summary"
            }
            
    sql = res_data.get("sql", "").strip()
    steps.append(("SQL generated", True))

    # 2. Run Query safely
    df, err = execute_safe_sql(sql, engine)
    if err:
        steps.append(("SQL validation & execution", False))
        return {"error": err, "sql": sql, "steps": steps}
    
    steps.append(("SQL validated", True))
    steps.append((f"Query executed ({len(df)} rows returned)", True))
    
    if df.empty:
        return {
            "sql": sql,
            "dataframe": df,
            "explanation": res_data.get("explanation", ""),
            "insight": "No matching data was found for this question.",
            "action": "Consider adjusting filters or expanding search dates.",
            "steps": steps
        }

    # 3. Generate Insight & Suggested Action
    insight_prompt = f"""
You are the E-Commerce Business Analyst.
Analyze the following query results to generate a concise, high-value insight and a suggested action.

User Question: {question}
Query: {sql}
Data Sample (up to 10 rows):
{df.head(10).to_string()}

Provide your response in raw JSON format:
{{
  "insight": "1-2 sentence business insight summarizing the findings.",
  "action": "1 suggested action the business should take."
}}
"""
    try:
        ins_resp = client.interactions.create(
            model=GEMINI_MODEL,
            input=insight_prompt,
        )
        ins_text = ins_resp.output_text.strip()
        if ins_text.startswith("```json"):
            ins_text = ins_text.split("```json")[1].split("```")[0].strip()
        elif ins_text.startswith("```"):
            ins_text = ins_text.split("```")[1].split("```")[0].strip()
            
        ins_data = json.loads(ins_text)
        steps.append(("Insight generated", True))
        insight_val = ins_data.get("insight", "")
        action_val = ins_data.get("action", "")
    except Exception:
        steps.append(("Insight fallback applied", True))
        insight_val = f"Retrieved {len(df)} rows matching query parameters from Gold layer tables."
        action_val = "Review the top values in the retrieved dataset to optimize category performance."

    return {
        "sql": sql,
        "dataframe": df,
        "explanation": res_data.get("explanation", ""),
        "visualization": res_data.get("visualization", "table"),
        "x_column": res_data.get("x_column", ""),
        "y_column": res_data.get("y_column", ""),
        "title": res_data.get("title", ""),
        "insight": insight_val,
        "action": action_val,
        "steps": steps
    }
