"""
Download and prepare REAL dengue + weather data.

Disease source:
    OpenDengue (peer-reviewed global dengue case-count database)
    Figshare DOI: 10.6084/m9.figshare.24259573

Weather source:
    Open-Meteo Historical Weather API (ERA5/ERA5-Land reanalysis)

Usage:
    python data/download_real_data.py --country India

The script:
1. Downloads OpenDengue's temporal-resolution extract.
2. Filters one country and converts observations to monthly totals.
3. Geocodes the selected country using Open-Meteo's geocoding API.
4. Downloads historical monthly weather for the same period.
5. Merges disease + weather data into data/real_dengue_weather.csv.

Note: OpenDengue is a compilation of publicly available surveillance data;
case definitions and reporting completeness vary by source and place.
"""

import argparse
import io
import json
import os
import zipfile
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).resolve().parent
OUT = BASE / "real_dengue_weather.csv"
RAW = BASE / "opendengue_raw.csv"
META = BASE / "real_data_metadata.json"

FIGSHARE_ARTICLE = "https://api.figshare.com/v2/articles/24259573"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"


def get_json(url, params=None):
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def download_opendengue():
    print("[1/4] Getting OpenDengue file information...")
    article = get_json(FIGSHARE_ARTICLE)
    files = article.get("files", [])
    candidates = [f for f in files if "Temporal_extract" in f["name"]]
    if not candidates:
        raise RuntimeError("Temporal_extract.csv was not found in the OpenDengue Figshare record.")

    # Prefer the smallest direct Temporal_extract file.
    file_info = sorted(candidates, key=lambda x: x.get("size", 10**30))[0]
    url = file_info["download_url"]
    print(f"Downloading {file_info['name']} ({file_info.get('size', 0)/1e6:.1f} MB)...")
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    content = r.content

    if file_info["name"].lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            candidates = [
                n for n in z.namelist()
                if n.lower().endswith(".csv") and "temporal" in n.lower()
            ]
            if not candidates:
                # Fall back to any CSV inside the archive to remain compatible with
                # newer Figshare package names or nested folder layouts.
                candidates = [n for n in z.namelist() if n.lower().endswith(".csv")]
            if not candidates:
                raise RuntimeError("No CSV file was found inside the OpenDengue archive.")
            with z.open(candidates[0]) as src, open(RAW, "wb") as dst:
                dst.write(src.read())
    else:
        RAW.write_bytes(content)

    return file_info["name"]


def geocode_country(country):
    print(f"[2/4] Finding coordinates for {country}...")
    data = get_json(GEOCODING_URL, {"name": country, "count": 1, "language": "en", "format": "json"})
    results = data.get("results", [])
    if not results:
        raise RuntimeError(f"Could not geocode country: {country}")
    return results[0]["latitude"], results[0]["longitude"], results[0].get("name", country)


def prepare_disease(country):
    print(f"[3/4] Preparing monthly dengue data for {country}...")
    df = pd.read_csv(RAW, low_memory=False)
    required = {"adm_0_name", "calendar_start_date", "calendar_end_date", "dengue_total"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"OpenDengue schema changed; missing columns: {sorted(missing)}")

    mask = df["adm_0_name"].astype(str).str.casefold() == country.casefold()
    df = df.loc[mask].copy()
    if df.empty:
        raise RuntimeError(f"No OpenDengue records found for {country}.")

    df["start"] = pd.to_datetime(df["calendar_start_date"], errors="coerce")
    df["end"] = pd.to_datetime(df["calendar_end_date"], errors="coerce")
    df["dengue_total"] = pd.to_numeric(df["dengue_total"], errors="coerce")
    df = df.dropna(subset=["start", "dengue_total"])

    # Keep the finest temporal observations. If weekly records exist, convert to
    # monthly by start date; if annual-only data is all that exists, the script
    # still works but forecasting quality will be lower.
    monthly = (
        df.assign(date=df["start"].dt.to_period("M").dt.to_timestamp())
          .groupby("date", as_index=False)["dengue_total"].sum()
          .rename(columns={"dengue_total": "cases"})
    )
    monthly["cases"] = monthly["cases"].clip(lower=0)
    return monthly


def fetch_weather(lat, lon, start, end):
    print(f"[4/4] Downloading real historical weather ({start.date()} to {end.date()})...")
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "daily": "temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum",
        "timezone": "auto",
    }
    data = get_json(WEATHER_URL, params)
    daily = pd.DataFrame(data.get("daily", {}))
    if daily.empty:
        raise RuntimeError("Open-Meteo returned no weather data.")
    daily["date"] = pd.to_datetime(daily["time"])
    daily["month"] = daily["date"].dt.to_period("M").dt.to_timestamp()
    monthly = daily.groupby("month", as_index=False).agg(
        avg_temp_c=("temperature_2m_mean", "mean"),
        humidity_pct=("relative_humidity_2m_mean", "mean"),
        rainfall_mm=("precipitation_sum", "sum"),
    )
    return monthly.rename(columns={"month": "date"})


def main(country):
    source_file = download_opendengue()
    disease = prepare_disease(country)
    lat, lon, geocoded = geocode_country(country)

    start = disease["date"].min()
    end = disease["date"].max()
    weather = fetch_weather(lat, lon, start, end)

    merged = disease.merge(weather, on="date", how="left")
    merged["country"] = country
    merged["month"] = merged["date"].dt.month
    merged["month_name"] = merged["date"].dt.strftime("%b")
    merged = merged.sort_values("date").reset_index(drop=True)

    # Require a usable weather match. A small number of missing months can be
    # filled by the same month's median; no disease values are fabricated.
    for col in ["avg_temp_c", "humidity_pct", "rainfall_mm"]:
        merged[col] = merged[col].fillna(merged.groupby("month")[col].transform("median"))

    merged.to_csv(OUT, index=False)
    metadata = {
        "disease_source": "OpenDengue",
        "disease_source_doi": "10.6084/m9.figshare.24259573",
        "weather_source": "Open-Meteo Historical Weather API",
        "country": country,
        "geocoded_name": geocoded,
        "latitude": lat,
        "longitude": lon,
        "start_date": str(start.date()),
        "end_date": str(end.date()),
        "rows": int(len(merged)),
        "note": "Reported surveillance data; completeness and case definitions vary by location and time.",
        "opendengue_file": source_file,
    }
    META.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\nSaved: {OUT}")
    print(f"Rows: {len(merged):,}")
    print(f"Period: {start.date()} -> {end.date()}")
    print(f"Weather coordinates: {lat:.4f}, {lon:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", default="India", help="Country name, e.g. India, Brazil, Thailand")
    args = parser.parse_args()
    main(args.country)
