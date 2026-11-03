"""OutbreakIQ Real Data Dashboard.

Run from project root:
    streamlit run app/dashboard.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models.alert_engine import build_alerts

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "real_dengue_weather.csv"
FORECAST = ROOT / "models" / "forecast_next.csv"
VALIDATION = ROOT / "models" / "forecast_validation.csv"
METRICS = ROOT / "models" / "forecast_metrics.json"
META = ROOT / "data" / "real_data_metadata.json"

st.set_page_config(page_title="OutbreakIQ | Real Data", page_icon="🩺", layout="wide")

st.markdown("""
<style>
.hero{padding:1.4rem 1.6rem;border-radius:18px;background:linear-gradient(120deg,#0f766e,#155e75);color:white;margin-bottom:1rem}
.hero h1{margin:0;font-size:2.2rem}.hero p{margin:.4rem 0 0;opacity:.92}
.card{padding:1rem;border:1px solid #e5e7eb;border-radius:14px;background:white}
</style>
""", unsafe_allow_html=True)

if not DATA.exists() or not FORECAST.exists():
    st.markdown('<div class="hero"><h1>🩺 OutbreakIQ — Real Data Edition</h1><p>Real dengue surveillance + real historical weather + time-aware forecasting</p></div>', unsafe_allow_html=True)
    st.warning("The real-data pipeline has not been run yet.")
    st.code("python run_pipeline.py --country India\nstreamlit run app/dashboard.py", language="bash")
    st.markdown("""
### What this upgraded version uses

- **Disease:** OpenDengue, a peer-reviewed database of publicly available dengue case counts.
- **Weather:** Open-Meteo historical weather/reanalysis data.
- **Validation:** expanding-window time-series validation; no random shuffling.
- **Forecast:** seasonal SARIMAX with uncertainty intervals.
- **Alerts:** transparent comparison against historical seasonal baselines.
""")
    st.stop()

@st.cache_data
def load():
    d = pd.read_csv(DATA, parse_dates=["date"]).sort_values("date")
    f = pd.read_csv(FORECAST, parse_dates=["date"])
    v = pd.read_csv(VALIDATION, parse_dates=["date"])
    metrics = json.loads(METRICS.read_text()) if METRICS.exists() else {}
    meta = json.loads(META.read_text()) if META.exists() else {}
    return d, f, v, metrics, meta

history, forecast, validation, metrics, meta = load()
alerts = build_alerts(history, forecast)

st.markdown(f'<div class="hero"><h1>🩺 OutbreakIQ</h1><p>{meta.get("country", "Selected country")} • Real disease surveillance + weather analytics</p></div>', unsafe_allow_html=True)
st.caption("Academic early-warning prototype. It is not a medical diagnosis or an operational public-health alert system.")

# Sidebar filters
st.sidebar.header("⚙️ Controls")
months_back = st.sidebar.slider("History shown (months)", 12, min(120, len(history)), min(60, len(history)))
view = history.tail(months_back).copy()

k1, k2, k3, k4 = st.columns(4)
k1.metric("📊 Latest reported cases", f"{int(history['cases'].iloc[-1]):,}")
k2.metric("📈 Next-month forecast", f"{int(forecast['forecast_cases'].iloc[0]):,}")
k3.metric("🧪 Holdout MAE", f"{metrics.get('holdout_mae', 0):,.0f}")
k4.metric("🚨 Alerts", int((alerts['alert_level'] != 'Low').sum()))

trend_tab, weather_tab, forecast_tab, alert_tab, validation_tab, data_tab = st.tabs([
    "📈 Disease Trend", "🌦️ Weather", "🔮 Forecast", "🚨 Alerts", "🧪 Validation", "📁 Data"
])

with trend_tab:
    st.subheader("Reported dengue cases over time")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=view.date, y=view.cases, mode="lines+markers", name="Reported cases"))
    fig.update_layout(height=430, xaxis_title="Month", yaxis_title="Reported cases")
    st.plotly_chart(fig, use_container_width=True)

    st.info("The disease series comes from reported surveillance records. Reporting completeness and case definitions can vary by place and time.")

with weather_tab:
    st.subheader("Real historical weather")
    w1, w2 = st.columns(2)
    with w1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=view.date, y=view.rainfall_mm, mode="lines", name="Rainfall (mm)"))
        fig.update_layout(height=350, title="Monthly rainfall", xaxis_title="Month", yaxis_title="mm")
        st.plotly_chart(fig, use_container_width=True)
    with w2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=view.date, y=view.avg_temp_c, mode="lines", name="Temperature (°C)"))
        fig.add_trace(go.Scatter(x=view.date, y=view.humidity_pct, mode="lines", name="Humidity (%)", yaxis="y2"))
        fig.update_layout(height=350, title="Temperature and humidity", yaxis_title="°C", yaxis2=dict(title="Humidity %", overlaying="y", side="right"))
        st.plotly_chart(fig, use_container_width=True)

    corr = view[["cases", "rainfall_mm", "avg_temp_c", "humidity_pct"]].corr()["cases"].drop("cases")
    st.write("Correlation with reported cases (descriptive, not causal):")
    st.dataframe(corr.round(2).rename("Correlation"), use_container_width=True)

with forecast_tab:
    st.subheader("🔮 Three-month disease forecast")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=view.date, y=view.cases, mode="lines", name="Historical cases"))
    fig.add_trace(go.Scatter(x=forecast.date, y=forecast.forecast_cases, mode="lines+markers", name="Forecast"))
    fig.add_trace(go.Scatter(x=forecast.date, y=forecast.upper, mode="lines", line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=forecast.date, y=forecast.lower, mode="lines", fill="tonexty", line=dict(width=0), name="Forecast interval"))
    fig.update_layout(height=470, xaxis_title="Month", yaxis_title="Cases")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(forecast, use_container_width=True, hide_index=True)
    st.caption("Long-range weather is not forecast here. For the 3-month case forecast, weather inputs are represented by historical monthly medians, which avoids pretending that future weather is known.")

with alert_tab:
    st.subheader("🚨 Automated early-warning signals")
    for _, row in alerts.iterrows():
        if row.alert_level == "High":
            st.error(f"**{row.date:%b %Y} — HIGH:** {row.message} Forecast ≈ {row.forecast_cases:,.0f} cases, {row.forecast_vs_baseline_pct:+.1f}% vs seasonal baseline.")
        elif row.alert_level == "Moderate":
            st.warning(f"**{row.date:%b %Y} — MODERATE:** {row.message} Forecast ≈ {row.forecast_cases:,.0f} cases, {row.forecast_vs_baseline_pct:+.1f}% vs seasonal baseline.")
        else:
            st.success(f"**{row.date:%b %Y} — LOW:** {row.message}")
    st.dataframe(alerts, use_container_width=True, hide_index=True)
    st.caption("Alert thresholds are transparent analytics rules, not official outbreak thresholds. They should be reviewed with public-health surveillance data before operational use.")

with validation_tab:
    st.subheader("🧪 Time-aware model validation")
    m1, m2, m3 = st.columns(3)
    m1.metric("Holdout MAE", f"{metrics.get('holdout_mae', 0):,.1f}")
    m2.metric("Holdout RMSE", f"{metrics.get('holdout_rmse', 0):,.1f}")
    m3.metric("Holdout MAPE", f"{metrics.get('holdout_mape_percent', 0):.1f}%")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=validation.date, y=validation.actual, mode="lines+markers", name="Actual"))
    fig.add_trace(go.Scatter(x=validation.date, y=validation.forecast, mode="lines+markers", name="Forecast"))
    fig.update_layout(height=420, title="Last 12 months: unseen holdout", xaxis_title="Month", yaxis_title="Cases")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Why this validation is better")
    st.write("The model is trained on earlier months and evaluated on later months. TimeSeriesSplit also uses expanding training windows. There is no random shuffle, so future observations do not leak into the past.")
    st.dataframe(pd.DataFrame(metrics.get("time_series_cv", [])), use_container_width=True, hide_index=True)

with data_tab:
    st.subheader("📁 Real-data provenance")
    st.json(meta)
    st.dataframe(history.tail(100), use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download real merged dataset", history.to_csv(index=False), "real_dengue_weather.csv", "text/csv")
    st.download_button("⬇️ Download forecast", forecast.to_csv(index=False), "forecast_next.csv", "text/csv")

st.markdown("---")
st.caption("Sources: OpenDengue disease surveillance database; Open-Meteo Historical Weather API. See README for citations and limitations.")
