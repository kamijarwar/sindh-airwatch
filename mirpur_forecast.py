import os
import joblib
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_URL = "https://api.open-meteo.com/v1/forecast"
MODEL_PATH = os.path.join("city_models", "mirpur_khas_rf.joblib")

WEATHER_COLS = [
    "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
    "wind_direction_10m", "precipitation", "surface_pressure", "cloud_cover",
]
AQI_FEATURES = ["aqi_lag1", "aqi_lag2", "aqi_lag7", "aqi_roll3", "aqi_roll7", "month"]
WEATHER_FEATURES = [f"{c}_lag1" for c in WEATHER_COLS]
FEATS = AQI_FEATURES + WEATHER_FEATURES

MIRPUR_CENTER = (25.5276, 69.0125)
MIRPUR_RADIUS_KM = 35

MIRPUR_KEYS = [
    "mirpur khas", "mirpurkhas",
    "میرپور خاص", "میرپورخاص", "ميرپور خاص",
]

_model = None


def is_mirpur(place):
    """Mirpur Khas District ki jagah par yeh model chalega (Kathri, Jhudo, etc. bhi)."""
    name = (place.get("name") or "")
    district = (place.get("district") or "")
    text = f"{name} {district}".lower()

    if any(k in text for k in MIRPUR_KEYS):
        return True

    mirpur_areas = [
        "kathri", "jhudo", "jhurdo", "digri", "kot ghulam muhammad",
        "jamesabad", "sindhri", "hussain bux mari", "shujabad",
        "nau kot", "naukot",
    ]
    if any(a in text for a in mirpur_areas):
        return True
    if any(u in f"{name} {district}" for u in ["کٹھڑی", "جھڈو", "ڈگری", "سندھڑی"]):
        return True

    other_districts = ["sanghar", "umerkot", "umarkot", "tharparkar", "badin", "tando allahyar", "hyder"]
    if any(od in district.lower() for od in other_districts):
        return False

    try:
        dlat = (float(place["lat"]) - MIRPUR_CENTER[0]) * 111.0
        dlon = (float(place["lon"]) - MIRPUR_CENTER[1]) * 111.0 * 0.9
        return (dlat ** 2 + dlon ** 2) ** 0.5 <= MIRPUR_RADIUS_KM
    except (KeyError, TypeError, ValueError):
        return False


def _get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def _features(daily):
    """Har din ke liye sirf pichle dinon ki maloomat (future leak nahi)."""
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


def _daily_now(lat, lon):
    """Pichle 10 din + aaj tak ka AQI aur mausam, din ke hisaab se."""
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


def _rain_tomorrow(lat, lon):
    """Kal ke liye baarish ka imkaan (forecast se)."""
    r = requests.get(WX_URL, params={
        "latitude": lat, "longitude": lon,
        "daily": "precipitation_probability_max",
        "forecast_days": 2, "timezone": "Asia/Karachi",
    }, timeout=30).json()
    vals = (r.get("daily") or {}).get("precipitation_probability_max") or []
    return vals[1] if len(vals) > 1 else None


def mirpur_tomorrow(lat, lon):
    """Return: aaj ka AQI, kal ka AQI (andaza), kal ki baarish %."""
    model = _get_model()
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
        "rain": _rain_tomorrow(lat, lon),
    }