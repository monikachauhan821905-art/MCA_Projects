"""
train_models.py
----------------
Modules 2, 3 and 5 of the project:
  - Data Cleaning
  - Exploratory Data Analysis (quick console summary)
  - Outbreak Prediction Model (Random Forest, XGBoost, Logistic Regression)
  - Time Series Forecasting (simple moving-average based monthly forecast)

Run:
    python models/train_models.py

Outputs (saved into models/):
    risk_classifier_rf.joblib
    risk_classifier_xgb.joblib
    risk_classifier_logreg.joblib
    label_encoders.joblib
    metrics.json
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from xgboost import XGBClassifier

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "..", "data", "disease_weather_data.csv")


# ---------------------------------------------------------------------------
# 1. DATA CLEANING (Module 2)
# ---------------------------------------------------------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # Drop exact duplicate rows
    df = df.drop_duplicates()

    # Fill missing rainfall with the seasonal median for that month
    df["rainfall_mm"] = df.groupby("month")["rainfall_mm"].transform(
        lambda s: s.fillna(s.median())
    )

    # Drop any row still missing a critical value
    df = df.dropna(subset=["cases", "risk_level", "avg_temp_c", "humidity_pct"])

    after = len(df)
    print(f"[Data Cleaning] {before} rows -> {after} rows "
          f"({before - after} duplicates/missing removed)")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. QUICK EDA (Module 3) — printed summary, not full notebook-style EDA
# ---------------------------------------------------------------------------
def quick_eda(df: pd.DataFrame):
    print("\n[EDA] Average cases by disease:")
    print(df.groupby("disease")["cases"].mean().round(1).sort_values(ascending=False))

    print("\n[EDA] Risk level distribution:")
    print(df["risk_level"].value_counts())

    print("\n[EDA] Correlation of rainfall/temperature/humidity with cases:")
    print(df[["rainfall_mm", "avg_temp_c", "humidity_pct", "cases"]].corr()["cases"].round(2))


# ---------------------------------------------------------------------------
# 3. OUTBREAK PREDICTION MODELS (Module 5)
# ---------------------------------------------------------------------------
def train_classifiers(df: pd.DataFrame):
    feature_cols = ["month", "rainfall_mm", "avg_temp_c", "humidity_pct"]

    le_disease = LabelEncoder()
    le_state = LabelEncoder()
    le_risk = LabelEncoder()

    X = df[feature_cols].copy()
    X["disease_enc"] = le_disease.fit_transform(df["disease"])
    X["state_enc"] = le_state.fit_transform(df["state"])
    y = le_risk.fit_transform(df["risk_level"])

    # Time-aware-ish split: shuffle but stratify by risk level so all
    # classes are represented in both train and test sets.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    models = {
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=10, random_state=42
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1,
            eval_metric="mlogloss", random_state=42
        ),
        "Logistic Regression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000)
        ),
    }

    metrics = {}
    trained = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        metrics[name] = {
            "accuracy": round(accuracy_score(y_test, preds), 3),
            "precision": round(precision_score(y_test, preds, average="macro", zero_division=0), 3),
            "recall": round(recall_score(y_test, preds, average="macro", zero_division=0), 3),
            "f1": round(f1_score(y_test, preds, average="macro", zero_division=0), 3),
        }
        trained[name] = model
        print(f"\n[{name}] " + ", ".join(f"{k}={v}" for k, v in metrics[name].items()))

    joblib.dump(trained["Random Forest"], os.path.join(HERE, "risk_classifier_rf.joblib"))
    joblib.dump(trained["XGBoost"], os.path.join(HERE, "risk_classifier_xgb.joblib"))
    joblib.dump(trained["Logistic Regression"], os.path.join(HERE, "risk_classifier_logreg.joblib"))
    joblib.dump(
        {"disease": le_disease, "state": le_state, "risk": le_risk},
        os.path.join(HERE, "label_encoders.joblib"),
    )

    return metrics


# ---------------------------------------------------------------------------
# 4. TIME SERIES FORECAST (Module 5 — monthly case forecasting)
#    Simple, dependency-light approach: weighted moving average of the same
    # month across previous years + short-term trend. Swappable later for
#    ARIMA/Prophet once multi-year real data is available.
# ---------------------------------------------------------------------------
def forecast_next_month(df: pd.DataFrame, state: str, disease: str) -> dict:
    subset = df[(df["state"] == state) & (df["disease"] == disease)]
    monthly_totals = subset.groupby("month")["cases"].sum().reindex(range(1, 13), fill_value=0)

    current_month = monthly_totals.idxmax()  # placeholder "current" = seasonal peak so far
    # Simple exponential smoothing forecast for the next month
    alpha = 0.5
    smoothed = monthly_totals.iloc[0]
    for v in monthly_totals.iloc[1:]:
        smoothed = alpha * v + (1 - alpha) * smoothed

    next_month_forecast = round(smoothed, 0)
    return {
        "state": state,
        "disease": disease,
        "monthly_totals": monthly_totals.to_dict(),
        "next_month_forecast": next_month_forecast,
    }


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Loading data from {DATA_PATH} ...")
    raw = pd.read_csv(DATA_PATH)

    clean = clean_data(raw)
    quick_eda(clean)

    print("\n=== Training classification models ===")
    metrics = train_classifiers(clean)

    print("\n=== Example time-series forecast (Punjab, Dengue) ===")
    forecast = forecast_next_month(clean, "Punjab", "Dengue")
    print(f"Next month forecast: {forecast['next_month_forecast']} cases")

    with open(os.path.join(HERE, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved metrics.json and model files in {HERE}")
