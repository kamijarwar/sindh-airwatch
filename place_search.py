import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_URL = "https://api.open-meteo.com/v1/forecast"

HEADERS = {"User-Agent": "SindhAirWatch/1.0 (https://github.com/sindh-airwatch)"}

ALIASES = {
    "mirpurkhas": "Mirpur Khas",
    "mirpur khas": "Mirpur Khas",
    "میرپور خاص": "Mirpur Khas",
    "ميرپور خاص": "Mirpur Khas",
    "umerkot": "Umerkot",
    "umarkot": "Umerkot",
    "umar kot": "Umerkot",
    "shaheed benazirabad": "Nawabshah",
    "نوابشاہ": "Nawabshah",
    "نوابشاهه": "Nawabshah",
    "کراچی": "Karachi",
    "ڪراچي": "Karachi",
    "حیدرآباد": "Hyderabad",
    "حيدرآباد": "Hyderabad",
    "سکھر": "Sukkur",
    "سکر": "Sukkur",
    "لاڑکانہ": "Larkana",
    "لاڙڪاڻو": "Larkana",
    "سانگھڑ": "Sanghar",
    "سانگهڙ": "Sanghar",
    "ٹنڈو آدم": "Tando Adam",
    "ٽنڊو آدم": "Tando Adam",
    "tando m khan": "Tando Muhammad Khan",
    "tando m. khan": "Tando Muhammad Khan",
}

# Sindh ke 30 bare shehar + mashhoor mohalle (foran mil jayenge, bina rukawat)
_FALLBACK = [
    # --- 30 Major Sindh Cities ---
    (["karachi"], "Karachi", "Karachi", 24.8607, 67.0011),
    (["hyderabad"], "Hyderabad", "Hyderabad District", 25.3960, 68.3578),
    (["sukkur"], "Sukkur", "Sukkur District", 27.7052, 68.8574),
    (["larkana"], "Larkana", "Larkana District", 27.5590, 68.2120),
    (["mirpur khas", "mirpurkhas"], "Mirpur Khas", "Mirpur Khas District", 25.5276, 69.0125),
    (["nawabshah", "shaheed benazirabad"], "Nawabshah", "Shaheed Benazirabad", 26.2442, 68.4100),
    (["jacobabad"], "Jacobabad", "Jacobabad District", 28.2769, 68.4514),
    (["khairpur"], "Khairpur", "Khairpur District", 27.5295, 68.7592),
    (["dadu"], "Dadu", "Dadu District", 26.7319, 67.7750),
    (["thatta"], "Thatta", "Thatta District", 24.7473, 67.9240),
    (["badin"], "Badin", "Badin District", 24.6557, 68.8383),
    (["sanghar"], "Sanghar", "Sanghar District", 26.0469, 68.9492),
    (["shikarpur"], "Shikarpur", "Shikarpur District", 27.9556, 68.6382),
    (["ghotki"], "Ghotki", "Ghotki District", 28.0064, 69.3150),
    (["matiari"], "Matiari", "Matiari District", 25.5971, 68.4467),
    (["umerkot", "umarkot", "umar kot"], "Umerkot", "Umerkot District", 25.3616, 69.7362),
    (["tando allahyar"], "Tando Allahyar", "Tando Allahyar District", 25.4600, 68.7200),
    (["tando adam"], "Tando Adam", "Sanghar District", 25.7682, 68.6620),
    (["mithi"], "Mithi", "Tharparkar District", 24.7370, 69.7971),
    (["kashmore"], "Kashmore", "Kashmore District", 28.4326, 69.5836),
    (["jamshoro"], "Jamshoro", "Jamshoro District", 25.4246, 68.2829),
    (["kotri"], "Kotri", "Jamshoro District", 25.3650, 68.3080),
    (["tando muhammad khan", "tando m khan", "tando m. khan"], "Tando Muhammad Khan", "Tando Muhammad Khan District", 25.1250, 68.5390),
    (["sehwan", "sehwan sharif"], "Sehwan", "Jamshoro District", 26.4249, 67.8613),
    (["kandhkot"], "Kandhkot", "Kashmore District", 28.2440, 69.1824),
    (["chhor"], "Chhor", "Umerkot District", 25.5126, 69.7836),
    (["moro"], "Moro", "Naushahro Feroze District", 26.6632, 68.0002),
    (["hala"], "Hala", "Matiari District", 25.8145, 68.4219),
    (["naushahro feroze"], "Naushahro Feroze", "Naushahro Feroze District", 26.8401, 68.1227),
    (["gambat"], "Gambat", "Khairpur District", 27.3517, 68.5215),

    # --- Karachi & Hyderabad Areas ---
    (["saddar", "sadar"], "Saddar", "Karachi", 24.8588, 67.0104),
    (["dha", "clifton"], "DHA / Clifton", "Karachi", 24.8138, 67.0422),
    (["gulshan", "gulshan-e-iqbal", "gulshan iqbal"], "Gulshan-e-Iqbal", "Karachi", 24.9180, 67.0970),
    (["gulistan-e-johar", "gulistan johar"], "Gulistan-e-Johar", "Karachi", 24.9162, 67.1315),
    (["tariq road", "pechs"], "Tariq Road / PECHS", "Karachi", 24.8716, 67.0599),
    (["korangi"], "Korangi", "Karachi", 24.8340, 67.1396),
    (["malir"], "Malir", "Karachi", 24.9065, 67.1608),
    (["lyari"], "Lyari", "Karachi", 24.8532, 66.9983),
    (["landhi"], "Landhi", "Karachi", 24.8500, 67.2000),
    (["keamari"], "Keamari", "Karachi", 24.8300, 66.9800),
    (["latifabad"], "Latifabad", "Hyderabad District", 25.3857, 68.3428),
    (["qasimabad", "qasim abad"], "Qasimabad", "Hyderabad District", 25.3587, 68.3556),
    (["hirabad"], "Hirabad", "Hyderabad District", 25.3760, 68.3700),
]


def _fallback_match(query):
    q = query.lower().strip()
    # Pehle exact match check karo
    for keys, name, district, lat, lon in _FALLBACK:
        if q in keys or q == name.lower():
            return {"name": name, "district": district, "lat": lat, "lon": lon}, True

    # Phir partial match check karo
    for keys, name, district, lat, lon in sorted(_FALLBACK, key=lambda x: -max(len(k) for k in x[0])):
        for k in keys:
            if k in q:
                return {"name": name, "district": district, "lat": lat, "lon": lon}, False
    return None, False


def _nominatim_lookup(query):
    """OpenStreetMap: mohalle aur galiyan bhi milti hain. Sirf Pakistan aur Sindh."""
    params = {
        "q": f"{query}, Sindh, Pakistan",
        "format": "json",
        "addressdetails": 1,
        "limit": 10,
        "countrycodes": "pk",
    }
    try:
        res = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10).json()
        if not isinstance(res, list):
            return []
    except Exception:
        return []

    places = []
    for r in res:
        if not isinstance(r, dict):
            continue
        addr = r.get("address", {})
        state = addr.get("state", "")
        if "Sindh" not in state and "سندھ" not in state:
            continue
        district = (
            addr.get("county")
            or addr.get("state_district")
            or addr.get("city")
            or ""
        )
        name = r.get("name") or r.get("display_name", "").split(",")[0]
        places.append({
            "name": name,
            "district": district,
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
        })
    return places


def _open_meteo_lookup(name):
    params = {
        "name": name,
        "count": 10,
        "country": "PK",
        "language": "en",
        "format": "json",
    }
    try:
        res = requests.get(GEO_URL, params=params, timeout=10).json()
        if not isinstance(res, dict):
            return []
    except Exception:
        return []

    places = []
    for r in res.get("results", []):
        if r.get("admin1") != "Sindh":
            continue
        places.append({
            "name": r.get("name"),
            "district": r.get("admin2", ""),
            "lat": r["latitude"],
            "lon": r["longitude"],
            "population": r.get("population") or 0,
        })
    places.sort(key=lambda p: p["population"], reverse=True)
    return places


def search_places_in_sindh(query, count=10):
    """Sindh ki jagah dhoondta hai: Pehle fast fallback, phir Nominatim aur Open-Meteo."""
    query = (query or "").strip()
    if len(query) < 2:
        return []

    alias = ALIASES.get(query.lower(), query)

    # 1) Agar exact city/area match mil gaya to foran return karo (0 second, koi API fail nahi)
    fb, is_exact = _fallback_match(alias)
    if fb and is_exact:
        return [fb]

    results = []
    seen = set()

    def add(p):
        key = (round(p["lat"], 3), round(p["lon"], 3), p["name"])
        if key not in seen:
            seen.add(key)
            results.append(p)

    if fb:
        add(fb)

    # 2) Nominatim (chhote mohalle, galiyan, gaon)
    for p in _nominatim_lookup(alias):
        add(p)

    # 3) Open-Meteo (shehar aur qasbe)
    for p in _open_meteo_lookup(alias):
        add(p)

    return results[:count]


def get_model_aqi(lat, lon):
    """Open-Meteo ka model AQI, temperature aur baarish ka imkaan. Agar AQI na mile to None."""
    aq_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "us_aqi,pm2_5",
        "timezone": "Asia/Karachi",
    }
    try:
        cur = requests.get(AQ_URL, params=aq_params, timeout=15).json().get("current", {})
    except Exception:
        return None

    if cur.get("us_aqi") is None:
        return None

    wx_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
        "hourly": "precipitation_probability",
        "forecast_days": 1,
        "timezone": "Asia/Karachi",
    }
    temp = None
    rain = None
    try:
        wx = requests.get(WX_URL, params=wx_params, timeout=15).json()
        wcur = wx.get("current", {})
        if wcur.get("temperature_2m") is not None:
            temp = round(wcur["temperature_2m"])

        probs = (wx.get("hourly") or {}).get("precipitation_probability") or []
        next6 = [p for p in probs[:6] if p is not None]
        if next6:
            rain = max(next6)
    except Exception:
        pass

    return {
        "aqi": round(cur["us_aqi"]),
        "pm25": round(cur.get("pm2_5") or 0, 1),
        "temp": temp,
        "rain": rain,
        "time": cur.get("time"),
    }