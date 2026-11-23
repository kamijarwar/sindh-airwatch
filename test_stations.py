import time
import requests

API_KEY = "dfeaa19e2c93eb82eb020dd8e0fa19a51b548d88d1aafd77b8da56527b6c8e33"

HEADERS = {"X-API-Key": API_KEY}
BASE = "https://api.openaq.org/v3"

# Karachi ke beech ka point, 25 km radius (OpenAQ ki max limit)
params = {"coordinates": "24.90,67.10", "radius": 25000, "limit": 100}

r = requests.get(f"{BASE}/locations", headers=HEADERS, params=params, timeout=60)
print("Status:", r.status_code)
if r.status_code != 200:
    print(r.text[:500])
    raise SystemExit

locations = r.json().get("results", [])
print("Total stations mile:", len(locations))
print("-" * 60)

live = 0
for loc in locations:
    # PM2.5 wala sensor dhoondo
    pm25_sensor_ids = [
        s["id"] for s in loc.get("sensors", [])
        if s.get("parameter", {}).get("name") == "pm25"
    ]
    if not pm25_sensor_ids:
        continue

    time.sleep(0.5)  # API par bojh na pare
    lr = requests.get(f"{BASE}/locations/{loc['id']}/latest", headers=HEADERS, timeout=60)
    if lr.status_code != 200:
        print(loc["name"], "-> latest data nahi mila", lr.status_code)
        continue

    value, when = None, None
    for item in lr.json().get("results", []):
        if item.get("sensorsId") in pm25_sensor_ids:
            value = item.get("value")
            when = item.get("datetime", {}).get("utc")

    c = loc.get("coordinates", {})
    print(f"{loc['name']} | lat {c.get('latitude')}, lon {c.get('longitude')} | PM2.5: {value} | time: {when}")
    if value is not None:
        live += 1

print("-" * 60)
print("PM2.5 reading wale stations:", live)