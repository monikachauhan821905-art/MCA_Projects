# 🎓 Project Demo & Viva Guide

## 1. Problem statement

Disease outbreaks are influenced by seasonal and environmental patterns. The project analyzes real dengue surveillance data together with historical weather data and builds a forecasting-based early-warning prototype.

## 2. Data

### Disease
OpenDengue provides publicly available dengue case counts collected from multiple public sources. The dataset contains location, start/end dates, case counts and case-definition metadata.

### Weather
Open-Meteo historical weather provides temperature, precipitation and humidity variables for the same time period.

## 3. Integration

Disease records are converted to monthly case totals. Weather observations are aggregated to monthly averages/totals and joined by month.

## 4. Forecasting

The project uses seasonal SARIMAX with a 12-month seasonal period. The model captures trend, autocorrelation and yearly seasonality.

## 5. Validation

The last 12 months are held out as an unseen test period. Additional `TimeSeriesSplit` folds use earlier data to predict later data. No random shuffle is used.

## 6. Prediction graphs

The dashboard displays:

- Historical disease trend
- 3-month forecast
- Forecast interval
- Holdout actual vs predicted cases
- Rainfall, temperature and humidity trends
- Weather/case correlations

## 7. Automated alerts

The alert engine compares each forecast with the historical median for that same calendar month and assigns Low, Moderate or High analytics status.

## 8. Viva questions

### Why did you replace the synthetic dataset?
To make the project more realistic and demonstrate an actual data-engineering and forecasting workflow using publicly available surveillance data.

### Why not use a random train-test split?
Because time-series data are ordered. A random split can allow future observations to influence training. Chronological validation better represents real forecasting.

### What is SARIMAX?
SARIMAX is Seasonal ARIMA with eXogenous variables. It models temporal dependence and seasonality while allowing external variables such as weather to be included.

### Why seasonality = 12?
The disease data are aggregated monthly, so 12 months represent one yearly seasonal cycle.

### What is MAE?
Mean Absolute Error. It gives the average absolute difference between actual and forecasted cases.

### What is RMSE?
Root Mean Squared Error. It penalizes larger errors more strongly than MAE.

### What is MAPE?
Mean Absolute Percentage Error. It expresses forecast error as a percentage, although it can become unstable when actual case counts are close to zero.

### Why are there confidence intervals?
A point forecast alone hides uncertainty. The interval shows a range of plausible future values under the fitted statistical model.

### Does high alert mean an outbreak is confirmed?
No. It is only a transparent analytics signal based on the project's threshold rules. Official outbreak declarations require validated surveillance and public-health assessment.
