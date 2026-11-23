import os
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import xgboost as xgb

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

# Sindh ke shehar: (latitude, longitude, CSV file)
CITIES = {
    "Hyderabad": (25.3960, 68.3578, "data_hyderabad.csv"),
    "Mirpur Khas": (25.5276, 69.0125, "data_mirpur_khas.csv"),
    "Sukkur": (27.7052, 68.8574, "data_sukkur.csv"),
    "Larkana": (27.5590, 68.2120, "data_larkana.csv"),
    "Nawabshah": (26.2442, 68.4100, "data_nawabshah.csv"),
    "Thatta": (24.7473, 67.9240, "data_thatta.csv"),
    "Badin": (24.6557, 68.8383, "data_badin.csv"),
    "Sanghar": (26.0469, 68.9492, "data_sanghar.csv"),
    "Dadu": (26.7319, 67.7750, "data_dadu.csv"),
    "Khairpur": (27.5295, 68.7592, "data_khairpur.csv"),
    "Jacobabad": (28.2769, 68.4514, "data_jacobabad.csv"),
    "Jamshoro": (25.4246, 68.2829, "data_jamshoro.csv"),
    "Kotri": (25.3650, 68.3080, "data_kotri.csv"),
    "Tando Allahyar": (25.4600, 68.7200, "data_tando_allahyar.csv"),
    "Tando Muhammad Khan": (25.1250, 68.5390, "data_tando_muhammad_khan.csv"),
}

TIMEOUT_SECONDS = 180
MAX_TRIES = 3


def _get_json(url, params):
    """Retry ke saath API call. Timeout ho to dobara try karega."""
    last_error = None
    for attempt in range(1, MAX_TRIES + 1):
        try:
            res = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            last_error = e
            print(f"    Koshish {attempt}/{MAX_TRIES} fail: {e}")
            if attempt < MAX_TRIES:
                time.sleep(5)
    raise last_error


def download_city_data(city_name, lat, lon, csv_path, days=1050):
    """Open-Meteo se ~1050 din ka AQI aur Weather download karta hai."""
    if os.path.exists(csv_path):
        print(f"[OK] {city_name}: '{csv_path}' pehle se mojood hai.")
        return True

    now_utc = datetime.now(timezone.utc)
    end_date = (now_utc - timedelta(days=2)).strftime("%Y-%m-%d")
    start_date = (now_utc - timedelta(days=days)).strftime("%Y-%m-%d")
    print(f"[DOWNLOADING] {city_name} ({start_date} se {end_date})...")

    try:
        aq_res = _get_json(AQ_HISTORICAL_URL, {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "us_aqi,pm2_5,pm10",
            "timezone": "Asia/Karachi",
        })

        wx_res = _get_json(WX_ARCHIVE_URL, {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(WEATHER_COLS),
            "timezone": "Asia/Karachi",
        })

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
        print(f"[ERROR] {city_name} download fail: {e}")
        return False


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


def evaluate_city(city_name, csv_path):
    df = pd.read_csv(csv_path, parse_dates=["time"]).set_index("time").sort_index()
    daily = df.resample("D").mean(numeric_only=True)
    d = build_features(daily)

    d["target_tomorrow"] = d["us_aqi"].shift(-1)
    d["target_change"] = d["target_tomorrow"] - d["us_aqi"]
    d = d.dropna(subset=FEATS + ["target_change", "target_tomorrow"])

    split = int(len(d) * 0.8)
    train = d.iloc[:split]
    test = d.iloc[split:].copy()

    # 1. Baseline: kal = aaj
    base_mae = float((test["us_aqi"] - test["target_tomorrow"]).abs().mean())

    # 2. AQI-only Model
    m_aqi = xgb.XGBRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, random_state=42,
    )
    m_aqi.fit(train[AQI_FEATURES], train["target_change"])
    pred_aqi = test["us_aqi"] + m_aqi.predict(test[AQI_FEATURES])
    aqi_mae = float((pred_aqi - test["target_tomorrow"]).abs().mean())

    # 3. AQI + Weather Model
    m_wx = xgb.XGBRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, random_state=42,
    )
    m_wx.fit(train[FEATS], train["target_change"])
    pred_wx = test["us_aqi"] + m_wx.predict(test[FEATS])
    wx_mae = float((pred_wx - test["target_tomorrow"]).abs().mean())

    gain_wx = (base_mae - wx_mae) / base_mae * 100
    gain_aqi = (base_mae - aqi_mae) / base_mae * 100

    return {
        "City": city_name,
        "Days": len(d),
        "Baseline_MAE": round(base_mae, 2),
        "AQI_Only_MAE": round(aqi_mae, 2),
        "AQI_Weather_MAE": round(wx_mae, 2),
        "Gain_AQI_%": round(gain_aqi, 1),
        "Gain_WX_%": round(gain_wx, 1),
    }


def main():
    print("=" * 75)
    print("SINDH AIRWATCH - ALL CITIES DATA & MODEL TRAINING")
    print("=" * 75)

    results = []
    for city_name, (lat, lon, csv_path) in CITIES.items():
        ok = download_city_data(city_name, lat, lon, csv_path)
        if ok:
            res = evaluate_city(city_name, csv_path)
            results.append(res)

    print("\n" + "=" * 75)
    print("FINAL RESULTS (Sorted by Weather Model Gain %)")
    print("=" * 75)
    if results:
        res_df = pd.DataFrame(results).sort_values(by="Gain_WX_%", ascending=False)
        print(res_df.to_string(index=False))
    else:
        print("Koi result nahi mila. Upar error dekho.")
    print("=" * 75)


if __name__ == "__main__":
    main()