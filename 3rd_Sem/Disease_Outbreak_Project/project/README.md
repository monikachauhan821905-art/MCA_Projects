# Disease Outbreak Prediction & Healthcare Analytics

A working prototype implementation of the project — SDG 3 (Good Health and Well-Being).

## What's included

```
project/
├── data/
│   └── generate_dataset.py     # Module 1: Data Collection (synthetic sample data for now)
├── models/
│   └── train_models.py         # Modules 2, 3, 5: Cleaning, EDA, Prediction Models
└── app/
    └── dashboard.py             # Module 6: Interactive Streamlit dashboard
```

## Setup

```bash
pip install -r requirements.txt
```

## Run it — 3 steps

```bash
# 1. Generate the sample dataset (Module 1)
python data/generate_dataset.py

# 2. Clean the data, run EDA, and train the ML models (Modules 2, 3, 5)
python models/train_models.py

# 3. Launch the interactive dashboard (Module 6)
streamlit run app/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`.

## What each script does

- **`data/generate_dataset.py`** — Creates `disease_weather_data.csv`: monthly, district-wise
  case counts for 5 diseases across 10 states, combined with weather data (rainfall,
  temperature, humidity). Built with realistic seasonal patterns so the pipeline can be
  developed before real WHO/Kaggle/Data.gov.in datasets are fully integrated.

- **`models/train_models.py`** — Cleans the data (missing values, duplicates), prints a
  quick EDA summary, then trains and saves three classifiers (Random Forest, XGBoost,
  Logistic Regression) to predict Low/Medium/High outbreak risk, plus a simple time-series
  forecast function for next month's case count. Saves trained models to `models/*.joblib`
  and metrics to `models/metrics.json`.

- **`app/dashboard.py`** — The District/State Dashboard. Lets you filter by disease and
  state, view KPIs, a case trend chart, a risk-distribution chart, a district risk table,
  and run a **live prediction** using the trained models.

## Swapping in real data later

Replace the CSV produced by `generate_dataset.py` with real data from:
- WHO: https://www.who.int/data/gho
- Kaggle: https://www.kaggle.com/datasets/siddhvr/dengue-prediction
- Data.gov.in / IDSP: https://idsp.mohfw.gov.in/
- Weather: https://power.larc.nasa.gov/ or https://open-meteo.com/

As long as the new CSV has the same column names (`state, district, month, disease,
rainfall_mm, avg_temp_c, humidity_pct, cases, risk_level`), the rest of the pipeline
(cleaning → training → dashboard) works without any changes.

---
Monika Chauhan (UID: 25MCI10067) · Amisha Chauhan (UID: 25MCI10077)
