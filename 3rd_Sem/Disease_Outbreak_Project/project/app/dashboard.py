"""
dashboard.py
------------
Module 6: District/State-wise Dashboard (Streamlit).

Run with:
    streamlit run app/dashboard.py

Loads the cleaned dataset + trained models (from models/train_models.py)
and lets the user explore outbreak risk by disease, state and district,
and generate a simple downloadable report (Module 7).
"""

import os
import sys
from datetime import datetime
from io import BytesIO

import joblib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "..", "data", "disease_weather_data.csv")
MODELS_DIR = os.path.join(HERE, "..", "models")

st.set_page_config(
    page_title="Disease Outbreak Prediction & Healthcare Analytics",
    page_icon="🩺",
    layout="wide",
)

st.markdown(
    """
    <style>
    html, body {
        background: #061722 !important;
        color: #edf4ff !important;
    }
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .stApp {
        background: #061722 !important;
        color: #edf4ff !important;
    }
    .stApp * {
        color: #edf4ff !important;
    }
    .stSidebar {
        background: #0b1d2a !important;
    }
    .stMarkdown, .stTitle, .stHeader, .stSubheader, .stCaption, .stMetricLabel, .stMetricValue,
    h1, h2, h3, h4, h5, p, span, div, label, li, td, th {
        color: #edf4ff !important;
    }
    .stDataFrame, .stTable {
        background: #0d1d2a !important;
        color: #edf4ff !important;
        border: 1px solid rgba(148, 163, 184, 0.4) !important;
    }
    table, th, td {
        background: #0d1d2a !important;
        color: #edf4ff !important;
    }
    thead th {
        background: #152b3b !important;
        color: #f8fbff !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricContainer"] {
        background: #0d1d2a !important;
        border: 1px solid rgba(148, 163, 184, 0.4) !important;
        border-radius: 10px !important;
        padding: 0.8rem !important;
    }
    .stDownloadButton > button, div.stButton > button {
        background: #1d9bf0 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button:hover, div.stButton > button:hover {
        background: #1677c9 !important;
        color: white !important;
    }
    .stDataFrame .stDataFrameContainer, .stDataFrameContainer * {
        background: #0d1d2a !important;
        color: #edf4ff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load data & models (cached so the app stays fast)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.drop_duplicates()
    df["rainfall_mm"] = df.groupby("month")["rainfall_mm"].transform(
        lambda s: s.fillna(s.median())
    )
    return df.dropna(subset=["cases", "risk_level"])


@st.cache_resource
def load_models():
    rf = joblib.load(os.path.join(MODELS_DIR, "risk_classifier_rf.joblib"))
    xgb = joblib.load(os.path.join(MODELS_DIR, "risk_classifier_xgb.joblib"))
    encoders = joblib.load(os.path.join(MODELS_DIR, "label_encoders.joblib"))
    return rf, xgb, encoders


def create_pdf_report(filtered, current_data, disease, state, current_month):
    report_buffer = BytesIO()
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    with PdfPages(report_buffer) as pdf:
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.text(0.08, 0.88, "Disease outbreak analytics report", fontsize=22, weight="bold")
        fig.text(0.08, 0.83, f"Scope: {disease} | {state}", fontsize=12)
        fig.text(0.08, 0.79, f"Latest period: {month_names[int(current_month) - 1]}", fontsize=12)
        fig.text(0.08, 0.74, f"Generated: {datetime.now():%Y-%m-%d %H:%M}", fontsize=10, color="#555555")

        total_cases = int(current_data["cases"].sum())
        high_risk = int((current_data["risk_level"] == "High").sum())
        metrics = (
            f"Reported cases: {total_cases:,}\n"
            f"High-risk districts: {high_risk}\n"
            f"Districts included: {current_data['district'].nunique()}"
        )
        fig.text(0.08, 0.58, metrics, fontsize=16, linespacing=1.8)
        fig.text(
            0.08, 0.28,
            "This report summarizes the selected dashboard view. Data may be synthetic;\n"
            "risk classifications are analytical model outputs, not clinical guidance.",
            fontsize=10, color="#555555",
        )
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        trend = filtered.groupby("month")["cases"].sum().reindex(range(1, 13), fill_value=0)
        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        ax.plot(month_names, trend.values, marker="o", color="#028090")
        ax.set_title("Monthly reported cases")
        ax.set_ylabel("Cases")
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        top_districts = current_data.sort_values("cases", ascending=False).head(12)
        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        colors = top_districts["risk_level"].map(
            {"Low": "#04B389", "Medium": "#E8A23D", "High": "#E0524B"}
        )
        ax.barh(top_districts["district"].astype(str), top_districts["cases"], color=colors)
        ax.invert_yaxis()
        ax.set_title("Highest-case districts in the selected period")
        ax.set_xlabel("Reported cases")
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

    return report_buffer.getvalue()


try:
    df = load_data()
    rf_model, xgb_model, encoders = load_models()
    models_ready = True
except FileNotFoundError:
    models_ready = False
    df = pd.read_csv(DATA_PATH) if os.path.exists(DATA_PATH) else pd.DataFrame()

# ---------------------------------------------------------------------------
# Sidebar — filters (Module 6 controls)
# ---------------------------------------------------------------------------
st.sidebar.title("🩺 Outbreak Analytics")
st.sidebar.caption("Disease Outbreak Prediction & Healthcare Analytics")

if df.empty:
    st.sidebar.error("No data found. Run data/generate_dataset.py first.")
    st.stop()

diseases = sorted(df["disease"].unique())
states = ["All States"] + sorted(df["state"].unique())

disease = st.sidebar.selectbox("Disease", diseases)
state = st.sidebar.selectbox("State", states)

filtered = df[df["disease"] == disease]
if state != "All States":
    filtered = filtered[filtered["state"] == state]

st.sidebar.markdown("---")
st.sidebar.markdown("**Data sources:** WHO · Kaggle · Data.gov.in · Weather API")
st.sidebar.markdown("**Models:** Random Forest · XGBoost · Logistic Regression · Time Series")

if not models_ready:
    st.sidebar.warning("Model files not found — run `python models/train_models.py` first "
                        "to enable live risk prediction.")

# ---------------------------------------------------------------------------
# Main — title & KPIs
# ---------------------------------------------------------------------------
st.title("District/State Outbreak Dashboard")
st.caption(f"Showing **{disease}** · **{state}**")

current_month = filtered["month"].max()
current_data = filtered[filtered["month"] == current_month]
prev_month_data = filtered[filtered["month"] == max(current_month - 1, 1)]

total_current = int(current_data["cases"].sum())
total_prev = int(prev_month_data["cases"].sum()) or 1
pct_change = round(((total_current - total_prev) / total_prev) * 100, 1)
high_risk_count = int((current_data["risk_level"] == "High").sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Reported cases (latest month)", f"{total_current:,}")
col2.metric("Change vs previous month", f"{pct_change:+.1f}%")
col3.metric("High-risk districts", high_risk_count)
col4.metric("Districts shown", current_data["district"].nunique())

st.subheader("Download report")
st.caption("Exports the current disease, state, and latest-month selection.")
report_col1, report_col2 = st.columns(2)
report_name = f"outbreak_report_{disease.lower()}_{state.lower().replace(' ', '-')}.pdf"
report_col1.download_button(
    "Download PDF report",
    data=create_pdf_report(filtered, current_data, disease, state, current_month),
    file_name=report_name,
    mime="application/pdf",
    type="primary",
)
report_col2.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name=f"outbreak_data_{disease.lower()}_{state.lower().replace(' ', '-')}.csv",
    mime="text/csv",
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Trend chart + risk distribution
# ---------------------------------------------------------------------------
left, right = st.columns([1.6, 1])

with left:
    st.subheader("Monthly case trend")
    trend = filtered.groupby("month")["cases"].sum().reset_index()
    trend["month_name"] = trend["month"].apply(
        lambda m: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][m-1]
    )
    fig = px.line(trend, x="month_name", y="cases", markers=True,
                  labels={"month_name": "Month", "cases": "Cases"})
    fig.update_traces(line_color="#028090")
    st.plotly_chart(fig)

with right:
    st.subheader("Risk distribution")
    risk_counts = current_data["risk_level"].value_counts().reindex(
        ["Low", "Medium", "High"], fill_value=0
    ).reset_index()
    risk_counts.columns = ["risk_level", "count"]
    fig2 = px.pie(risk_counts, names="risk_level", values="count", hole=0.5,
                  color="risk_level",
                  color_discrete_map={"Low": "#04B389", "Medium": "#E8A23D", "High": "#E0524B"})
    st.plotly_chart(fig2)

# ---------------------------------------------------------------------------
# District risk heatmap
# ---------------------------------------------------------------------------
st.subheader("District risk heatmap")
st.caption("Each cell shows the latest-month risk level. Darker colors indicate higher risk; the case count is shown inside each cell.")
heat = current_data[["state", "district", "cases", "risk_level"]].sort_values(
    "cases", ascending=False
)
heat["risk_score"] = heat["risk_level"].map({"Low": 1, "Medium": 2, "High": 3})
heat["district_label"] = heat["state"] + " - " + heat["district"]
heatmap = go.Figure(
    go.Heatmap(
        x=[f"Month {int(current_month)}"],
        y=heat["district_label"],
        z=heat[["risk_score"]].values,
        text=[[f"{risk} risk<br>{int(cases):,} cases"] for risk, cases in zip(heat["risk_level"], heat["cases"])],
        texttemplate="%{text}",
        textfont={"size": 13},
        customdata=heat[["risk_level", "cases"]].values,
        hovertemplate="<b>%{y}</b><br>Risk: %{customdata[0]}<br>Cases: %{customdata[1]:,}<extra></extra>",
        zmin=1,
        zmax=3,
        colorscale=[[0, "#04B389"], [0.5, "#E8A23D"], [1, "#E0524B"]],
        showscale=False,
    )
)
heatmap.update_layout(height=max(260, min(620, 70 + len(heat) * 34)), margin={"l": 10, "r": 10, "t": 10, "b": 10}, xaxis_title="Selected period", yaxis_title="District")
st.plotly_chart(heatmap)
st.markdown(":green[Low] = lower observed risk &nbsp;&nbsp; :orange[Medium] = moderate observed risk &nbsp;&nbsp; :red[High] = higher observed risk")
st.caption("Detailed view: sort the table by cases or risk level to compare districts.")


st.dataframe(heat[["state", "district", "cases", "risk_level"]], height=320)

# ---------------------------------------------------------------------------
# Live prediction using the trained models (Module 5 in action)
# ---------------------------------------------------------------------------
st.subheader("Run a live risk prediction")
st.caption("Uses the trained Random Forest & XGBoost models from models/train_models.py")

pc1, pc2, pc3, pc4 = st.columns(4)
in_month = pc1.slider("Month", 1, 12, int(current_month))
in_rain = pc2.number_input("Rainfall (mm)", 0.0, 400.0, 120.0)
in_temp = pc3.number_input("Avg temperature (°C)", 10.0, 45.0, 28.0)
in_humidity = pc4.number_input("Humidity (%)", 10.0, 100.0, 55.0)

if st.button("Predict outbreak risk", type="primary"):
    if not models_ready:
        st.error("Train the models first: `python models/train_models.py`")
    else:
        disease_enc = encoders["disease"].transform([disease])[0]
        state_enc = encoders["state"].transform(
            [state if state != "All States" else df["state"].iloc[0]]
        )[0]
        X_new = pd.DataFrame([{
            "month": in_month, "rainfall_mm": in_rain, "avg_temp_c": in_temp,
            "humidity_pct": in_humidity, "disease_enc": disease_enc, "state_enc": state_enc,
        }])
        rf_pred = encoders["risk"].inverse_transform(rf_model.predict(X_new))[0]
        xgb_pred = encoders["risk"].inverse_transform(xgb_model.predict(X_new))[0]

        r1, r2 = st.columns(2)
        r1.success(f"**Random Forest prediction:** {rf_pred} risk")
        r2.success(f"**XGBoost prediction:** {xgb_pred} risk")


