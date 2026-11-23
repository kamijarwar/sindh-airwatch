import os
import time
from datetime import datetime, timedelta, timezone
import joblib
import pandas as pd
import requests
from sklearn.ensemble import RandomForestRegressor

AQ_HISTORICAL_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

MODEL_DIR = "city_models"
os.makedirs(MODEL_DIR, exist_ok=True)

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

# 20 Pass hone wale shehar (Karachi + 9 purane + 10 naye)
PASS_CITIES = {
    "Karachi": (24.8607, 67.0011, "data_karachi.csv", "karachi_rf.joblib"),
    "Hyderabad": (25.3960, 68.3578, "data_hyderabad.csv", "hyderabad_rf.joblib"),
    "Mirpur Khas": (25.5276, 69.0125, "data_mirpur_khas.csv", "mirpur_khas_rf.joblib"),
    "Sukkur": (27.7052, 68.8574, "data_sukkur.csv", "sukkur_rf.joblib"),
    "Sanghar": (26.0469, 68.9492, "data_sanghar.csv", "sanghar_rf.joblib"),
    "Jacobabad": (28.2769, 68.4514, "data_jacobabad.csv", "jacobabad_rf.joblib"),
    "Jamshoro": (25.4304, 68.2809, "data_jamshoro.csv", "jamshoro_rf.joblib"),
    "Tando Allahyar": (25.4605, 68.7174, "data_tando_allahyar.csv", "tando_allahyar_rf.joblib"),
    "Kotri": (25.3657, 68.3083, "data_kotri.csv", "kotri_rf.joblib"),
    "Tando Muhammad Khan": (25.1239, 68.5389, "data_tando_muhammad_khan.csv", "tando_muhammad_khan_rf.joblib"),
    "Shikarpur": (27.9556, 68.6382, "data_shikarpur.csv", "shikarpur_rf.joblib"),
    "Ghotki": (28.0064, 69.3150, "data_ghotki.csv", "ghotki_rf.joblib"),
    "Matiari": (25.5971, 68.4467, "data_matiari.csv", "matiari_rf.joblib"),
    "Umerkot": (25.3616, 69.7362, "data_umerkot.csv", "umerkot_rf.joblib"),
    "Sehwan": (26.4249, 67.8613, "data_sehwan.csv", "sehwan_rf.joblib"),
    "Kashmore": (28.4326, 69.5836, "data_kashmore.csv", "kashmore_rf.joblib"),
    "Tando Adam": (25.7682, 68.6620, "data_tando_adam.csv", "tando_adam_rf.joblib"),
    "Kandhkot": (28.2440, 69.1824, "data_kandhkot.csv", "kandhkot_rf.joblib"),
    "Mithi": (24.7370, 69.7971, "data_mithi.csv", "mithi_rf.joblib"),
    "Chhor": (25.5126, 69.7836, "data_chhor.csv", "chhor_rf.joblib"),
}


def ensure_city_data(city_name, lat, lon, csv_path, days=1050):
    """Agar CSV pehle se mojood hai aur usmein weather columns hain toh download nahi karega."""
    if os.path.exists(csv_path):
        try:
            df_check = pd.read_csv(csv_path, nrows=5)
            if all(c in df_check.columns for c in WEATHER_COLS) and "us_aqi" in df_check.columns:
                print(f"[OK] {city_name}: '{csv_path}' pehle se mojood hai.")
                return True
        except Exception:
            pass

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
            print(f"[SAVED DATA] {city_name}: '{csv_path}' ({len(df)} rows).")
            time.sleep(1)
            return True

        except Exception as e:
            print(f"[RETRY] {city_name} error: {e}")
            time.sleep(4)

    print(f"[FAILED] {city_name} download nahi ho saka.")
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


def train_and_save(city_name, csv_path, model_filename):
    df = pd.read_csv(csv_path, parse_dates=["time"]).set_index("time").sort_index()
    daily = df.resample("D").mean(numeric_only=True)
    d = build_features(daily)

    d["target_tomorrow"] = d["us_aqi"].shift(-1)
    d["target_change"] = d["target_tomorrow"] - d["us_aqi"]
    d = d.dropna(subset=FEATS + ["target_change", "target_tomorrow"])

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=6,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(d[FEATS], d["target_change"])

    out_path = os.path.join(MODEL_DIR, model_filename)
    joblib.dump(model, out_path)
    print(f"[MODEL SAVED] {city_name:20s} -> {out_path} ({len(d)} days trained)")


def main():
    print("=" * 70)
    print("SAVING RANDOM FOREST MODELS FOR 20 SINDH CITIES (INCLUDING KARACHI)")
    print("=" * 70)

    saved_count = 0
    for city_name, (lat, lon, csv_path, model_file) in PASS_CITIES.items():
        if ensure_city_data(city_name, lat, lon, csv_path):
            train_and_save(city_name, csv_path, model_file)
            saved_count += 1

    print("=" * 70)
    print(f"MUKAMMAL! {saved_count}/20 shehron ke models '{MODEL_DIR}/' folder mein save ho gaye.")
    print("=" * 70)


if __name__ == "__main__":
    main()