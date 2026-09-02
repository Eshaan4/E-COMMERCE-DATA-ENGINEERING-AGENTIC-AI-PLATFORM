"""
pipeline_agent.py – Explains ETL/ELT execution status and audit metrics.
"""
import os
import json
from google import genai
from agentic_ai.config import GEMINI_API_KEY, GEMINI_MODEL
from agentic_ai.prompts import PIPELINE_AGENT_PROMPT
from agentic_ai.tools import execute_safe_sql
from src.utils.db_utils import read_sql


def run_pipeline_agent(question: str, engine=None) -> dict:
    """
    Run pipeline metrics agent to fetch metadata details.
    """
    steps = [("Metadata context loaded", True)]
    
    if not GEMINI_API_KEY:
        return {"error": "Gemini API key is not configured.", "steps": [("API Key validation", False)]}
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
{PIPELINE_AGENT_PROMPT}

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
        return {"error": f"Failed to generate metadata query: {e}", "steps": steps}

    # Execute
    df, err = execute_safe_sql(sql, engine)
    if err:
        steps.append(("SQL execution", False))
        return {"error": err, "sql": sql, "steps": steps}
        
    steps.append(("SQL validated", True))
    steps.append((f"Metadata query executed ({len(df)} rows returned)", True))

    # Generate explanation
    analysis_prompt = f"""
You are the Lead Data Engineer.
Explain the pipeline run execution details returned below to answer the user's question.

User Question: {question}
Query: {sql}
Results:
{df.to_string()}

Provide your response in JSON format:
{{
  "answer": "Professional summary explaining the pipeline health status or audit details.",
  "action": "Suggested maintenance action (if any)."
}}
"""
    try:
        ans_resp = client.interactions.create(
            model=GEMINI_MODEL,
            input=analysis_prompt,
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
            "dataframe": df,
            "answer": ans_data.get("answer", ""),
            "action": ans_data.get("action", ""),
            "steps": steps
        }
    except Exception as e:
        steps.append(("Insight generation fallback applied", True))
        return {
            "sql": sql,
            "dataframe": df,
            "answer": f"Metadata scan loaded successfully. Retrieved {len(df)} pipeline records.",
            "action": "Examine raw metadata table results.",
            "steps": steps
        }


def get_pipeline_status(engine) -> dict:
    """Helper to return current pipeline stats for overview badges."""
    stats = {"status": "Healthy", "last_run": "None", "records": 0, "failed": 0}
    try:
        df = read_sql("""
            SELECT start_time, status, total_records_read, records_rejected 
            FROM metadata.pipeline_runs 
            ORDER BY start_time DESC LIMIT 1
        """, engine)
        if not df.empty:
            stats["status"] = "Healthy" if df["status"].iloc[0] == "SUCCESS" else "Warning"
            stats["last_run"] = df["start_time"].iloc[0].strftime("%Y-%m-%d %H:%M:%S")
            stats["records"] = int(df["total_records_read"].iloc[0])
            stats["failed"] = int(df["records_rejected"].iloc[0])
    except Exception:
        pass
    return stats
