"""
action_agent.py – Generates practical business action recommendations from insights.
"""
import os
import json
from google import genai
from agentic_ai.config import GEMINI_API_KEY, GEMINI_MODEL
from agentic_ai.prompts import ACTION_AGENT_PROMPT


def run_action_agent(question: str, insight_context: str, engine=None) -> dict:
    """
    Generate actionable business recommendations based on insights.

    Args:
        question: Original user question.
        insight_context: Insight text from the Insight Agent or Data Agent.
        engine: SQLAlchemy engine (unused directly).

    Returns:
        dict with recommended_action, rationale, steps.
    """
    steps = [("Action Agent activated", True)]

    if not GEMINI_API_KEY:
        return {
            "error": "Gemini API key is not configured.",
            "steps": [("API Key validation", False)],
        }

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""{ACTION_AGENT_PROMPT}

User Question: {question}

Insight Context:
{insight_context}
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
        steps.append(("Action recommendations generated", True))

        return {
            "action": res.get("recommended_action", ""),
            "rationale": res.get("rationale", ""),
            "steps": steps,
        }
    except Exception as e:
        steps.append(("Action generation failed", False))
        return {
            "action": "Review the data and insights above and consider targeted operational improvements.",
            "rationale": "",
            "error": str(e),
            "steps": steps,
        }
