import re
from place_search import search_places_in_sindh
from openaq_helper import get_live_karachi_sensors, haversine_km

# API key secrets.toml se
with open(".streamlit/secrets.toml", "r") as f:
    KEY = re.search(r'OPENAQ_API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

RADIUS_KM = 25


def sensors_near_point(lat, lon, sensors, radius_km=RADIUS_KM):
    """Is point ke qareeb ke sensors, sab se qareeb pehle."""
    out = []
    for s in sensors:
        d = haversine_km(lat, lon, s["lat"], s["lon"])
        if d <= radius_km:
            out.append((s, round(d, 1)))
    return sorted(out, key=lambda x: x[1])


if __name__ == "__main__":
    q = input("Jagah ka naam likho: ")
    places = search_places_in_sindh(q)
    if not places:
        print("Koi jagah nahi mili.")
        raise SystemExit

    place = places[0]
    print(f"\nJagah: {place['name']} ({place['district']})")
    print(f"Coordinates: {place['lat']}, {place['lon']}\n")

    print("Live sensors load ho rahe hain...")
    sensors = get_live_karachi_sensors(KEY, lat=place["lat"], lon=place["lon"])
    print(f"Total live sensors: {len(sensors)}\n")

    near = sensors_near_point(place["lat"], place["lon"], sensors)
    if not near:
        print(f"{RADIUS_KM} km ke andar koi sensor nahi mila.")
    else:
        for s, d in near:
            print(f"{s['name']} | {d} km | AQI {s['aqi']} ({s['category']}) | {s['age_hours']} ghante pehle")