"""
insight_agent.py – Generates deep business insights from data results.
Identifies trends, anomalies, top/bottom performers, period comparisons.
"""
import os
import json
from google import genai
from agentic_ai.config import GEMINI_API_KEY, GEMINI_MODEL
from agentic_ai.prompts import INSIGHT_AGENT_PROMPT


def run_insight_agent(question: str, data_context: str, engine=None) -> dict:
    """
    Analyze data results and generate business insights.

    Args:
        question: Original user question.
        data_context: Stringified data/results from the Data Agent or other sources.
        engine: SQLAlchemy engine (unused directly, but kept for interface consistency).

    Returns:
        dict with insight, evidence, action, steps.
    """
    steps = [("Insight Agent activated", True)]

    if not GEMINI_API_KEY:
        return {
            "error": "Gemini API key is not configured.",
            "steps": [("API Key validation", False)],
        }

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""{INSIGHT_AGENT_PROMPT}

User Question: {question}

Data Context:
{data_context}
"""
    try:
        response = client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt,
        )
        text = response.output_text.strip()

        # Clean markdown wrappers
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        elif text.startswith("```"):
            text = text.split("```")[1].split("```")[0].strip()

        res = json.loads(text)
        steps.append(("Business insight generated", True))

        return {
            "insight": res.get("insight", ""),
            "evidence": res.get("evidence", []),
            "steps": steps,
        }
    except Exception as e:
        steps.append(("Insight generation failed", False))
        return {
            "insight": "Based on the available data, further analysis is needed to draw specific conclusions.",
            "evidence": [],
            "error": str(e),
            "steps": steps,
        }
