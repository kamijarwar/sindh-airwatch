import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

CSV = "data_mirpur_khas.csv"

df = pd.read_csv(CSV, parse_dates=["time"])
df = df.set_index("time").sort_index()

# Daily average
daily = df.resample("D").mean(numeric_only=True)

WEATHER_COLS = [
    "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
    "wind_direction_10m", "precipitation", "surface_pressure", "cloud_cover",
]

# Sirf pichle dinon ke features (future leak nahi)
daily["aqi_lag1"] = daily["us_aqi"].shift(1)
daily["aqi_lag2"] = daily["us_aqi"].shift(2)
daily["aqi_lag7"] = daily["us_aqi"].shift(7)
daily["aqi_roll3"] = daily["us_aqi"].shift(1).rolling(3).mean()
daily["aqi_roll7"] = daily["us_aqi"].shift(1).rolling(7).mean()
daily["month"] = daily.index.month

for c in WEATHER_COLS:
    daily[f"{c}_lag1"] = daily[c].shift(1)

# Target: kal ka AQI aaj ke AQI se kitna badlega
daily["next_aqi"] = daily["us_aqi"].shift(-1)
daily["target_change"] = daily["next_aqi"] - daily["us_aqi"]

daily = daily.dropna()

AQI_FEATURES = ["aqi_lag1", "aqi_lag2", "aqi_lag7", "aqi_roll3", "aqi_roll7", "month"]
WEATHER_FEATURES = [f"{c}_lag1" for c in WEATHER_COLS]

# Chronological 80/20 split
split = int(len(daily) * 0.8)
train = daily.iloc[:split]
test = daily.iloc[split:]


def run(features, label):
    model = xgb.XGBRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, random_state=42,
    )
    model.fit(train[features], train["target_change"])
    change_pred = model.predict(test[features])

    final_pred = test["us_aqi"].values + change_pred
    mae = mean_absolute_error(test["next_aqi"], final_pred)
    rmse = np.sqrt(mean_squared_error(test["next_aqi"], final_pred))
    print(f"{label}: MAE={mae:.2f}  RMSE={rmse:.2f}")
    return mae


baseline_mae = mean_absolute_error(test["next_aqi"], test["us_aqi"])
print(f"Baseline (kal = aaj): MAE={baseline_mae:.2f}")

mae_aqi = run(AQI_FEATURES, "Sirf AQI features")
mae_both = run(AQI_FEATURES + WEATHER_FEATURES, "AQI + Weather")

print(f"Baseline se farq (AQI+Weather): {baseline_mae - mae_both:+.2f} AQI points")
print(f"Test days: {len(test)}")