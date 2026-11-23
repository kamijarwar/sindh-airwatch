import difflib
import os
import re
import statistics
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import streamlit as st

from place_search import search_places_in_sindh, get_model_aqi
from openaq_helper import get_sensors_for_place


st.set_page_config(page_title="Sindh AirWatch", page_icon="🌤️", layout="centered")

DEFAULT_PLACE = "Karachi"

# ------------------------------------------------------------------ LANGUAGE
LANGS = {"English": "en", "Roman Urdu": "ro", "اردو": "ur", "English + اردو": "both"}
choice = st.selectbox("🌐 Language / زبان / Zuban", list(LANGS.keys()), index=0)
LANG = LANGS[choice]

# Har text: (English, Roman Urdu, Urdu)
T = {
    "title": ("Sindh AirWatch", "Sindh AirWatch", "سندھ ایئر واچ"),
    "subtitle": (
        "Weather and air quality for all of Sindh",
        "Poore Sindh ka mausam aur hawa",
        "پورے سندھ کا موسم اور ہوا",
    ),
    "search_label": (
        "Search any place in Sindh",
        "Sindh ki kisi bhi jagah ka naam likhein",
        "سندھ کی کسی بھی جگہ کا نام لکھیں",
    ),
    "placeholder": (
        "e.g. Hyderabad, Saddar, Sukkur",
        "Misal: Hyderabad, Saddar, Sukkur",
        "مثال: حیدرآباد، صدر، سکھر",
    ),
    "default_note": (
        "Showing Karachi for now. Type any place in Sindh and press Enter.",
        "Abhi Karachi dikh raha hai. Sindh ki koi bhi jagah likh kar Enter dabayein.",
        "ابھی کراچی دکھایا جا رہا ہے۔ سندھ کی کوئی بھی جگہ لکھ کر Enter دبائیں۔",
    ),
    "not_found": (
        "No place found. Check the spelling.",
        "Koi jagah nahi mili. Spelling check karein.",
        "کوئی جگہ نہیں ملی۔ ہجے چیک کریں۔",
    ),
    "did_you_mean": (
        "Did you mean one of these?",
        "Kya aap ye dhoondh rahe the?",
        "کیا آپ یہ تلاش کر رہے تھے؟",
    ),
    "choose_sugg": ("Choose", "Chunein", "چنیں"),
    "other_places": (
        "Other places with this name",
        "Isi naam ki aur jagahen",
        "اسی نام کی دوسری جگہیں",
    ),
    "choose": ("Choose place", "Jagah chunein", "جگہ چنیں"),
    "sec_weather": ("🌡️ Weather now", "🌡️ Abhi ka mausam", "🌡️ اس وقت کا موسم"),
    "feels": ("Feels like", "Mehsoos ho raha", "محسوس ہو رہا"),
    "humidity": ("Humidity", "Nami", "نمی"),
    "wind": ("Wind", "Hawa", "ہوا"),
    "sec_aqi": ("🌫️ Air quality", "🌫️ Hawa ki quality", "🌫️ ہوا کا معیار"),
    "ground": ("📡 Ground sensors", "📡 Zameeni sensors", "📡 زمینی سینسرز"),
    "model": ("🛰️ Model estimate", "🛰️ Model ka andaza", "🛰️ ماڈل کا اندازہ"),
    "pm": ("PM2.5", "PM2.5", "PM2.5"),
    "sec_rain": (
        "☔ Rain chance (next 6 hours)",
        "☔ Baarish ka imkaan (agle 6 ghante)",
        "☔ بارش کا امکان (اگلے 6 گھنٹے)",
    ),
    "sec_mask": ("😷 Mask", "😷 Mask", "😷 ماسک"),
    "sec_health": ("🧑‍⚕️ Health advice", "🧑‍⚕️ Sehat ki salah", "🧑‍⚕️ صحت کا مشورہ"),
    "who0": ("General public", "Aam log", "عام لوگ"),
    "who1": ("Children", "Bachay", "بچے"),
    "who2": ("Elderly", "Bazurg", "بزرگ"),
    "who3": ("Asthma & heart patients", "Dama aur dil ke mareez", "دمہ اور دل کے مریض"),
    "model_note": (
        "No ground sensor here. The AQI is a satellite and weather model estimate.",
        "Yahan zameeni sensor nahi. AQI satellite aur weather model ka andaza hai.",
        "یہاں زمینی سینسر نہیں۔ AQI سیٹلائٹ اور موسمی ماڈل کا اندازہ ہے۔",
    ),
    "one_sensor": (
        "Only 1 ground sensor nearby ({v} µg/m³, {age} hours old). One sensor is not enough for the whole area, so the model AQI is shown.",
        "Qareeb sirf 1 zameeni sensor hai ({v} µg/m³, {age} ghante purana). Ek sensor se poore ilake ka AQI nahi dikhaya ja sakta, is liye model ka AQI dikhaya gaya hai.",
        "قریب صرف 1 زمینی سینسر ہے ({v} µg/m³، {age} گھنٹے پرانا)۔ ایک سینسر سے پورے علاقے کا AQI نہیں دکھایا جا سکتا، اس لیے ماڈل کا AQI دکھایا گیا ہے۔",
    ),
    "forecast_note": (
        "Current reading only. Tomorrow's forecast is not available for this place yet.",
        "Sirf abhi ki reading. Is jagah ka kal ka forecast abhi available nahi.",
        "صرف موجودہ ریڈنگ۔ اس جگہ کا کل کا فورکاسٹ ابھی دستیاب نہیں۔",
    ),
    "rain_note": (
        "Chance of rain in the next 6 hours.",
        "Agle 6 ghanton mein baarish ka imkaan.",
        "اگلے 6 گھنٹوں میں بارش کا امکان۔",
    ),
    "details": ("📊 Sensor details", "📊 Sensor ki details", "📊 سینسر کی تفصیلات"),
    "age_radio": (
        "How old can the sensor data be?",
        "Sensor ka data kitna purana ho sakta hai?",
        "سینسر کا ڈیٹا کتنا پرانا ہو سکتا ہے؟",
    ),
    "hours_fmt": ("{h} hours", "{h} ghante tak", "{h} گھنٹے تک"),
    "old_warn": (
        "{n} sensor(s) older than {h} hours.",
        "{n} sensor {h} ghante se purane hain.",
        "{n} سینسر {h} گھنٹے سے پرانے ہیں۔",
    ),
    "col_sensor": ("Sensor", "Sensor", "سینسر"),
    "col_dist": ("Distance (km)", "Doori (km)", "فاصلہ (km)"),
    "col_aqi": ("AQI", "AQI", "AQI"),
    "col_pm": ("PM2.5", "PM2.5", "PM2.5"),
    "col_age": ("Hours ago", "Ghante pehle", "گھنٹے پہلے"),
    "no_data": (
        "Weather data is not available right now. Try again later.",
        "Abhi mausam ka data nahi mil raha. Thodi der baad try karein.",
        "ابھی موسم کا ڈیٹا دستیاب نہیں۔ بعد میں کوشش کریں۔",
    ),
    "no_key": (
        "OpenAQ key not found. Ground sensors are off.",
        "OpenAQ key nahi mili. Zameeni sensors band hain.",
        "OpenAQ کی نہیں ملی۔ زمینی سینسر بند ہیں۔",
    ),
    "src": (
        "Data: Open-Meteo and OpenAQ",
        "Data: Open-Meteo aur OpenAQ",
        "ڈیٹا: Open-Meteo اور OpenAQ",
    ),
}


def pick(tup):
    """Tuple (en, ro, ur) mein se chosen language ka text."""
    en, ro, ur = tup
    if LANG == "en":
        return en
    if LANG == "ro":
        return ro
    if LANG == "ur":
        return ur
    return f"{en} | {ur}"


def tx(key, **kw):
    s = pick(T[key])
    return s.format(**kw) if kw else s


# ------------------------------------------------------------------ KNOWN PLACES (spelling ke liye)
KNOWN_PLACES = [
    "Karachi", "Saddar", "DHA", "Clifton", "Gulshan-e-Iqbal", "Gulistan-e-Johar",
    "Korangi", "Malir", "Lyari", "Orangi Town", "Nazimabad", "North Nazimabad",
    "Landhi", "Keamari", "Scheme 33", "PECHS", "Tariq Road", "Baldia Town",
    "Surjani Town", "Federal B Area",
    "Hyderabad", "Sukkur", "Larkana", "Mirpur Khas", "Nawabshah", "Shaheed Benazirabad",
    "Jacobabad", "Khairpur", "Dadu", "Thatta", "Badin", "Tando Allahyar", "Tando Adam",
    "Tando Muhammad Khan", "Tando Jam", "Kotri", "Sehwan", "Shikarpur", "Ghotki",
    "Umerkot", "Matiari", "Hala", "Sanghar", "Jamshoro", "Kandhkot", "Kashmore",
    "Moro", "Naushahro Feroze", "Gambat",
]


def suggestions(q):
    """Galat spelling par mile-julte naam (shuru wale + milte julte)."""
    ql = q.lower().strip()
    lower_map = {n.lower(): n for n in KNOWN_PLACES}
    starts = [n for n in KNOWN_PLACES if n.lower().startswith(ql)]
    close = [lower_map[c] for c in difflib.get_close_matches(ql, list(lower_map), n=6, cutoff=0.5)]
    out = []
    for n in starts + close:
        if n not in out:
            out.append(n)
    return out[:6]


# ------------------------------------------------------------------ AQI CATEGORIES
CATS = [
    dict(upper=50, color="#2E9E4F", text="white",
         name=("Good", "Acha", "اچھی"),
         mask=("No mask required.", "Mask ki zaroorat nahi.", "ماسک کی ضرورت نہیں۔"),
         adv=[
             ("Normal outdoor activities.", "Bahar ki sargarmiyan normal.", "باہر کے کام معمول کے مطابق کریں۔"),
             ("Safe to play outside.", "Bahar khelna bilkul theek.", "باہر کھیلنا محفوظ ہے۔"),
             ("Normal routine.", "Normal routine.", "معمول کے مطابق۔"),
             ("Normal routine. Keep medicines handy.", "Dawaiyan saath rakhein.", "دوائیں ساتھ رکھیں۔"),
         ]),
    dict(upper=100, color="#F2C500", text="black",
         name=("Moderate", "Darmiyana", "درمیانی"),
         mask=("Mask not required (optional for sensitive groups).",
               "Mask zaroori nahi. Hassas log chahein to pehn sakte hain.",
               "ماسک ضروری نہیں، حساس افراد چاہیں تو پہن سکتے ہیں۔"),
         adv=[
             ("Normal routine.", "Normal routine.", "معمول کے مطابق۔"),
             ("Can play outside.", "Bahar khel sakte hain.", "باہر کھیل سکتے ہیں۔"),
             ("Avoid prolonged heavy exertion.", "Lambi bahar ki mehnat se bachein.", "زیادہ دیر کی سخت مشقت سے بچیں۔"),
             ("Limit heavy exertion. Keep inhaler.", "Mehnat kam karein. Inhaler saath rakhein.", "مشقت کم کریں، انہیلر ساتھ رکھیں۔"),
         ]),
    dict(upper=150, color="#F28C1E", text="black",
         name=("Unhealthy for Sensitive Groups", "Hassas logon ke liye kharab", "حساس افراد کے لیے خراب"),
         mask=("A mask outdoors is recommended for sensitive groups.",
               "Bahar jaate waqt mask pehenna behtar hai.",
               "باہر جاتے وقت ماسک پہننا بہتر ہے۔"),
         adv=[
             ("Reduce prolonged outdoor exertion.", "Bahar lambi mehnat kam karein.", "باہر لمبی مشقت کم کریں۔"),
             ("Avoid playing outside for long hours.", "Bahar der tak na khelein.", "باہر زیادہ دیر نہ کھیلیں۔"),
             ("Reduce outdoor walks.", "Bahar kam jayein.", "باہر کم جائیں۔"),
             ("Stay indoors as much as possible.", "Ghar mein rahein, dawaiyan saath rakhein.", "گھر میں رہیں، دوائیں ساتھ رکھیں۔"),
         ]),
    dict(upper=200, color="#D63B3B", text="white",
         name=("Unhealthy", "Kharab", "خراب"),
         mask=("Wear an N95 / KN95 mask when going outside.",
               "Bahar jana ho to achha mask (N95 / KN95) pehnein.",
               "باہر جانا ہو تو N95 / KN95 ماسک پہنیں۔"),
         adv=[
             ("Avoid outdoor workouts.", "Bahar ki mehnat kam karein.", "باہر ورزش سے بچیں۔"),
             ("Play indoors.", "Ghar ke andar khelein.", "گھر کے اندر کھیلیں۔"),
             ("Stay indoors.", "Ghar mein rahein.", "گھر میں رہیں۔"),
             ("Stay indoors. Consult a doctor if unwell.", "Tabiyat kharab ho to doctor se milein.", "طبیعت خراب ہو تو ڈاکٹر سے ملیں۔"),
         ]),
    dict(upper=300, color="#7B3FA0", text="white",
         name=("Very Unhealthy", "Bohat kharab", "بہت خراب"),
         mask=("An N95 / KN95 mask is mandatory if going outside.",
               "Bahar jana zaroori ho to N95 / KN95 mask pehnein.",
               "باہر جانا ضروری ہو تو N95 / KN95 ماسک پہنیں۔"),
         adv=[
             ("Avoid all outdoor exertion.", "Bahar ki mehnat bilkul na karein.", "باہر کی مشقت بالکل نہ کریں۔"),
             ("Keep strictly indoors.", "Ghar mein rakhein.", "گھر کے اندر رکھیں۔"),
             ("Keep windows closed.", "Khidkiyan band rakhein.", "کھڑکیاں بند رکھیں۔"),
             ("Seek medical help if needed.", "Tabiyat bigray to doctor se rabta karein.", "ضرورت ہو تو ڈاکٹر سے رجوع کریں۔"),
         ]),
    dict(upper=10_000, color="#7E0023", text="white",
         name=("Hazardous", "Khatarnak", "خطرناک"),
         mask=("Strictly wear an N95 / KN95 respirator mask.",
               "Bahar jana ho to N95 / KN95 mask zaroor pehnein.",
               "باہر جانا ہو تو N95 / KN95 ماسک لازمی پہنیں۔"),
         adv=[
             ("Do not go outside.", "Bahar na niklein.", "باہر نہ نکلیں۔"),
             ("Keep strictly indoors.", "Ghar mein rakhein.", "گھر کے اندر رکھیں۔"),
             ("Keep windows closed.", "Khidkiyan band rakhein.", "کھڑکیاں بند رکھیں۔"),
             ("Emergency: stay indoors.", "Foran ehtiyat karein.", "ہنگامی احتیاط کریں۔"),
         ]),
]
WHO_ICONS = ["🧑", "🧒", "👴", "🫁"]


def get_category(aqi):
    for c in CATS:
        if aqi <= c["upper"]:
            return c
    return CATS[-1]


def pm25_to_aqi(pm25):
    """PM2.5 (µg/m³) -> US EPA AQI. Returns (aqi, category_name)."""
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
    for c_low, c_high, i_low, i_high, name in breakpoints:
        if c_low <= c <= c_high:
            return round((i_high - i_low) / (c_high - c_low) * (c - c_low) + i_low), name
    return 500, "Hazardous"


# ------------------------------------------------------------------ STYLE
font_import = (
    "@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap');"
    if LANG in ("ur", "both") else ""
)
st.markdown(
    f"""<style>{font_import}
.stApp {{ background: linear-gradient(180deg, #0a1633 0%, #25427a 100%) fixed !important; }}
[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container h1, .block-container p, .block-container label,
.block-container [data-testid="stCaptionContainer"] {{
  color: #ffffff !important; text-shadow: 0 1px 3px rgba(0,0,0,0.35);
}}
</style>""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ HELPERS
def get_openaq_key():
    try:
        if "OPENAQ_API_KEY" in st.secrets:
            return st.secrets["OPENAQ_API_KEY"]
    except Exception:
        pass
    if os.path.exists(".streamlit/secrets.toml"):
        with open(".streamlit/secrets.toml", "r") as f:
            m = re.search(r'OPENAQ_API_KEY\s*=\s*"([^"]+)"', f.read())
            if m:
                return m.group(1)
    return None


def now_pkt_stamp():
    pkt = datetime.now(timezone.utc) + timedelta(hours=5)
    return pkt.strftime("%H:%M PKT")


def fmt(v, suffix=""):
    return "--" if v is None else f"{round(v)}{suffix}"


@st.cache_data(ttl=3600, show_spinner=False)
def find_places(q):
    return search_places_in_sindh(q)


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_model_aqi(lat, lon):
    return get_model_aqi(lat, lon)


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_weather(lat, lon):
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
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
        return None
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


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_place_sensors(api_key, lat, lon, max_hours=6):
    return get_sensors_for_place(api_key, lat, lon, max_age_hours=max_hours)


def glass(title, body):
    return (
        '<div style="background:rgba(255,255,255,.14);backdrop-filter:blur(10px);'
        'border:1px solid rgba(255,255,255,.25);border-radius:18px;padding:14px 18px;'
        'margin:10px 0;color:#fff;">'
        f'<div style="font-size:13px;font-weight:700;opacity:.9;margin-bottom:8px;">{title}</div>'
        f"{body}</div>"
    )


def hero(name, sub, temp, aqi_val, cat, feels):
    temp_html = "--" if temp is None else f"{round(temp)}°"
    feels_html = "" if feels is None else f"{tx('feels')}: {round(feels)}°"
    return f"""
<div style="background:linear-gradient(160deg,rgba(255,255,255,.24),rgba(255,255,255,.08));
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border:1px solid rgba(255,255,255,.3);border-radius:24px;padding:22px 22px 16px;
  color:#fff;box-shadow:0 10px 30px rgba(0,0,0,.25);margin:10px 0;">
  <div style="font-size:13px;opacity:.85;">{sub}</div>
  <div style="font-size:26px;font-weight:700;margin-top:2px;">{name}</div>
  <div style="display:flex;align-items:flex-end;justify-content:space-between;margin-top:8px;">
    <div>
      <div style="font-size:72px;font-weight:300;line-height:1;">{temp_html}</div>
      <div style="font-size:13px;opacity:.9;margin-top:4px;">{feels_html}</div>
    </div>
    <div style="text-align:right;">
      <div style="background:{cat['color']};color:{cat['text']};padding:4px 14px;border-radius:999px;font-weight:700;display:inline-block;">{aqi_val} AQI</div>
      <div style="font-size:14px;margin-top:6px;font-weight:600;">{pick(cat['name'])}</div>
    </div>
  </div>
</div>
"""


# ------------------------------------------------------------------ PAGE
st.title(tx("title"))
st.caption(tx("subtitle"))

api_key = get_openaq_key()
if not api_key:
    st.caption(tx("no_key"))

query = st.text_input(tx("search_label"), placeholder=tx("placeholder"))

if query.strip():
    target = query.strip()
else:
    target = DEFAULT_PLACE
    st.caption(tx("default_note"))

places = find_places(target)

# Spelling galat ho to milte julte naam dikhao
if not places:
    close = suggestions(target)
    if close:
        st.caption(tx("did_you_mean"))
        chosen = st.selectbox(tx("choose_sugg"), close, key="sugg")
        places = find_places(chosen)

if not places:
    st.warning(tx("not_found"))
    st.stop()

place = places[0]
if len(places) > 1:
    with st.expander(tx("other_places")):
        place = st.selectbox(
            tx("choose"),
            places,
            format_func=lambda p: f"{p['name']} ({p['district'] or 'Sindh'})",
            key="pl",
        )

lat, lon = place["lat"], place["lon"]
m = fetch_model_aqi(lat, lon)
w = fetch_weather(lat, lon)

near = []
if api_key:
    try:
        near = fetch_place_sensors(api_key, lat, lon, 6)
    except Exception:
        near = []

if m is None and not near:
    st.info(tx("no_data"))
    st.stop()

# ---- AQI ka faisla
# 2 ya zyada sensor: zameeni reading. 1 sensor: model AQI (ek sensor se poore ilake ka AQI nahi).
if len(near) >= 2:
    med = statistics.median([s["pm25"] for s in near[:3]])
    aqi_val, _ = pm25_to_aqi(med)
    pm_val = round(med, 1)
    source = tx("ground")
elif m is not None:
    aqi_val = m["aqi"]
    pm_val = m["pm25"]
    source = tx("model")
else:
    med = near[0]["pm25"]
    aqi_val, _ = pm25_to_aqi(med)
    pm_val = round(med, 1)
    source = tx("ground")

cat = get_category(aqi_val)
temp = (w or {}).get("temp")
if temp is None and m is not None:
    temp = m.get("temp")
feels = (w or {}).get("feels")
rain = (w or {}).get("rain")
if rain is None and m is not None:
    rain = m.get("rain")

sub = f"{place['district'] or 'Sindh'} · {now_pkt_stamp()}"
st.markdown(hero(place["name"], sub, temp, aqi_val, cat, feels), unsafe_allow_html=True)

# ---- Section 1: mausam
if w:
    wx_body = (
        '<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">'
        f"<span>{tx('feels')}: <b>{fmt(w['feels'], '°')}</b></span>"
        f"<span>{tx('humidity')}: <b>{fmt(w['hum'], '%')}</b></span>"
        f"<span>{tx('wind')}: <b>{fmt(w['wind'], ' km/h')}</b></span>"
        "</div>"
    )
else:
    wx_body = "--"
st.markdown(glass(tx("sec_weather"), wx_body), unsafe_allow_html=True)

# ---- Section 2: hawa ki quality
aqi_body = (
    f'<div style="font-size:15px;">{tx("pm")}: <b>{pm_val} µg/m³</b> · {source}</div>'
    f'<div style="margin-top:6px;font-size:14px;">{pick(cat["name"])}</div>'
)
st.markdown(glass(tx("sec_aqi"), aqi_body), unsafe_allow_html=True)

if len(near) == 1 and m is not None:
    s = near[0]
    st.caption(tx("one_sensor", v=s["pm25"], age=s["age_hours"]))
elif not near:
    st.caption(tx("model_note"))

# ---- Section 3: baarish
rain_body = (
    f'<div style="font-size:28px;font-weight:700;">{fmt(rain, "%")}</div>'
    f'<div style="font-size:13px;opacity:.85;">{tx("rain_note")}</div>'
)
st.markdown(glass(tx("sec_rain"), rain_body), unsafe_allow_html=True)

# ---- Section 4: mask
st.markdown(glass(tx("sec_mask"), f"<div>{pick(cat['mask'])}</div>"), unsafe_allow_html=True)

# ---- Section 5: sehat ki salah, har group ke liye alag
health_rows = ""
for i, icon in enumerate(WHO_ICONS):
    group_name = tx("who" + str(i))
    advice_text = pick(cat["adv"][i])
    health_rows += (
        f'<div style="margin:6px 0;"><b>{icon} {group_name}</b><br>'
        f'<span style="font-size:14px;">{advice_text}</span></div>'
    )
st.markdown(glass(tx("sec_health"), health_rows), unsafe_allow_html=True)

st.caption(tx("forecast_note"))

# ---- Sensor details (chhupi hui)
if near:
    with st.expander(tx("details")):
        hours = st.radio(
            tx("age_radio"),
            [6, 12, 24],
            index=0,
            horizontal=True,
            format_func=lambda h: tx("hours_fmt", h=h),
            key="hours",
        )
        rows = near if hours == 6 else fetch_place_sensors(api_key, lat, lon, hours)

        if rows:
            df = pd.DataFrame(rows)[["name", "distance_km", "aqi", "pm25", "age_hours"]]
            df.columns = [tx("col_sensor"), tx("col_dist"), tx("col_aqi"), tx("col_pm"), tx("col_age")]
            st.dataframe(df, hide_index=True, use_container_width=True)

            old = [s for s in rows if s["age_hours"] > hours]
            if old:
                st.caption(tx("old_warn", n=len(old), h=hours))

st.caption(tx("src"))