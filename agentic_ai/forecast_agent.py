"""
forecast_agent.py – Generates revenue forecasts using linear extrapolation.
Reuses existing get_revenue_time_series() and numpy polyfit approach.
"""
import os
import json
import numpy as np
import pandas as pd
from google import genai
from agentic_ai.config import GEMINI_API_KEY, GEMINI_MODEL
from agentic_ai.prompts import FORECAST_AGENT_PROMPT
from agentic_ai.ml_agent import get_revenue_time_series


def _generate_forecast(engine, periods: int = 3) -> dict:
    """
    Generate a simple linear extrapolation forecast.

    Returns dict with historical data, forecast values, trend info.
    """
    ts = get_revenue_time_series(engine)

    if ts.empty or len(ts) < 3:
        return {"error": "Insufficient historical data for forecasting (need at least 3 months)."}

    # Linear regression on historical data
    y = ts["revenue"].values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)

    # Generate forecast points
    forecast_x = np.arange(len(y), len(y) + periods)
    forecast_y = slope * forecast_x + intercept

    # Build forecast period labels
    last_period = ts["period"].iloc[-1]  # e.g. "2018-08"
    last_year, last_month = int(last_period.split("-")[0]), int(last_period.split("-")[1])

    forecast_periods = []
    for i in range(1, periods + 1):
        m = last_month + i
        yr = last_year + (m - 1) // 12
        mo = ((m - 1) % 12) + 1
        forecast_periods.append(f"{yr}-{mo:02d}")

    # Historical stats
    avg_revenue = float(np.mean(y))
    last_revenue = float(y[-1])
    trend_direction = "increasing" if slope > 0 else "decreasing"

    # Month-over-month growth from last known
    forecast_values = []
    for i, fv in enumerate(forecast_y):
        prev = last_revenue if i == 0 else float(forecast_y[i - 1])
        growth = ((float(fv) - prev) / prev * 100) if prev > 0 else 0
        forecast_values.append({
            "period": forecast_periods[i],
            "forecast_revenue": round(float(fv), 2),
            "growth_pct": round(growth, 1),
        })

    # Build combined DataFrame for visualization
    hist_df = ts[["period", "revenue"]].copy()
    hist_df["type"] = "Historical"
    hist_df["trend_line"] = slope * x + intercept

    fc_df = pd.DataFrame({
        "period": forecast_periods,
        "revenue": forecast_y,
        "type": "Forecast",
        "trend_line": forecast_y,
    })

    combined = pd.concat([hist_df, fc_df], ignore_index=True)

    return {
        "dataframe": combined,
        "forecast_values": forecast_values,
        "trend_direction": trend_direction,
        "slope_per_month": round(float(slope), 2),
        "avg_historical_revenue": round(avg_revenue, 2),
        "last_known_revenue": round(last_revenue, 2),
        "periods_forecasted": periods,
        "historical_months": len(ts),
    }


def run_forecast_agent(question: str, engine=None) -> dict:
    """
    Run the forecast agent to predict future revenue.
    """
    steps = [("Forecast Agent activated", True)]

    # Determine forecast periods from the question
    periods = 3  # default: next quarter
    q_lower = question.lower()
    if "next month" in q_lower or "1 month" in q_lower:
        periods = 1
    elif "6 month" in q_lower or "half year" in q_lower:
        periods = 6
    elif "next year" in q_lower or "12 month" in q_lower:
        periods = 12

    # Generate forecast
    forecast = _generate_forecast(engine, periods)

    if "error" in forecast:
        steps.append(("Forecast generation failed", False))
        return {"error": forecast["error"], "steps": steps}

    steps.append((f"Forecast computed ({periods} periods ahead)", True))

    # Build context for LLM explanation
    fc_summary = "\n".join([
        f"  {fv['period']}: R${fv['forecast_revenue']:,.2f} ({fv['growth_pct']:+.1f}%)"
        for fv in forecast["forecast_values"]
    ])
    context = (
        f"Trend: {forecast['trend_direction']} (slope R${forecast['slope_per_month']:,.2f}/month)\n"
        f"Last known revenue: R${forecast['last_known_revenue']:,.2f}\n"
        f"Historical average: R${forecast['avg_historical_revenue']:,.2f}\n"
        f"Based on {forecast['historical_months']} months of data\n"
        f"Forecast:\n{fc_summary}"
    )

    if not GEMINI_API_KEY:
        return {
            "answer": f"**Revenue Forecast**\n\n{context}",
            "dataframe": forecast.get("dataframe"),
            "steps": steps,
        }

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""{FORECAST_AGENT_PROMPT}

User Question: {question}

Forecast Data:
{context}
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
        steps.append(("Forecast explanation generated", True))

        return {
            "answer": res.get("answer", ""),
            "insight": res.get("insight", ""),
            "action": res.get("action", ""),
            "dataframe": forecast.get("dataframe"),
            "steps": steps,
        }
    except Exception as e:
        steps.append(("Forecast explanation fallback", True))
        return {
            "answer": f"**Revenue Forecast**\n\n{context}",
            "dataframe": forecast.get("dataframe"),
            "steps": steps,
        }
