"""
router_agent.py – Classify user query intent and route to one or more specialist agents.
Supports multi-agent chaining for complex questions.
"""
import os
import json
from google import genai
from agentic_ai.config import GEMINI_API_KEY, GEMINI_MODEL
from agentic_ai.prompts import ROUTER_PROMPT

AGENT_INFO = {
    "data": {
        "name": "Data Agent",
        "icon": "📊",
        "description": "Queries Gold-layer business data using natural-language questions and generates SQL, insights and visualizations.",
    },
    "pipeline": {
        "name": "Pipeline Agent",
        "icon": "⚙️",
        "description": "Monitors pipeline executions, metadata, ETL/ELT status and data quality.",
    },
    "ml": {
        "name": "ML Agent",
        "icon": "🧠",
        "description": "Performs trend analysis, anomaly detection and statistical insights.",
    },
    "forecast": {
        "name": "Forecast Agent",
        "icon": "🔮",
        "description": "Predicts future revenue using historical trend extrapolation.",
    },
    "insight": {
        "name": "Insight Agent",
        "icon": "💡",
        "description": "Generates deep business insights from analytical results.",
    },
    "action": {
        "name": "Action Agent",
        "icon": "🎯",
        "description": "Recommends practical business actions based on data insights.",
    },
    "report": {
        "name": "Report Agent",
        "icon": "📋",
        "description": "Summarizes dashboard pages and provides executive-level overviews.",
    },
    "general": {
        "name": "General Agent",
        "icon": "💬",
        "description": "Handles general project and data-related questions.",
    },
}


def route_question(question: str) -> dict:
    """
    Query Gemini model or fast rules to classify the user's intent.
    Returns:
        {"agents": ["data", "insight", ...]}
    """
    q_low = question.lower()
    if "total sales" in q_low or "top 10" in q_low or "region" in q_low or "monthly sales" in q_low or "sales" in q_low and "forecast" not in q_low:
        return {"agents": ["data"]}
    elif "forecast" in q_low or "predict" in q_low or "next month" in q_low:
        return {"agents": ["forecast"]}
    elif "why" in q_low or "decrease" in q_low or "drop" in q_low:
        return {"agents": ["data", "insight"]}
    elif "focus" in q_low or "action" in q_low or "improve" in q_low or "should we" in q_low:
        return {"agents": ["data", "insight", "action"]}
    elif "summarize" in q_low or "dashboard" in q_low or "report" in q_low:
        return {"agents": ["report"]}
    elif "pipeline" in q_low or "etl" in q_low or "run" in q_low:
        return {"agents": ["pipeline"]}
    elif "anomaly" in q_low or "trend" in q_low or "ml" in q_low:
        return {"agents": ["ml"]}

    fallback = {"agents": ["general"]}
    if not GEMINI_API_KEY:
        return fallback

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.interactions.create(
            model=GEMINI_MODEL,
            input=f"{ROUTER_PROMPT}\n\nUser Question:\n{question}",
        )
        text = response.output_text.strip()

        # Clean markdown wrappers if any
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        elif text.startswith("```"):
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)

        # Support both old {"category": "..."} and new {"agents": [...]} format
        if "agents" in data:
            agents = [a for a in data["agents"] if a in AGENT_INFO]
            if agents:
                return {"agents": agents}
        elif "category" in data and data["category"] in AGENT_INFO:
            return {"agents": [data["category"]]}

        return fallback
    except Exception:
        return fallback
