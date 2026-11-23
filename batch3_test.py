import os
import time
from datetime import datetime, timedelta, timezone
import pandas as pd
import requests
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor

AQ_HISTORICAL_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

WEATHER_COLS = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
    "surface_pressure",
    "cloud_cover",
]

AQI_FEATURES = ["aqi_lag1", "aqi_lag2", "aqi_lag7", "aqi_roll3", "aqi_roll7", "month"]
WEATHER_FEATURES = [f"{c}_lag1" for c in WEATHER_COLS]
FEATS = AQI_FEATURES + WEATHER_FEATURES

# Batch 3 ke aakhri 6 shehar
BATCH3_CITIES = {
    "Tando Adam": (25.7682, 68.6620, "data_tando_adam.csv"),
    "Moro": (26.6632, 68.0002, "data_moro.csv"),
    "Gambat": (27.3517, 68.5215, "data_gambat.csv"),
    "Kandhkot": (28.2440, 69.1824, "data_kandhkot.csv"),
    "Mithi": (24.7370, 69.7971, "data_mithi.csv"),
    "Chhor": (25.5126, 69.7836, "data_chhor.csv"),
}


def download_city_data(city_name, lat, lon, csv_path, days=1050):
    """Open-Meteo se ~1050 din ka AQI aur mausam download karta hai."""
    if os.path.exists(csv_path):
        print(f"[OK] {city_name}: '{csv_path}' pehle se mojood hai.")
        return True

    now_utc = datetime.now(timezone.utc)
    end_date = (now_utc - timedelta(days=2)).strftime("%Y-%m-%d")
    start_date = (now_utc - timedelta(days=days)).strftime("%Y-%m-%d")

    for attempt in range(1, 4):
        print(f"[DOWNLOADING] {city_name} ({start_date} se {end_date}) - Koshish {attempt}/3...")
        try:
            aq_res = requests.get(
                AQ_HISTORICAL_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": start_date,
                    "end_date": end_date,
                    "hourly": "us_aqi,pm2_5,pm10",
                    "timezone": "Asia/Karachi",
                },
                timeout=120,
            ).json()

            wx_res = requests.get(
                WX_ARCHIVE_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": start_date,
                    "end_date": end_date,
                    "hourly": ",".join(WEATHER_COLS),
                    "timezone": "Asia/Karachi",
                },
                timeout=120,
            ).json()

            if "hourly" not in aq_res or "hourly" not in wx_res:
                print(f"[ERROR] {city_name}: API se poora data nahi mila.")
                return False

            df_aq = pd.DataFrame(aq_res["hourly"])
            df_wx = pd.DataFrame(wx_res["hourly"])
            df_aq["time"] = pd.to_datetime(df_aq["time"])
            df_wx["time"] = pd.to_datetime(df_wx["time"])

            df = df_aq.merge(df_wx, on="time", how="inner").sort_values("time")
            df.to_csv(csv_path, index=False)
            print(f"[SAVED] {city_name}: '{csv_path}' ({len(df)} rows save ho gayin).")
            time.sleep(1)
            return True

        except Exception as e:
            print(f"[RETRY] {city_name} timeout/error: {e}")
            time.sleep(4)

    print(f"[FAILED] {city_name} 3 koshishon ke baad bhi download nahi ho saka.")
    return False


def build_features(daily):
    """Pichle dinon ki maloomat se features banana (future leak nahi)."""
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


def compare_city(city_name, csv_path):
    """Baseline, XGBoost aur RandomForest ka muqabla karta hai."""
    df = pd.read_csv(csv_path, parse_dates=["time"]).set_index("time").sort_index()
    daily = df.resample("D").mean(numeric_only=True)
    d = build_features(daily)

    d["target_tomorrow"] = d["us_aqi"].shift(-1)
    d["target_change"] = d["target_tomorrow"] - d["us_aqi"]
    d = d.dropna(subset=FEATS + ["target_change", "target_tomorrow"])

    split = int(len(d) * 0.8)
    train = d.iloc[:split]
    test = d.iloc[split:].copy()

    # 1. Baseline (kal = aaj)
    base_mae = float((test["us_aqi"] - test["target_tomorrow"]).abs().mean())

    # 2. XGBoost
    m_xgb = xgb.XGBRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, random_state=42,
    )
    m_xgb.fit(train[FEATS], train["target_change"])
    pred_xgb = test["us_aqi"] + m_xgb.predict(test[FEATS])
    xgb_mae = float((pred_xgb - test["target_tomorrow"]).abs().mean())

    # 3. RandomForest
    m_rf = RandomForestRegressor(
        n_estimators=200, max_depth=6, random_state=42, n_jobs=-1,
    )
    m_rf.fit(train[FEATS], train["target_change"])
    pred_rf = test["us_aqi"] + m_rf.predict(test[FEATS])
    rf_mae = float((pred_rf - test["target_tomorrow"]).abs().mean())

    # Sab se behtar kaun hai?
    best_mae = min(base_mae, xgb_mae, rf_mae)
    if best_mae == rf_mae:
        best_name = "RandomForest"
    elif best_mae == xgb_mae:
        best_name = "XGBoost"
    else:
        best_name = "Baseline"

    rf_gain = (base_mae - rf_mae) / base_mae * 100

    return {
        "City": city_name,
        "Days": len(d),
        "Baseline": round(base_mae, 2),
        "XGBoost": round(xgb_mae, 2),
        "RandomForest": round(rf_mae, 2),
        "RF_Gain_%": round(rf_gain, 1),
        "Best": best_name,
    }


def main():
    print("=" * 72)
    print("BATCH 3 TEST: Tando Adam, Moro, Gambat, Kandhkot, Mithi, Chhor")
    print("=" * 72)

    results = []
    for city_name, (lat, lon, csv_path) in BATCH3_CITIES.items():
        ok = download_city_data(city_name, lat, lon, csv_path)
        if ok:
            res = compare_city(city_name, csv_path)
            results.append(res)

    print("\n" + "=" * 72)
    print("BATCH 3 COMPARISON (Test MAE, kam behtar hai)")
    print("=" * 72)
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
    print("=" * 72)


if __name__ == "__main__":
    main()