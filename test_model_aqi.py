import requests
from place_search import search_places_in_sindh

AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def model_aqi(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "us_aqi,pm2_5",
        "timezone": "Asia/Karachi",
    }
    r = requests.get(AQ_URL, params=params, timeout=20).json()
    cur = r.get("current", {})
    return cur.get("us_aqi"), cur.get("pm2_5"), cur.get("time")


PLACES = [
    "Hyderabad", "Karachi", "Sukkur", "Larkana", "Mirpurkhas", "Mirpur Khas",
    "Nawabshah", "Jacobabad", "Khairpur", "Dadu", "Thatta", "Badin",
    "Tando Adam", "Kotri", "Sehwan", "Shikarpur", "Ghotki", "Tando Allahyar",
    "Umerkot", "Umar Kot", "Matiari", "Hala",
]

print(f"{'Jagah':<18} | {'AQI':>5} | {'PM2.5':>6} | Waqt")
print("-" * 60)

for q in PLACES:
    places = search_places_in_sindh(q)
    if not places:
        print(f"{q:<18} | Location nahi mili")
        continue

    p = places[0]
    try:
        aqi, pm, t = model_aqi(p["lat"], p["lon"])
    except Exception as e:
        print(f"{q:<18} | error: {e}")
        continue

    print(f"{q:<18} | {str(aqi):>5} | {str(pm):>6} | {t}")