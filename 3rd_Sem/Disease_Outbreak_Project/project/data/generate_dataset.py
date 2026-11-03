"""
generate_dataset.py
--------------------
Creates a realistic sample dataset for the Disease Outbreak Prediction project.

In the real project, this data would come from:
  - WHO (https://www.who.int/data/gho)
  - Kaggle disease datasets
  - Data.gov.in / IDSP (Integrated Disease Surveillance Programme)
  - NASA POWER / Open-Meteo (weather data)

For Phase 2, we generate a synthetic but seasonally realistic dataset so the
full pipeline (cleaning -> EDA -> modeling -> dashboard) can be built and
demonstrated end-to-end before real datasets are fully integrated.

Output: data/disease_weather_data.csv
Columns:
  state, district, month (1-12), month_name, disease,
  rainfall_mm, avg_temp_c, humidity_pct, cases, risk_level
"""

import numpy as np
import pandas as pd
import os

np.random.seed(42)

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Seasonal multipliers per disease (index 0 = Jan)
DISEASE_SEASONALITY = {
    "Dengue":      [0.30, 0.25, 0.30, 0.40, 0.60, 1.00, 1.60, 1.90, 1.70, 1.20, 0.60, 0.35],
    "Malaria":     [0.40, 0.35, 0.40, 0.50, 0.70, 1.10, 1.50, 1.70, 1.50, 1.00, 0.60, 0.45],
    "Influenza":   [1.60, 1.40, 1.00, 0.60, 0.40, 0.30, 0.30, 0.35, 0.40, 0.60, 1.00, 1.50],
    "Chikungunya": [0.30, 0.25, 0.30, 0.35, 0.55, 0.95, 1.50, 1.80, 1.60, 1.10, 0.55, 0.30],
}

# Rough rainfall (mm) and temperature (C) seasonal pattern for India (generic)
RAINFALL_SEASON = [15, 20, 25, 30, 60, 180, 260, 240, 160, 60, 20, 10]
TEMP_SEASON = [18, 21, 27, 32, 36, 34, 30, 29, 29, 27, 22, 18]

STATES = {
    "Punjab": ["Amritsar", "Ludhiana", "Jalandhar", "Patiala"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat", "Karnal"],
    "Delhi": ["New Delhi", "North Delhi", "South Delhi", "East Delhi"],
    "Himachal Pradesh": ["Shimla", "Kangra", "Mandi", "Solan"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "Kerala": ["Ernakulam", "Thiruvananthapuram", "Kozhikode", "Kottayam"],
    "West Bengal": ["Kolkata", "Howrah", "Darjeeling", "Malda"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"],
}

STATE_BASE_CASES = {
    "Punjab": 420, "Haryana": 380, "Delhi": 560, "Himachal Pradesh": 260,
    "Rajasthan": 610, "Uttar Pradesh": 1000, "Maharashtra": 900,
    "Kerala": 520, "West Bengal": 700, "Tamil Nadu": 650,
}


def risk_from_cases(cases, peak):
    """Convert a case count into a Low / Medium / High risk label,
    relative to this district+disease's own peak month."""
    ratio = cases / peak
    if ratio >= 0.75:
        return "High"
    elif ratio >= 0.45:
        return "Medium"
    return "Low"


def generate():
    rows = []
    for disease, seasonality in DISEASE_SEASONALITY.items():
        for state, districts in STATES.items():
            base = STATE_BASE_CASES[state]
            for district in districts:
                district_variance = np.random.uniform(0.82, 1.20)
                monthly_cases = []
                monthly_extra = []
                for m_idx, month in enumerate(MONTHS):
                    noise = np.random.uniform(0.90, 1.12)
                    cases = int((base / len(districts)) * seasonality[m_idx]
                                * district_variance * noise)
                    rainfall = round(RAINFALL_SEASON[m_idx] * np.random.uniform(0.85, 1.15), 1)
                    temp = round(TEMP_SEASON[m_idx] * np.random.uniform(0.95, 1.05), 1)
                    humidity = round(45 + rainfall / 6 + np.random.uniform(-5, 5), 1)
                    monthly_cases.append(max(cases, 0))
                    monthly_extra.append((rainfall, temp, humidity))

                # Risk is relative to THIS district+disease's own yearly peak,
                # so each district/disease combination gets a meaningful spread
                # of Low / Medium / High across the year (not all flat "Low").
                peak = max(monthly_cases) if max(monthly_cases) > 0 else 1
                for m_idx, month in enumerate(MONTHS):
                    cases = monthly_cases[m_idx]
                    rainfall, temp, humidity = monthly_extra[m_idx]
                    risk = risk_from_cases(cases, peak)
                    rows.append({
                        "state": state,
                        "district": district,
                        "month": m_idx + 1,
                        "month_name": month,
                        "disease": disease,
                        "rainfall_mm": rainfall,
                        "avg_temp_c": temp,
                        "humidity_pct": humidity,
                        "cases": cases,
                        "risk_level": risk,
                    })

    df = pd.DataFrame(rows)

    # Simulate a few realistic data-quality issues to be cleaned later:
    # (a) a handful of missing rainfall values
    missing_idx = df.sample(frac=0.01, random_state=1).index
    df.loc[missing_idx, "rainfall_mm"] = np.nan
    # (b) a few duplicate rows
    dup_rows = df.sample(frac=0.005, random_state=2)
    df = pd.concat([df, dup_rows], ignore_index=True)

    return df


if __name__ == "__main__":
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    df = generate()
    out_path = os.path.join(os.path.dirname(__file__), "disease_weather_data.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
    print(df.head())
