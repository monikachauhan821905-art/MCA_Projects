"""Train and validate the forecasting component using time-aware splits.

Run:
    python models/train_forecasting.py

Outputs:
    models/forecast_model.joblib
    models/forecast_metrics.json
    models/forecast_validation.csv
    models/forecast_next.csv
"""

import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from statsmodels.tsa.statespace.sarimax import SARIMAX

HERE = Path(__file__).resolve().parent
DATA = HERE / "../data/real_dengue_weather.csv"


def load_data():
    df = pd.read_csv(DATA, parse_dates=["date"]).sort_values("date")
    df = df.drop_duplicates("date").set_index("date").asfreq("MS")
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce").interpolate(limit_direction="both")
    for c in ["rainfall_mm", "avg_temp_c", "humidity_pct"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").interpolate(limit_direction="both")
    return df


def fit_forecast(train, steps, future_weather):
    # Seasonal monthly SARIMAX. Exogenous weather is used for historical model
    # diagnostics; future weather uses the seasonal median to avoid inventing
    # a long-range weather forecast.
    exog_cols = ["rainfall_mm", "avg_temp_c", "humidity_pct"]
    model = SARIMAX(
        train["cases"],
        exog=train[exog_cols],
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fitted = model.fit(disp=False)
    fc = fitted.get_forecast(steps=steps, exog=future_weather[exog_cols])
    return fitted, fc.predicted_mean.clip(lower=0), fc.conf_int().clip(lower=0)


def seasonal_weather(df, dates):
    climatology = df.groupby(df.index.month)[["rainfall_mm", "avg_temp_c", "humidity_pct"]].median()
    out = climatology.loc[[d.month for d in dates]].copy()
    out.index = dates
    return out


def evaluate(df):
    # Final 12 months are never used for model selection/training.
    if len(df) < 48:
        raise RuntimeError("At least 48 monthly observations are recommended for seasonal forecasting.")

    split = len(df) - 12
    train = df.iloc[:split].copy()
    test = df.iloc[split:].copy()

    _, pred, ci = fit_forecast(train, len(test), test[["rainfall_mm", "avg_temp_c", "humidity_pct"]])
    mae = mean_absolute_error(test["cases"], pred)
    rmse = mean_squared_error(test["cases"], pred) ** 0.5
    denom = np.maximum(test["cases"].values, 1)
    mape = np.mean(np.abs((test["cases"].values - pred.values) / denom)) * 100

    validation = pd.DataFrame({
        "date": test.index,
        "actual": test["cases"].values,
        "forecast": pred.values,
        "lower": ci.iloc[:, 0].values,
        "upper": ci.iloc[:, 1].values,
    })

    # TimeSeriesSplit gives expanding training windows and later test windows;
    # no shuffling or future leakage.
    n_splits = min(4, max(2, len(train) // 12 - 1))
    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=6)
    fold_rows = []
    X = train[["cases", "rainfall_mm", "avg_temp_c", "humidity_pct"]]
    for fold, (tr_idx, va_idx) in enumerate(tscv.split(X), start=1):
        tr = train.iloc[tr_idx]
        va = train.iloc[va_idx]
        try:
            _, p, _ = fit_forecast(tr, len(va), va[["rainfall_mm", "avg_temp_c", "humidity_pct"]])
            fold_rows.append({
                "fold": fold,
                "train_end": str(tr.index.max().date()),
                "validation_start": str(va.index.min().date()),
                "validation_end": str(va.index.max().date()),
                "mae": float(mean_absolute_error(va["cases"], p)),
                "rmse": float(mean_squared_error(va["cases"], p) ** 0.5),
            })
        except Exception as exc:
            fold_rows.append({"fold": fold, "error": str(exc)})

    return validation, fold_rows, {
        "holdout_months": 12,
        "holdout_mae": round(float(mae), 2),
        "holdout_rmse": round(float(rmse), 2),
        "holdout_mape_percent": round(float(mape), 2),
        "time_series_cv": fold_rows,
    }


def main():
    df = load_data()
    validation, folds, metrics = evaluate(df)

    future_dates = pd.date_range(df.index.max() + pd.offsets.MonthBegin(1), periods=3, freq="MS")
    future_weather = seasonal_weather(df, future_dates)
    model, pred, ci = fit_forecast(df, 3, future_weather)

    forecast = pd.DataFrame({
        "date": future_dates,
        "forecast_cases": np.round(pred.values, 0),
        "lower": np.round(ci.iloc[:, 0].values, 0),
        "upper": np.round(ci.iloc[:, 1].values, 0),
        "rainfall_mm_assumption": np.round(future_weather["rainfall_mm"].values, 1),
        "temperature_assumption": np.round(future_weather["avg_temp_c"].values, 1),
        "humidity_assumption": np.round(future_weather["humidity_pct"].values, 1),
    })

    # Save model + metadata.
    joblib.dump({"model": model, "weather_columns": ["rainfall_mm", "avg_temp_c", "humidity_pct"]}, HERE / "forecast_model.joblib")
    validation.to_csv(HERE / "forecast_validation.csv", index=False)
    forecast.to_csv(HERE / "forecast_next.csv", index=False)
    (HERE / "forecast_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\n=== Time-aware forecasting ===")
    print(json.dumps({k: v for k, v in metrics.items() if k != "time_series_cv"}, indent=2))
    print("\n3-month forecast:")
    print(forecast.to_string(index=False))


if __name__ == "__main__":
    main()
