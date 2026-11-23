import re
import time
from place_search import search_places_in_sindh
from openaq_helper import get_sensors_for_place

with open(".streamlit/secrets.toml", "r") as f:
    KEY = re.search(r'OPENAQ_API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

PLACES = [
    "Hyderabad", "Karachi", "Sukkur", "Larkana", "Mirpurkhas",
    "Nawabshah", "Jacobabad", "Khairpur", "Dadu", "Thatta",
    "Badin", "Tando Adam", "Kotri", "Sehwan", "Shikarpur",
    "Ghotki", "Tando Allahyar", "Umerkot", "Matiari", "Hala",
]

print(f"{'Jagah':<18} | {'Sensors':>7} | {'Sab se qareeb (km)':>18} | AQI")
print("-" * 65)

for q in PLACES:
    places = search_places_in_sindh(q)
    if not places:
        print(f"{q:<18} | {'---':>7} | {'Location nahi mili':>18} |")
        continue

    p = places[0]
    try:
        near = get_sensors_for_place(KEY, p["lat"], p["lon"], max_age_hours=24)
    except Exception as e:
        print(f"{q:<18} | error: {e}")
        continue

    if near:
        best = near[0]
        print(f"{q:<18} | {len(near):>7} | {best['distance_km']:>18} | {best['aqi']} ({best['name'][:25]})")
    else:
        print(f"{q:<18} | {0:>7} | {'---':>18} | sensor nahi")

    time.sleep(2)