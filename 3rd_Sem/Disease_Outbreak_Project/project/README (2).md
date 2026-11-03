# 🩺 OutbreakIQ — Disease Outbreak Prediction & Forecasting

An upgraded MCA AI/ML healthcare analytics project that combines **real dengue surveillance data**, **real historical weather data**, **time-aware machine learning/statistical validation**, **3-month forecasting**, interactive prediction graphs, and transparent automated early-warning signals.

## 🌟 What changed from the original project?

| Original | Upgraded |
|---|---|
| Synthetic disease data | **Real OpenDengue surveillance data** |
| Synthetic rainfall/temp/humidity | **Open-Meteo historical weather data** |
| Random train/test split | **Time-based holdout + TimeSeriesSplit** |
| Moving-average forecast | **Seasonal SARIMAX forecasting** |
| Basic dashboard | **Forecast + validation + alerts dashboard** |
| No uncertainty | **Forecast confidence intervals** |
| Manual interpretation | **Automated transparent alert rules** |

## 📚 Data sources

### Disease data — OpenDengue
OpenDengue is a global database of publicly available dengue case counts assembled from ministry of health websites, peer-reviewed publications and other disease databases. The peer-reviewed Scientific Data paper describes version 1.2 as containing more than 56 million dengue cases from 102 countries between 1924 and 2023, with most records at weekly or monthly resolution.

- Dataset DOI: `10.6084/m9.figshare.24259573`
- Project: https://opendengue.org/
- Paper DOI: `10.1038/s41597-024-03120-7`

### Weather data — Open-Meteo
Historical weather is downloaded from Open-Meteo. Its historical API provides reanalysis-based weather data including temperature, precipitation and humidity. ERA5/ERA5-Land are suitable for consistent historical analysis.

- https://open-meteo.com/en/docs/historical-weather-api

## 🧠 Project pipeline

```text
REAL DENGUE SURVEILLANCE
(OpenDengue)
        │
        ├──────────────┐
        │              │
        ▼              ▼
 Disease cases     REAL WEATHER
 weekly/monthly    Open-Meteo
        │              │
        └──────┬───────┘
               ▼
       Monthly integration
               │
               ▼
        Data cleaning
               │
               ▼
     Exploratory analysis
               │
               ▼
     Time-aware validation
               │
        ┌──────┴────────┐
        ▼               ▼
   Holdout test    TimeSeriesSplit
        │               │
        └──────┬────────┘
               ▼
       Seasonal SARIMAX
               │
               ▼
      3-month forecast
               │
        ┌──────┴────────┐
        ▼               ▼
 Forecast graph    Confidence interval
        │
        ▼
 Automated early-warning rules
        │
        ▼
 Streamlit healthcare dashboard
```

## ▶️ Run the upgraded project

Open the `project` folder in VS Code.

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Download real disease + weather data and train the forecast model

For India:

```bash
python run_pipeline.py --country India
```

You can replace India with another country supported by OpenDengue, for example:

```bash
python run_pipeline.py --country Brazil
```

### 3. Start the dashboard

```bash
streamlit run app/dashboard.py
```

Then open the local Streamlit URL shown in the terminal, normally:

```text
http://localhost:8501
```

## 📁 Important files

```text
project/
├── app/
│   └── dashboard.py                 # Interactive dashboard
├── data/
│   ├── download_real_data.py        # Downloads/merges real data
│   ├── real_dengue_weather.csv      # Created after pipeline runs
│   └── real_data_metadata.json      # Data provenance
├── models/
│   ├── train_forecasting.py         # SARIMAX + time-aware validation
│   ├── alert_engine.py              # Automated warning rules
│   ├── forecast_model.joblib        # Trained forecast model
│   ├── forecast_next.csv            # 3-month forecast
│   ├── forecast_validation.csv      # Holdout predictions
│   └── forecast_metrics.json        # MAE/RMSE/MAPE + CV results
├── run_pipeline.py                  # One-command setup
└── requirements.txt
```

## 🔮 What is “proper forecasting” here?

The project uses a **seasonal SARIMAX** model for monthly cases:

- AR component → uses previous case values.
- I component → differences the series to handle trend/non-stationarity.
- MA component → learns from previous forecast errors.
- Seasonal component → models the 12-month yearly cycle.
- Weather variables → used as historical exogenous signals.

For long-range future months, actual future weather is not known. Therefore the forecast pipeline uses historical monthly weather medians instead of pretending future weather is known.

## 🧪 Why time-based validation?

Randomly mixing January 2024 and January 2026 into both train and test can leak future patterns into training. This project instead keeps chronology intact:

```text
PAST ------------------------------> FUTURE
TRAIN TRAIN TRAIN TRAIN | TEST TEST TEST
                         ↑
                    unseen period
```

The final 12 months are kept as a holdout set, and expanding-window `TimeSeriesSplit` is also used for additional validation.

## 🚨 Automated alerts

Alerts compare forecasted cases with the historical seasonal baseline for the same calendar month:

- **Low:** within the normal historical range.
- **Moderate:** forecast is ≥30% above the seasonal baseline.
- **High:** forecast is ≥75% above the baseline or the upper forecast interval reaches roughly 2× the baseline.

These thresholds are **project analytics rules**, not official public-health thresholds.

## ⚠️ Important limitations

1. OpenDengue is a compilation of reported surveillance data, so under-reporting, missingness and different case definitions can affect comparisons.
2. Open-Meteo historical data are reanalysis/model-based estimates rather than a direct reading from one weather station at every location.
3. A country-level weather coordinate is used for the selected country, so it is not a substitute for district-level meteorological observations.
4. Forecast uncertainty grows with forecast horizon.
5. The alert engine is an academic early-warning demonstration and must not be used as a medical diagnosis or operational outbreak declaration.

## 🎓 One-line viva answer

> “This project integrates real dengue surveillance data with historical weather information, validates forecasting models using chronological splits, forecasts future disease cases with seasonal SARIMAX, and presents the results through an interactive Streamlit early-warning dashboard.”
