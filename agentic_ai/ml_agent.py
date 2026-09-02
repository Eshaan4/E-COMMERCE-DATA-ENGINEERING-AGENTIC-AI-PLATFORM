"""
ml_agent.py – Performs statistical analytics, trend lines, percentage variation, and z-scores.
"""
import os
import json
import numpy as np
import pandas as pd
from google import genai
from agentic_ai.config import GEMINI_API_KEY, GEMINI_MODEL
from agentic_ai.prompts import ML_AGENT_PROMPT
from agentic_ai.tools import execute_safe_sql
from src.utils.db_utils import read_sql


def run_ml_agent(question: str, engine=None) -> dict:
    """
    Run machine learning agent to perform statistical analysis.
    """
    steps = [("Data loaded", True)]
    
    if not GEMINI_API_KEY:
        return {"error": "Gemini API key is not configured.", "steps": [("API Key validation", False)]}
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
{ML_AGENT_PROMPT}

User Question: {question}
"""
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
        sql = res_data.get("sql", "").strip()
        steps.append(("SQL generated", True))
    except Exception as e:
        return {"error": f"Failed to generate analysis query: {e}", "steps": steps}

    # Execute
    df, err = execute_safe_sql(sql, engine)
    if err:
        steps.append(("SQL execution", False))
        return {"error": err, "sql": sql, "steps": steps}
        
    steps.append(("SQL validated", True))
    steps.append((f"Data fetched ({len(df)} rows)", True))

    # Calculate statistics based on fetched results
    analysis = run_full_analysis(df, res_data.get("analysis_type", "trend"))
    steps.append(("Statistical processing completed", True))

    # Generate ML explanation
    ml_prompt = f"""
You are the Machine Learning Specialist.
Explain the statistical results returned below to answer the user's question.

User Question: {question}
Analysis Type: {res_data.get('analysis_type', 'trend')}
Dataset details: {len(df)} rows
Key Findings:
{str({k: v for k, v in analysis.items() if k != 'dataframe'})}

Provide your response in JSON format:
{{
  "answer": "Professional summary explaining the statistical findings, trend slopes, or anomalies.",
  "action": "Suggested business decision based on this statistical context."
}}
"""
    try:
        ans_resp = client.interactions.create(
            model=GEMINI_MODEL,
            input=ml_prompt,
        )
        ans_text = ans_resp.output_text.strip()
        if ans_text.startswith("```json"):
            ans_text = ans_text.split("```json")[1].split("```")[0].strip()
        elif ans_text.startswith("```"):
            ans_text = ans_text.split("```")[1].split("```")[0].strip()
            
        ans_data = json.loads(ans_text)
        steps.append(("Insight generated", True))
        
        return {
            "sql": sql,
            "dataframe": analysis.get("dataframe", df),
            "answer": ans_data.get("answer", ""),
            "insight": ans_data.get("answer", ""), # Sync for UI consistency
            "action": ans_data.get("action", ""),
            "anomalies": analysis.get("anomalies", pd.DataFrame()),
            "steps": steps
        }
    except Exception as e:
        steps.append(("Insight generation fallback applied", True))
        return {
            "sql": sql,
            "dataframe": analysis.get("dataframe", df),
            "answer": f"Statistical analysis complete. Computed trends and deviation metrics.",
            "insight": f"Statistical analysis complete. Computed trends and deviation metrics.",
            "action": "Check the rendered visualizations and data table details.",
            "steps": steps
        }


def run_full_analysis(df: pd.DataFrame, analysis_type: str) -> dict:
    """Perform actual calculations: moving average, z-score anomaly, linear trend line."""
    result = {"dataframe": df}
    
    if df.empty or len(df) < 2:
        return result

    # Standardize columns to lower for calculation
    df.columns = [c.lower() for c in df.columns]
    
    # Identify numeric column
    val_cols = [c for c in df.columns if c in ("revenue", "payment_value", "total_item_value", "price", "value")]
    if not val_cols:
        # Fallback to first numeric column
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        val_col = num_cols[0] if num_cols else None
    else:
        val_col = val_cols[0]

    if not val_col:
        return result

    # Cast to numeric to avoid type errors (Decimal etc.)
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce").astype(float)
    
    # 1. Trend Line (Linear Regression Slope)
    y = df[val_col].values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    df["trend_line"] = slope * x + intercept
    
    result["slope"] = slope
    result["direction"] = "increasing" if slope > 0 else "decreasing"
    
    # 2. Moving Average
    df["ma_3"] = df[val_col].rolling(window=3, min_periods=1).mean()
    
    # 3. MoM growth pct
    if len(df) > 1:
        df["growth_pct"] = df[val_col].pct_change() * 100
        result["avg_growth_pct"] = float(df["growth_pct"].mean())

    # 4. Z-Score Anomaly detection
    mean = np.mean(y)
    std = np.std(y) if np.std(y) > 0 else 1.0
    z_scores = (y - mean) / std
    df["z_score"] = z_scores
    df["is_anomaly"] = np.abs(z_scores) > 2.0
    
    anomalies = df[df["is_anomaly"]]
    result["anomalies_detected"] = len(anomalies)
    result["anomalies"] = anomalies
    result["highest_deviation"] = float(np.max(np.abs(z_scores)))
    
    return result


def get_revenue_time_series(engine) -> pd.DataFrame:
    """Fetch monthly revenue time series directly from revenue mart."""
    try:
        df = read_sql("""
            SELECT (year::text || '-' || LPAD(month::text, 2, '0')) AS period, 
                   SUM(total_revenue) AS revenue
            FROM gold.revenue_mart
            GROUP BY year, month
            ORDER BY year, month
        """, engine)
        
        # Cast loaded sql column to float to avoid decimal type issues
        if not df.empty:
            df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").astype(float)
            
        return df
    except Exception:
        return pd.DataFrame()
