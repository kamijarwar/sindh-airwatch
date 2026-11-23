import os
import joblib
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_URL = "https://api.open-meteo.com/v1/forecast"
MODEL_DIR = "city_models"

WEATHER_COLS = [
    "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
    "wind_direction_10m", "precipitation", "surface_pressure", "cloud_cover",
]
AQI_FEATURES = ["aqi_lag1", "aqi_lag2", "aqi_lag7", "aqi_roll3", "aqi_roll7", "month"]
WEATHER_FEATURES = [f"{c}_lag1" for c in WEATHER_COLS]
FEATS = AQI_FEATURES + WEATHER_FEATURES

# 20 Shehar jinka Random Forest farq 2% se zyada hai (Karachi samet)
FORECAST_CITIES = {
    "Karachi": {"lat": 24.8607, "lon": 67.0011, "model": "karachi_rf.joblib", "gain": 7.1},
    "Hyderabad": {"lat": 25.3960, "lon": 68.3578, "model": "hyderabad_rf.joblib", "gain": 5.5},
    "Mirpur Khas": {"lat": 25.5276, "lon": 69.0125, "model": "mirpur_khas_rf.joblib", "gain": 5.9},
    "Sukkur": {"lat": 27.7052, "lon": 68.8574, "model": "sukkur_rf.joblib", "gain": 3.9},
    "Sanghar": {"lat": 26.0469, "lon": 68.9492, "model": "sanghar_rf.joblib", "gain": 5.5},
    "Jacobabad": {"lat": 28.2769, "lon": 68.4514, "model": "jacobabad_rf.joblib", "gain": 2.2},
    "Jamshoro": {"lat": 25.4246, "lon": 68.2829, "model": "jamshoro_rf.joblib", "gain": 6.2},
    "Tando Allahyar": {"lat": 25.4600, "lon": 68.7200, "model": "tando_allahyar_rf.joblib", "gain": 6.8},
    "Kotri": {"lat": 25.3650, "lon": 68.3080, "model": "kotri_rf.joblib", "gain": 4.4},
    "Tando Muhammad Khan": {"lat": 25.1250, "lon": 68.5390, "model": "tando_muhammad_khan_rf.joblib", "gain": 4.2},
    "Shikarpur": {"lat": 27.9556, "lon": 68.6382, "model": "shikarpur_rf.joblib", "gain": 3.7},
    "Ghotki": {"lat": 28.0064, "lon": 69.3150, "model": "ghotki_rf.joblib", "gain": 3.7},
    "Matiari": {"lat": 25.5971, "lon": 68.4467, "model": "matiari_rf.joblib", "gain": 5.3},
    "Umerkot": {"lat": 25.3616, "lon": 69.7362, "model": "umerkot_rf.joblib", "gain": 5.3},
    "Sehwan": {"lat": 26.4249, "lon": 67.8613, "model": "sehwan_rf.joblib", "gain": 3.8},
    "Kashmore": {"lat": 28.4326, "lon": 69.5836, "model": "kashmore_rf.joblib", "gain": 4.8},
    "Tando Adam": {"lat": 25.7682, "lon": 68.6620, "model": "tando_adam_rf.joblib", "gain": 7.2},
    "Kandhkot": {"lat": 28.2440, "lon": 69.1824, "model": "kandhkot_rf.joblib", "gain": 5.7},
    "Mithi": {"lat": 24.7370, "lon": 69.7971, "model": "mithi_rf.joblib", "gain": 5.3},
    "Chhor": {"lat": 25.5126, "lon": 69.7836, "model": "chhor_rf.joblib", "gain": 3.0},
}

MIN_GAIN_PCT = 2.0
_models = {}


def _load_model(model_file):
    if model_file not in _models:
        _models[model_file] = joblib.load(os.path.join(MODEL_DIR, model_file))
    return _models[model_file]


def find_city(place):
    """Search result ko FORECAST_CITIES mein se match karta hai (naam ya coordinates se)."""
    text = f"{place.get('name', '')} {place.get('district', '')}".lower()
    for city in FORECAST_CITIES:
        if city.lower() in text:
            return city
    for city, info in FORECAST_CITIES.items():
        try:
            dlat = (float(place["lat"]) - info["lat"]) * 111.0
            dlon = (float(place["lon"]) - info["lon"]) * 111.0 * 0.9
            # Karachi bada shehar hai is liye 25 km, baqi ke liye 15 km
            radius = 25.0 if city == "Karachi" else 15.0
            if (dlat ** 2 + dlon ** 2) ** 0.5 <= radius:
                return city
        except (KeyError, TypeError, ValueError):
            pass
    return None


def city_has_forecast(city):
    """Tareeqa A: Ab har shehar ke liye kal ka forecast available hai (20 par RF, baqi par Open-Meteo)."""
    return True


def _daily_now(lat, lon):
    aq = requests.get(AQ_URL, params={
        "latitude": lat, "longitude": lon, "hourly": "us_aqi",
        "past_days": 10, "forecast_days": 1, "timezone": "Asia/Karachi",
    }, timeout=30).json()
    wx = requests.get(WX_URL, params={
        "latitude": lat, "longitude": lon,
        "hourly": ",".join(WEATHER_COLS),
        "past_days": 10, "forecast_days": 1, "timezone": "Asia/Karachi",
    }, timeout=30).json()

    a = pd.DataFrame(aq["hourly"])
    a["time"] = pd.to_datetime(a["time"])
    w = pd.DataFrame(wx["hourly"])
    w["time"] = pd.to_datetime(w["time"])

    df = a.merge(w, on="time", how="inner").set_index("time").sort_index()
    now = (datetime.now(timezone.utc) + timedelta(hours=5)).replace(tzinfo=None)
    df = df[df.index <= now]
    return df.resample("D").mean(numeric_only=True)


def _features(daily):
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


def _weather_tomorrow(lat, lon):
    """Kal ki baarish % aur kal ka max/min temperature."""
    r = requests.get(WX_URL, params={
        "latitude": lat, "longitude": lon,
        "daily": "precipitation_probability_max,temperature_2m_max,temperature_2m_min",
        "forecast_days": 2, "timezone": "Asia/Karachi",
    }, timeout=30).json()
    daily = r.get("daily") or {}
    rains = daily.get("precipitation_probability_max") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    return {
        "rain": rains[1] if len(rains) > 1 else None,
        "temp_max": round(tmax[1]) if len(tmax) > 1 and tmax[1] is not None else None,
        "temp_min": round(tmin[1]) if len(tmin) > 1 and tmin[1] is not None else None,
    }


def _openmeteo_tomorrow_aqi(lat, lon):
    """Jin shehron mein RF model nahi hai (jaise Larkana, Badin), wahan Open-Meteo se kal ka AQI."""
    aq = requests.get(AQ_URL, params={
        "latitude": lat, "longitude": lon, "hourly": "us_aqi",
        "past_days": 1, "forecast_days": 2, "timezone": "Asia/Karachi",
    }, timeout=30).json()
    df = pd.DataFrame(aq["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    daily = df.set_index("time")["us_aqi"].resample("D").mean().dropna()
    if len(daily) < 2:
        raise ValueError("Open-Meteo se kal ka AQI nahi mila")
    today_aqi = float(daily.iloc[-2])
    tomorrow_aqi = float(daily.iloc[-1])
    return round(today_aqi), round(tomorrow_aqi)


def city_tomorrow(city, lat, lon):
    """
    Return: aaj ka AQI, kal ka AQI, kal ki baarish %, kal ka temp, aur source.
    - Agar city 20 pass shehron mein hai -> Random Forest model chalega.
    - Agar city baqi Sindh mein hai (jaise Larkana/Badin) -> Open-Meteo forecast chalega.
    """
    wx_tom = _weather_tomorrow(lat, lon)

    if city is not None and city in FORECAST_CITIES:
        info = FORECAST_CITIES[city]
        model = _load_model(info["model"])

        daily = _daily_now(lat, lon)
        if daily.empty:
            raise ValueError("AQI ya mausam ka data khaali hai")
        feat = _features(daily).dropna(subset=FEATS)
        if feat.empty:
            raise ValueError("Pichle dinon ka data kam hai")
        row = feat.iloc[[-1]]

        today_aqi = float(row["us_aqi"].iloc[0])
        change = float(model.predict(row[FEATS])[0])
        tomorrow_aqi = max(0.0, today_aqi + change)

        return {
            "today_aqi": round(today_aqi),
            "tomorrow_aqi": round(tomorrow_aqi),
            "rain": wx_tom["rain"],
            "temp_max": wx_tom["temp_max"],
            "temp_min": wx_tom["temp_min"],
            "source": "local_rf",
            "city": city,
            "gain": info["gain"],
        }

    # Fallback (Tareeqa A): Open-Meteo forecast for Larkana, Badin, Thatta, Moro, etc.
    today_aqi, tomorrow_aqi = _openmeteo_tomorrow_aqi(lat, lon)
    return {
        "today_aqi": today_aqi,
        "tomorrow_aqi": tomorrow_aqi,
        "rain": wx_tom["rain"],
        "temp_max": wx_tom["temp_max"],
        "temp_min": wx_tom["temp_min"],
        "source": "open_meteo",
        "city": None,
        "gain": None,
    }


if __name__ == "__main__":
    print("Testing 1) Karachi (RF Model), 2) Mirpur Khas (RF Model), 3) Larkana (Open-Meteo Fallback)...")
    print("Karachi    ->", city_tomorrow("Karachi", 24.8607, 67.0011))
    print("Mirpur Khas->", city_tomorrow("Mirpur Khas", 25.5276, 69.0125))
    print("Larkana    ->", city_tomorrow(None, 27.5590, 68.2120))