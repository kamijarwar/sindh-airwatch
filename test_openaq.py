import re
import requests

# .streamlit/secrets.toml se key nikalna
with open(".streamlit/secrets.toml", "r") as f:
  content = f.read()

api_key = re.search(r'OPENAQ_API_KEY\s*=\s*"([^"]+)"', content).group(1)
headers = {"X-API-Key": api_key}

# 1. Karachi ke sensors mangwana
url = "https://api.openaq.org/v3/locations"
params = {"coordinates": "24.8607,67.0011", "radius": 25000, "limit": 25}
res = requests.get(url, params=params, headers=headers).json()

print("Live PM2.5 Readings check ho rahi hain...\n")

# 2. Har sensor ke andar PM2.5 dhoondna aur uski taza reading lena
for loc in res.get("results", []):
  loc_id = loc.get("id")
  name = loc.get("name")

  # Dekho is location par PM2.5 ka sensor ID kya hai
  pm25_sensor_id = None
  for s in loc.get("sensors", []):
    if s.get("parameter", {}).get("name") == "pm25":
      pm25_sensor_id = s.get("id")
      break

  if pm25_sensor_id:
    # Taza reading mangwana
    latest_url = f"https://api.openaq.org/v3/locations/{loc_id}/latest"
    latest_res = requests.get(latest_url, headers=headers).json()

    for item in latest_res.get("results", []):
      if item.get("sensorsId") == pm25_sensor_id:
        val = item.get("value")
        time_str = item.get("datetime", {}).get("local", "Unknown time")
        print(f"- {name}: PM2.5 = {val} µg/m³ (Waqt: {time_str})")