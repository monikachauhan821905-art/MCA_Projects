"""Simple, transparent outbreak alert engine for the dashboard.

Alerts are analytics signals, not medical/public-health decisions.
"""

import numpy as np
import pandas as pd


def build_alerts(history, forecast):
    h = history.copy()
    h["date"] = pd.to_datetime(h["date"])
    h = h.sort_values("date")
    forecast = forecast.copy()
    forecast["date"] = pd.to_datetime(forecast["date"])

    # Seasonal baseline: historical median for the same calendar month.
    baseline = h.groupby(h["date"].dt.month)["cases"].median().to_dict()
    rows = []
    for _, r in forecast.iterrows():
        month = r["date"].month
        base = float(baseline.get(month, h["cases"].median()))
        ratio = float(r["forecast_cases"]) / max(base, 1)
        if ratio >= 1.75 or float(r["upper"]) >= max(base * 2.0, 1):
            level = "High"
        elif ratio >= 1.30:
            level = "Moderate"
        else:
            level = "Low"
        rows.append({
            "date": r["date"],
            "alert_level": level,
            "forecast_cases": float(r["forecast_cases"]),
            "seasonal_baseline": round(base, 1),
            "forecast_vs_baseline_pct": round((ratio - 1) * 100, 1),
            "message": (
                "Forecast is substantially above the historical seasonal baseline."
                if level == "High" else
                "Forecast is above the historical seasonal baseline."
                if level == "Moderate" else
                "Forecast is within the historical seasonal range."
            ),
        })
    return pd.DataFrame(rows)
