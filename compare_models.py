import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor

CITIES = {
    "Hyderabad": "data_hyderabad.csv",
    "Mirpur Khas": "data_mirpur_khas.csv",
    "Sukkur": "data_sukkur.csv",
    "Larkana": "data_larkana.csv",
    "Nawabshah": "data_nawabshah.csv",
    "Thatta": "data_thatta.csv",
    "Badin": "data_badin.csv",
    "Sanghar": "data_sanghar.csv",
    "Dadu": "data_dadu.csv",
    "Khairpur": "data_khairpur.csv",
    "Jacobabad": "data_jacobabad.csv",
    "Jamshoro": "data_jamshoro.csv",
    "Kotri": "data_kotri.csv",
    "Tando Allahyar": "data_tando_allahyar.csv",
    "Tando Muhammad Khan": "data_tando_muhammad_khan.csv",
}

WEATHER_COLS = [
    "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
    "wind_direction_10m", "precipitation", "surface_pressure", "cloud_cover",
]
AQI_FEATURES = ["aqi_lag1", "aqi_lag2", "aqi_lag7", "aqi_roll3", "aqi_roll7", "month"]
WEATHER_FEATURES = [f"{c}_lag1" for c in WEATHER_COLS]
FEATS = AQI_FEATURES + WEATHER_FEATURES


def build_features(daily):
    d = daily.copy()
    d["aqi_lag1"] = d["us_aqi"].shift(1)
    d["aqi_lag2"] = d["us_aqi"].shift(2)
    d["aqi_lag7"] = d["us_aqi"].shift(7)
    d["aqi_roll3"] = d["us_aqi"].shift(1).rolling(3).mean()
    d["aqi_roll7"] = d["us_aqi"].shift(1).rolling(7).mean()
    d["month"] = d.index.month
    for c in WEATHER_COLS:
        d[f"{c}_lag1"] = d[c].shift(1)
    return d


def compare_city(city, csv_path):
    df = pd.read_csv(csv_path, parse_dates=["time"]).set_index("time").sort_index()
    daily = df.resample("D").mean(numeric_only=True)
    d = build_features(daily)

    d["target_tomorrow"] = d["us_aqi"].shift(-1)
    d["target_change"] = d["target_tomorrow"] - d["us_aqi"]
    d = d.dropna(subset=FEATS + ["target_change", "target_tomorrow"])

    split = int(len(d) * 0.8)
    train = d.iloc[:split]
    test = d.iloc[split:]

    # 1. Baseline: kal = aaj
    base_mae = np.mean(np.abs(test["us_aqi"] - test["target_tomorrow"]))

    # 2. XGBoost
    xgb_model = xgb.XGBRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, random_state=42,
    )
    xgb_model.fit(train[FEATS], train["target_change"])
    xgb_pred = test["us_aqi"] + xgb_model.predict(test[FEATS])
    xgb_mae = np.mean(np.abs(xgb_pred - test["target_tomorrow"]))

    # 3. Random Forest
    rf_model = RandomForestRegressor(
        n_estimators=200, max_depth=6, min_samples_leaf=5,
        random_state=42, n_jobs=-1,
    )
    rf_model.fit(train[FEATS], train["target_change"])
    rf_pred = test["us_aqi"] + rf_model.predict(test[FEATS])
    rf_mae = np.mean(np.abs(rf_pred - test["target_tomorrow"]))

    scores = {"Baseline": base_mae, "XGBoost": xgb_mae, "RandomForest": rf_mae}
    best = min(scores, key=scores.get)

    return {
        "City": city,
        "Baseline": round(base_mae, 2),
        "XGBoost": round(xgb_mae, 2),
        "RandomForest": round(rf_mae, 2),
        "Best": best,
    }


def main():
    results = []
    for city, path in CITIES.items():
        try:
            results.append(compare_city(city, path))
        except FileNotFoundError:
            print(f"[SKIP] {city}: '{path}' nahi mili.")
        except Exception as e:
            print(f"[ERROR] {city}: {e}")

    if results:
        print("\n" + "=" * 70)
        print("MODEL COMPARISON (Test MAE, kam behtar hai)")
        print("=" * 70)
        print(pd.DataFrame(results).to_string(index=False))
        print("=" * 70)
    else:
        print("Koi result nahi mila.")


if __name__ == "__main__":
    main()