from concurrent.futures import ThreadPoolExecutor
import difflib
import os
import re
import statistics
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from place_search import search_places_in_sindh, get_model_aqi
from openaq_helper import get_sensors_for_place
from city_forecast import find_city, city_has_forecast, city_tomorrow


app = FastAPI(title="Sindh AirWatch API")

# React frontend ko is backend se baat karne ki ijazat (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_URL = "https://api.open-meteo.com/v1/forecast"

SINDH_CITIES = {
    "Karachi": (24.8607, 67.0011),
    "Hyderabad": (25.3960, 68.3578),
    "Sukkur": (27.7052, 68.8574),
    "Larkana": (27.5590, 68.2120),
    "Mirpur Khas": (25.5276, 69.0125),
    "Nawabshah": (26.2442, 68.4100),
    "Jacobabad": (28.2769, 68.4514),
    "Khairpur": (27.5295, 68.7592),
    "Dadu": (26.7319, 67.7750),
    "Thatta": (24.7473, 67.9240),
    "Badin": (24.6557, 68.8383),
    "Sanghar": (26.0469, 68.9492),
    "Shikarpur": (27.9556, 68.6382),
    "Ghotki": (28.0064, 69.3150),
    "Matiari": (25.5971, 68.4467),
    "Umerkot": (25.3616, 69.7362),
    "Tando Allahyar": (25.4600, 68.7200),
    "Tando Adam": (25.7682, 68.6620),
    "Mithi": (24.7370, 69.7971),
    "Kashmore": (28.4326, 69.5836),
    "Jamshoro": (25.4246, 68.2829),
    "Kotri": (25.3650, 68.3080),
    "Tando Muhammad Khan": (25.1250, 68.5390),
    "Sehwan": (26.4249, 67.8613),
    "Kandhkot": (28.2440, 69.1824),
    "Chhor": (25.5126, 69.7836),
    "Moro": (26.6632, 68.0002),
    "Hala": (25.8145, 68.4219),
    "Naushahro Feroze": (26.8401, 68.1227),
    "Gambat": (27.3517, 68.5215),
}

KNOWN_PLACES = list(SINDH_CITIES.keys()) + [
    "Saddar", "DHA", "Clifton", "Gulshan-e-Iqbal", "Gulistan-e-Johar", "Korangi",
    "Malir", "Lyari", "Orangi Town", "Nazimabad", "North Nazimabad", "Landhi",
    "Keamari", "Scheme 33", "PECHS", "Tariq Road", "Baldia Town", "Surjani Town",
    "Shaheed Benazirabad", "Tando Jam", "Latifabad", "Qasimabad", "Hirabad",
    "Kathri", "Jhudo", "Digri",
]


# ------------------------------------------------------------------ SIMPLE CACHE
_CACHE = {}


def cached(key, ttl_seconds, fn):
    now = time.time()
    if key in _CACHE:
        val, expires_at = _CACHE[key]
        if now < expires_at:
            return val
    val = fn()
    if val is not None:
        _CACHE[key] = (val, now + ttl_seconds)
    return val


# ------------------------------------------------------------------ HELPERS
def get_openaq_key():
    env_key = os.environ.get("OPENAQ_API_KEY")
    if env_key:
        return env_key
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r", encoding="utf-8") as f:
                m = re.search(r'OPENAQ_API_KEY\s*=\s*"([^"]+)"', f.read())
                if m:
                    return m.group(1)
        except Exception:
            pass
    return None


def now_pkt():
    return datetime.now(timezone.utc) + timedelta(hours=5)


def pm25_to_aqi(pm25):
    if pm25 is None or pm25 < 0:
        return None
    c = round(float(pm25), 1)
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500),
    ]
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= c <= c_high:
            return round((i_high - i_low) / (c_high - c_low) * (c - c_low) + i_low)
    return 500


def get_suggestions(q):
    ql = (q or "").lower().strip()
    if not ql:
        return []
    lower_map = {n.lower(): n for n in KNOWN_PLACES}
    starts = [n for n in KNOWN_PLACES if n.lower().startswith(ql)]
    close = [
        lower_map[c]
        for c in difflib.get_close_matches(ql, list(lower_map), n=6, cutoff=0.5)
    ]
    out = []
    for n in starts + close:
        if n not in out:
            out.append(n)
    return out[:6]


def fetch_weather(lat, lon):
    def _load():
        try:
            r = requests.get(
                WX_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m",
                    "hourly": "precipitation_probability",
                    "forecast_days": 1,
                    "timezone": "Asia/Karachi",
                },
                timeout=15,
            ).json()
        except Exception:
            return {}
        cur = r.get("current", {})
        probs = (r.get("hourly") or {}).get("precipitation_probability") or []
        next6 = [p for p in probs[:6] if p is not None]
        return {
            "temp": cur.get("temperature_2m"),
            "feels": cur.get("apparent_temperature"),
            "hum": cur.get("relative_humidity_2m"),
            "wind": cur.get("wind_speed_10m"),
            "rain": max(next6) if next6 else None,
        }

    return cached(("wx", round(lat, 3), round(lon, 3)), 1800, _load)


def fetch_strip(lat, lon):
    def _load():
        try:
            common = {
                "latitude": lat,
                "longitude": lon,
                "timezone": "Asia/Karachi",
                "forecast_days": 2,
            }
            aq = requests.get(
                API_URL, params={**common, "hourly": "us_aqi"}, timeout=20
            ).json()
            wx = requests.get(
                WX_URL,
                params={
                    **common,
                    "hourly": "temperature_2m,wind_speed_10m,weather_code,is_day",
                },
                timeout=20,
            ).json()
            a = pd.DataFrame(aq["hourly"])
            w = pd.DataFrame(wx["hourly"])
            a["time"] = pd.to_datetime(a["time"])
            w["time"] = pd.to_datetime(w["time"])
            df = a.merge(w, on="time", how="inner")
            start = (
                now_pkt()
                .replace(tzinfo=None)
                .replace(minute=0, second=0, microsecond=0)
            )
            df = df[df["time"] >= start].dropna(subset=["us_aqi"]).head(24)
            rows = []
            for idx, (_, row) in enumerate(df.iterrows()):
                rows.append(
                    {
                        "time": row["time"].strftime("%H:%M"),
                        "is_now": idx == 0,
                        "aqi": int(round(row["us_aqi"])),
                        "temp": int(round(row["temperature_2m"]))
                        if pd.notna(row["temperature_2m"])
                        else None,
                        "wind": int(round(row["wind_speed_10m"]))
                        if pd.notna(row["wind_speed_10m"])
                        else None,
                        "weather_code": int(row["weather_code"])
                        if pd.notna(row["weather_code"])
                        else 3,
                        "is_day": int(row["is_day"])
                        if pd.notna(row["is_day"])
                        else 1,
                    }
                )
            return rows
        except Exception:
            return []

    return cached(("strip", round(lat, 3), round(lon, 3)), 1800, _load)


def fetch_hourly_history(lat, lon):
    def _load():
        r = requests.get(
            API_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "us_aqi,pm2_5,pm10",
                "past_days": 31,
                "forecast_days": 1,
            },
            timeout=30,
        )
        r.raise_for_status()
        df = pd.DataFrame(r.json()["hourly"])
        df["time"] = pd.to_datetime(df["time"])
        return df

    return cached(("hist", round(lat, 3), round(lon, 3)), 3600, _load)


# ------------------------------------------------------------------ ROUTES
@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Sindh AirWatch API chal rahi hai!"}


@app.get("/api/cities")
def list_cities():
    return {"cities": list(SINDH_CITIES.keys())}


@app.get("/api/nearest")
def nearest_city(lat: float, lon: float):
    if not (23.5 <= lat <= 29.0 and 66.4 <= lon <= 71.2):
        return {"city": "Karachi", "in_sindh": False}
    best_city = "Karachi"
    best_dist = 999999.0
    for name, (clat, clon) in SINDH_CITIES.items():
        d = ((lat - clat) * 111.0) ** 2 + ((lon - clon) * 100.0) ** 2
        if d < best_dist:
            best_dist = d
            best_city = name
    return {"city": best_city, "in_sindh": True}


@app.get("/api/place")
def get_place_data(
    q: str = "Karachi",
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    name: Optional[str] = None,
    district: Optional[str] = None,
    max_hours: int = 6,
):
    api_key = get_openaq_key()
    other_places = []

    if lat is not None and lon is not None and name:
        place = {
            "name": name,
            "district": district or "Sindh",
            "lat": lat,
            "lon": lon,
        }
    else:
        places = cached(("search", q.strip().lower()), 3600, lambda: search_places_in_sindh(q))
        if not places:
            return {
                "found": False,
                "suggestions": get_suggestions(q),
                "has_openaq_key": bool(api_key),
            }
        place = places[0]
        other_places = places

    plat, plon = place["lat"], place["lon"]
    matched_city = find_city(place)
    has_tom = city_has_forecast(matched_city)

    # Saare internet calls ek saath (parallel) chalenge taake app super fast khule
    def load_model():
        return cached(
            ("model", round(plat, 3), round(plon, 3)),
            1800,
            lambda: get_model_aqi(plat, plon),
        )

    def load_sensors(hrs):
        if not api_key:
            return []
        try:
            return cached(
                ("sensors", round(plat, 3), round(plon, 3), hrs),
                1800,
                lambda: get_sensors_for_place(api_key, plat, plon, max_age_hours=hrs),
            )
        except Exception:
            return []

    def load_tomorrow():
        if not has_tom:
            return None
        try:
            return cached(
                ("tom", matched_city or "", round(plat, 3), round(plon, 3)),
                1800,
                lambda: city_tomorrow(matched_city, plat, plon),
            )
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=5) as ex:
        f_model = ex.submit(load_model)
        f_wx = ex.submit(fetch_weather, plat, plon)
        f_near6 = ex.submit(load_sensors, 6)
        f_near_req = ex.submit(load_sensors, max_hours) if max_hours != 6 else f_near6
        f_tom = ex.submit(load_tomorrow)
        f_strip = ex.submit(fetch_strip, plat, plon)

        m = f_model.result()
        w = f_wx.result() or {}
        near6 = f_near6.result() or []
        near_req = f_near_req.result() or []
        tom = f_tom.result()
        strip = f_strip.result() or []

    if len(near6) >= 2:
        med = statistics.median([s["pm25"] for s in near6[:3]])
        aqi_val = pm25_to_aqi(med)
        pm_val = round(med, 1)
        source_type = "ground"
        sensor_count = len(near6)
    elif m is not None:
        aqi_val = m["aqi"]
        pm_val = m["pm25"]
        source_type = "model"
        sensor_count = len(near6)
    elif near6:
        aqi_val = pm25_to_aqi(near6[0]["pm25"])
        pm_val = round(near6[0]["pm25"], 1)
        source_type = "ground"
        sensor_count = 1
    else:
        return {"found": True, "no_data": True, "place": place, "has_openaq_key": bool(api_key)}

    temp = w.get("temp") if w.get("temp") is not None else (m or {}).get("temp")
    rain = w.get("rain") if w.get("rain") is not None else (m or {}).get("rain")
    one_sensor = near6[0] if (len(near6) == 1 and m is not None) else None
    old_count = len([s for s in near_req if s.get("age_hours", 0) > max_hours])

    return {
        "found": True,
        "no_data": False,
        "has_openaq_key": bool(api_key),
        "place": place,
        "other_places": other_places,
        "stamp": now_pkt().strftime("%H:%M PKT"),
        "current": {
            "aqi": aqi_val,
            "pm25": pm_val,
            "temp": round(temp) if temp is not None else None,
            "feels": round(w["feels"]) if w.get("feels") is not None else None,
            "hum": round(w["hum"]) if w.get("hum") is not None else None,
            "wind": round(w["wind"]) if w.get("wind") is not None else None,
            "rain": round(rain) if rain is not None else None,
            "source_type": source_type,
            "sensor_count": sensor_count,
            "one_sensor": one_sensor,
        },
        "tomorrow": tom,
        "hourly_24h": strip,
        "sensors": near_req,
        "sensors_old_count": old_count,
    }


@app.get("/api/ranking")
def get_ranking():
    def _load_all():
        cities_20 = list(SINDH_CITIES.items())[:20]

        def one_city(item):
            name, (la, lo) = item
            m = cached(
                ("model", round(la, 3), round(lo, 3)),
                1800,
                lambda: get_model_aqi(la, lo),
            )
            if m is None:
                return None
            return {
                "city": name,
                "aqi": m["aqi"],
                "temp": round(m["temp"]) if m.get("temp") is not None else None,
            }

        with ThreadPoolExecutor(max_workers=10) as ex:
            rows = [r for r in ex.map(one_city, cities_20) if r is not None]
        rows.sort(key=lambda r: r["aqi"])
        return rows

    return {"rows": cached("ranking_20", 1800, _load_all)}


@app.get("/api/trends")
def get_trends(city: str = "Karachi"):
    if city not in SINDH_CITIES:
        city = "Karachi"
    lat, lon = SINDH_CITIES[city]
    try:
        hourly = fetch_hourly_history(lat, lon)
    except Exception:
        return {"ok": False, "city": city}

    hr = hourly.tail(72).copy()
    hr["time"] = hr["time"] + pd.Timedelta(hours=5)
    hr_valid = hr.dropna(subset=["us_aqi"])

    last24 = hr_valid.tail(24)
    cleanest = None
    peak = None
    if not last24.empty:
        best_row = last24.loc[last24["us_aqi"].idxmin()]
        worst_row = last24.loc[last24["us_aqi"].idxmax()]
        cleanest = {
            "time": best_row["time"].strftime("%I:%M %p"),
            "aqi": int(round(best_row["us_aqi"])),
        }
        peak = {
            "time": worst_row["time"].strftime("%I:%M %p"),
            "aqi": int(round(worst_row["us_aqi"])),
        }

    hourly_72h = [
        {
            "time": row["time"].strftime("%d %b %H:%M"),
            "aqi": round(float(row["us_aqi"]), 1),
        }
        for _, row in hr_valid.iterrows()
    ]

    daily = (
        hourly.set_index("time")["us_aqi"]
        .resample("D")
        .mean()
        .dropna()
        .tail(30)
    )
    daily_30d = [
        {"date": idx.strftime("%d %b"), "aqi": round(float(val), 1)}
        for idx, val in daily.items()
    ]

    return {
        "ok": True,
        "city": city,
        "cleanest": cleanest,
        "peak": peak,
        "hourly_72h": hourly_72h,
        "daily_30d": daily_30d,
    }