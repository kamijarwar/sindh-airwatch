from datetime import datetime, timezone
import math
import re
import requests

# Karachi ke mashhoor areas ke coordinates (Area Search ke liye)
KARACHI_AREAS = {
    "Saddar": (24.8588, 67.0104),
    "DHA / Clifton": (24.8138, 67.0422),
    "Gulshan-e-Iqbal": (24.9180, 67.0970),
    "Gulistan-e-Johar": (24.9162, 67.1315),
    "Tariq Road / PECHS": (24.8716, 67.0599),
    "North Nazimabad": (24.9372, 67.0423),
    "Korangi": (24.8340, 67.1396),
    "Malir / Airport": (24.9065, 67.1608),
    "Lyari / Kharadar": (24.8532, 66.9983),
    "Orangi Town": (24.9482, 66.9904),
}

# Default center: Karachi
KARACHI_LAT = 24.8607
KARACHI_LON = 67.0011


def pm25_to_aqi(pm25):
  """PM2.5 (µg/m³) ko US EPA standard AQI mein convert karta hai."""
  if pm25 is None or pm25 < 0:
    return None, "Unknown"
  c = round(float(pm25), 1)
  breakpoints = [
      (0.0, 12.0, 0, 50, "Good"),
      (12.1, 35.4, 51, 100, "Moderate"),
      (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups"),
      (55.5, 150.4, 151, 200, "Unhealthy"),
      (150.5, 250.4, 201, 300, "Very Unhealthy"),
      (250.5, 500.4, 301, 500, "Hazardous"),
  ]
  for c_low, c_high, i_low, i_high, category in breakpoints:
    if c_low <= c <= c_high:
      aqi = round(
          ((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low
      )
      return aqi, category
  return 500, "Hazardous"


def haversine_km(lat1, lon1, lat2, lon2):
  """Do points ke darmiyan faasla (km mein) nikalta hai."""
  R = 6371.0
  dlat = math.radians(lat2 - lat1)
  dlon = math.radians(lon2 - lon1)
  a = (
      math.sin(dlat / 2) ** 2
      + math.cos(math.radians(lat1))
      * math.cos(math.radians(lat2))
      * math.sin(dlon / 2) ** 2
  )
  return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_live_karachi_sensors(api_key, max_age_hours=48,
                             lat=KARACHI_LAT, lon=KARACHI_LON,
                             radius_m=25000):
  """Diye gaye coordinates ke around active sensors lata hai.
  Bina lat/lon diye to Karachi ke sensors aate hain (purana behavior)."""
  headers = {"X-API-Key": api_key}
  url = "https://api.openaq.org/v3/locations"
  params = {"coordinates": f"{lat},{lon}", "radius": radius_m, "limit": 50}

  res = requests.get(url, params=params, headers=headers, timeout=10).json()
  now_utc = datetime.now(timezone.utc)
  best_by_name = {}

  for loc in res.get("results", []):
    loc_id = loc.get("id")
    name = (loc.get("name") or "Unknown").strip()
    coords = loc.get("coordinates", {})
    s_lat, s_lon = coords.get("latitude"), coords.get("longitude")
    if s_lat is None or s_lon is None:
      continue

    pm25_sensor_id = None
    for s in loc.get("sensors", []):
      if s.get("parameter", {}).get("name") == "pm25":
        pm25_sensor_id = s.get("id")
        break

    if not pm25_sensor_id:
      continue

    latest_url = f"https://api.openaq.org/v3/locations/{loc_id}/latest"
    latest_res = requests.get(
        latest_url, headers=headers, timeout=10
    ).json()

    for item in latest_res.get("results", []):
      if item.get("sensorsId") == pm25_sensor_id:
        val = item.get("value")
        dt_utc_str = item.get("datetime", {}).get("utc")
        dt_local_str = item.get("datetime", {}).get("local")

        if dt_utc_str and val is not None and val >= 0:
          dt_utc = datetime.fromisoformat(dt_utc_str.replace("Z", "+00:00"))
          age_hours = (now_utc - dt_utc).total_seconds() / 3600.0

          if age_hours <= max_age_hours:
            aqi, category = pm25_to_aqi(val)
            entry = {
                "name": name,
                "lat": s_lat,
                "lon": s_lon,
                "pm25": round(val, 1),
                "aqi": aqi,
                "category": category,
                "updated_local": dt_local_str,
                "age_hours": round(age_hours, 1),
            }
            # Agar naam pehle se hai to sirf sab se taza (kam age_hours) wala rakho
            if (
                name not in best_by_name
                or age_hours < best_by_name[name]["age_hours"]
            ):
              best_by_name[name] = entry

  return list(best_by_name.values())


def find_nearest_sensor(area_name, sensors):
  """Kisi area ke sab se qareeb wala active sensor dhoondta hai."""
  if area_name not in KARACHI_AREAS or not sensors:
    return None
  alat, alon = KARACHI_AREAS[area_name]
  nearest = min(
      sensors, key=lambda s: haversine_km(alat, alon, s["lat"], s["lon"])
  )
  dist_km = round(
      haversine_km(alat, alon, nearest["lat"], nearest["lon"]), 1
  )
  return nearest, dist_km


if __name__ == "__main__":
  with open(".streamlit/secrets.toml", "r") as f:
    key = re.search(r'OPENAQ_API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

  sensors = get_live_karachi_sensors(key)
  print(f"Unique Active Sensors: {len(sensors)}\n")

  for area in ["Saddar", "DHA / Clifton", "Gulistan-e-Johar", "Korangi"]:
    nearest, dist = find_nearest_sensor(area, sensors)
    print(
        f"Area: {area} -> Nearest Sensor: {nearest['name']} ({dist} km door)"
        f" | AQI: {nearest['aqi']} ({nearest['category']})"
    )


def get_sensors_for_place(api_key, lat, lon, radius_km=25, max_age_hours=48):
  """Kisi bhi jagah (lat, lon) ke qareeb ke sensors, sab se qareeb pehle."""
  sensors = get_live_karachi_sensors(
      api_key, max_age_hours=max_age_hours,
      lat=lat, lon=lon, radius_m=int(radius_km * 1000),
  )
  out = []
  for s in sensors:
    d = round(haversine_km(lat, lon, s["lat"], s["lon"]), 1)
    if d <= radius_km:
      s["distance_km"] = d
      out.append(s)
  return sorted(out, key=lambda s: s["distance_km"])