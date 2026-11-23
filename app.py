import difflib
import os
import re
import statistics
from datetime import datetime, timedelta, timezone

import altair as alt
import joblib
import pandas as pd
import requests
import streamlit as st
from streamlit_js_eval import get_geolocation

from place_search import search_places_in_sindh, get_model_aqi
from openaq_helper import get_sensors_for_place
from city_forecast import (
    FORECAST_CITIES,
    FEATS,
    WEATHER_COLS,
    find_city,
    city_has_forecast,
    city_tomorrow,
)


st.set_page_config(page_title="Sindh AirWatch", page_icon="🌤️", layout="centered")

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

QUICK_CITIES = [
    ("Nawabshah", ("Nawabshah", "Nawabshah", "نوابشاہ", "نوابشاهه")),
    ("Mirpur Khas", ("Mirpur Khas", "Mirpur Khas", "میرپور خاص", "ميرپور خاص")),
    ("Hyderabad", ("Hyderabad", "Hyderabad", "حیدرآباد", "حيدرآباد")),
    ("Karachi", ("Karachi", "Karachi", "کراچی", "ڪراچي")),
    ("Sukkur", ("Sukkur", "Sukkur", "سکھر", "سکر")),
    ("Larkana", ("Larkana", "Larkana", "لاڑکانہ", "لاڙڪاڻو")),
    ("Sanghar", ("Sanghar", "Sanghar", "سانگھڑ", "سانگهڙ")),
    ("Tando Adam", ("Tando Adam", "Tando Adam", "ٹنڈو آدم", "ٽنڊو آدم")),
]

KNOWN_PLACES = list(SINDH_CITIES.keys()) + [
    "Saddar", "DHA", "Clifton", "Gulshan-e-Iqbal", "Gulistan-e-Johar", "Korangi",
    "Malir", "Lyari", "Orangi Town", "Nazimabad", "North Nazimabad", "Landhi",
    "Keamari", "Scheme 33", "PECHS", "Tariq Road", "Baldia Town", "Surjani Town",
    "Shaheed Benazirabad", "Tando Jam", "Latifabad", "Qasimabad", "Hirabad",
    "Kathri", "Jhudo", "Digri",
]

# ------------------------------------------------------------------ LANGUAGE
LANGS = {"English": "en", "Roman Urdu": "ro", "اردو": "ur", "سنڌي": "sd"}
choice = st.selectbox("🌐 Language / زبان / ٻولي", list(LANGS.keys()), index=2)
LANG = LANGS[choice]
LIDX = {"en": 0, "ro": 1, "ur": 2, "sd": 3}[LANG]
IS_RTL = LANG in ("ur", "sd")
RTL = "direction:rtl;text-align:right;" if IS_RTL else ""
RTLF = "rtlf" if IS_RTL else ""

# Har text: (English, Roman Urdu, Urdu, Sindhi)
T = {
    "title": ("Sindh AirWatch", "Sindh AirWatch", "سندھ ایئر واچ", "سنڌ ايئر واچ"),
    "subtitle": (
        "Weather, air quality, tomorrow's forecast and health advice across Sindh",
        "Sindh ki har jagah ka mausam, hawa, kal ka andaza aur sehat ki salah",
        "سندھ کی ہر جگہ کا موسم، ہوا، کل کا اندازہ اور صحت کا مشورہ",
        "سنڌ جي هر هنڌ جي موسم، هوا، سڀاڻي جو اندازو ۽ صحت جو مشورو",
    ),
    "quick_lbl": (
        "👆 Tap your city (1-click):",
        "👆 Apna shehar chunein (1-click):",
        "👆 اپنا شہر منتخب کریں (صرف ایک کلک):",
        "👆 پنهنجو شهر چونڊيو (صرف هڪ ڪلڪ):",
    ),
    "search_label": (
        "Or type any city, town, or village in Sindh",
        "Ya Sindh ki kisi bhi jagah ka naam likhein",
        "یا سندھ کے کسی بھی شہر، قصبے یا گاؤں کا نام لکھیں",
        "يا سنڌ جي ڪنهن به شهر يا ڳوٺ جو نالو لکو",
    ),
    "placeholder": (
        "e.g. Nawabshah, Mirpur Khas, Karachi, Hyderabad",
        "Misal: Nawabshah, Mirpur Khas, Karachi, Hyderabad",
        "مثال: نوابشاہ، میرپور خاص، کراچی، حیدرآباد",
        "مثال: نوابشاهه، ميرپور خاص، ڪراچي، حيدرآباد",
    ),
    "gps_note": (
        "📍 Showing your exact GPS location ({city}). Tap a button or type above to switch.",
        "📍 Aapki exact GPS jagah ({city}) dikhayi ja rahi hai. Badalne ke liye button dabayein ya naam likhein.",
        "📍 آپ کا موجودہ GPS شہر ({city}) دکھایا جا رہا ہے۔ بدلنے کے لیے اوپر بٹن دبائیں یا نام لکھیں۔",
        "📍 توهان جو موجوده GPS شهر ({city}) ڏيکاريو پيو وڃي. مٽائڻ لاءِ مٿي بٽڻ دٻايو يا نالو لکو.",
    ),
    "btn_note": (
        "📍 Showing {city}. Tap another city button or search any place above.",
        "📍 Abhi {city} dikh raha hai. Koi aur shehar dekhne ke liye button dabayein ya naam likhein.",
        "📍 ابھی {city} دکھایا جا رہا ہے۔ کوئی اور شہر دیکھنے کے لیے بٹن دبائیں یا نام لکھیں۔",
        "📍 هاڻي {city} ڏيکاريو پيو وڃي. ڪو ٻيو شهر ڏسڻ لاءِ بٽڻ دٻايو يا نالو لکو.",
    ),
    "auto_note": (
        "📍 Showing {city}. Tap your city button above or allow browser GPS.",
        "📍 Abhi {city} dikh raha hai. Upar apne shehar ka button dabayein ya GPS Allow karein.",
        "📍 ابھی {city} دکھایا جا رہا ہے۔ اوپر اپنے شہر کا بٹن دبائیں یا لوکیشن Allow کریں۔",
        "📍 هاڻي {city} ڏيکاريو پيو وڃي. مٿي پنهنجي شهر جو بٽڻ دٻايو يا لوڪيشن Allow ڪريو.",
    ),
    "not_found": (
        "No place found. Check the spelling.",
        "Koi jagah nahi mili. Spelling check karein.",
        "کوئی جگہ نہیں ملی۔ ہجے چیک کریں۔",
        "ڪا به جڳهه نه ملي. اسپيلنگ چيڪ ڪريو۔",
    ),
    "did_you_mean": (
        "Did you mean one of these?",
        "Kya aap ye dhoondh rahe the?",
        "کیا آپ یہ تلاش کر رہے تھے؟",
        "ڇا توهان هي ڳولي رهيا هئا؟",
    ),
    "choose_sugg": ("Choose", "Chunein", "چنیں", "چونڊيو"),
    "other_places": (
        "Other places with this name",
        "Isi naam ki aur jagahen",
        "اسی نام کی دوسری جگہیں",
        "ساڳئي نالي واريون ٻيون جڳهيون",
    ),
    "choose": ("Choose place", "Jagah chunein", "جگہ چنیں", "جڳهه چونڊيو"),
    "verdict_lbl": (
        "Should I go outside right now?",
        "Kya abhi bahar jana theek hai?",
        "کیا ابھی باہر جانا ٹھیک ہے؟",
        "ڇا هاڻي ٻاهر وڃڻ ٺيڪ آهي؟",
    ),
    "feels": ("Feels like", "Mehsoos ho raha", "محسوس ہوتا ہے", "محسوس ٿئي ٿو"),
    "rain": ("Rain chance", "Baarish ka imkaan", "بارش کا امکان", "برسات جو امڪان"),
    "tom_temp": ("Tomorrow temp", "Kal ka darja hararat", "کل کا درجہ حرارت", "سڀاڻي جو گرمي پد"),
    "pm": ("PM2.5", "PM2.5", "باریک ذرات (PM2.5)", "سنهڙا ذرا (PM2.5)"),
    "humidity": ("Humidity", "Nami", "نمی", "نمي"),
    "wind": ("Wind", "Hawa", "ہوا کی رفتار", "هوا جي رفتار"),
    "src_ground": (
        "Ground sensors ({n})", "Zameeni sensors ({n})",
        "زمین پر لگے سینسر ({n})", "زميني سينسر ({n})",
    ),
    "src_model": ("Model estimate", "Model ka andaza", "اندازہ (ماڈل)", "ماڊل جو اندازو"),
    "one_sensor": (
        "Only 1 ground sensor nearby ({v} µg/m³, {age} hours old). One sensor is not enough for the whole area, so the model AQI is shown.",
        "Qareeb sirf 1 zameeni sensor hai ({v} µg/m³, {age} ghante purana). Ek sensor se poore ilake ka AQI nahi, is liye model ka AQI dikhaya gaya hai.",
        "قریب صرف 1 زمینی سینسر ہے ({v} µg/m³، {age} گھنٹے پرانا)۔ ایک سینسر سے پورے علاقے کا AQI نہیں بتایا جا سکتا، اس لیے ماڈل کا AQI دکھایا گیا ہے۔",
        "ويجهو صرف 1 زميني سينسر آهي ({v} µg/m³، {age} ڪلاڪ پراڻو). هڪ سينسر سڄي علائقي جو AQI نٿو ٻڌائي سگهي، تنهنڪري ماڊل جو AQI ڏيکاريو ويو آهي۔",
    ),
    "model_note": (
        "No ground sensor here. The AQI is a satellite and weather model estimate.",
        "Yahan zameeni sensor nahi. AQI satellite aur weather model ka andaza hai.",
        "یہاں زمینی سینسر نہیں۔ AQI سیٹلائٹ اور موسمی ماڈل کا اندازہ ہے۔",
        "هتي زميني سينسر ناهي. AQI سيٽلائيٽ ۽ موسمي ماڊل جو اندازو آهي۔",
    ),
    "rain_note": (
        "Chance of rain in the next 6 hours.",
        "Agle 6 ghanton mein baarish ka imkaan.",
        "اگلے 6 گھنٹوں میں بارش کا امکان۔",
        "ايندڙ 6 ڪلاڪن ۾ برسات جو امڪان۔",
    ),
    "tom_rf_title": (
        "Tomorrow's estimate ({city} Random Forest model)",
        "Kal ka andaza ({city} Random Forest model)",
        "کل کا اندازہ ({city} رینڈم فارسٹ ماڈل)",
        "سڀاڻي جو اندازو ({city} رينڊم فاريسٽ ماڊل)",
    ),
    "tom_rf_note": (
        "Local model (~{gain}% better than 'tomorrow = today').",
        "Local model ('kal = aaj' se ~{gain}% behtar).",
        "مقامی ماڈل ('کل = آج' سے تقریباً {gain}% بہتر)۔",
        "مقامي ماڊل ('سڀاڻي = اڄ' کان تقريباً {gain}% بهتر).",
    ),
    "tom_om_title": (
        "Tomorrow's estimate (Open-Meteo forecast)",
        "Kal ka andaza (Open-Meteo forecast)",
        "کل کا اندازہ (Open-Meteo پیشگوئی)",
        "سڀاڻي جو اندازو (Open-Meteo اڳڪٿي)",
    ),
    "tom_om_note": (
        "Satellite & weather forecast for tomorrow.",
        "Satellite aur mausam ke model se kal ka andaza.",
        "سیٹلائٹ اور موسمی ماڈل سے کل کا اندازہ۔",
        "سيٽلائيٽ ۽ موسمي ماڊل مان سڀاڻي جو اندازو.",
    ),
    "hyd_today": (
        "Today's average AQI", "Aaj ka average AQI",
        "آج کا اوسط AQI", "اڄ جو سراسري AQI",
    ),
    "sec_mask": ("😷 Mask", "😷 Mask", "😷 ماسک", "😷 ماسڪ"),
    "sec_health": (
        "🧑‍⚕️ Health advice", "🧑‍⚕️ Sehat ki salah",
        "🧑‍⚕️ صحت کا مشورہ", "🧑‍⚕️ صحت جو مشورو",
    ),
    "who0": ("General public", "Aam log", "عام لوگ", "عام ماڻهو"),
    "who1": ("Children", "Bachay", "بچے", "ٻار"),
    "who2": ("Elderly", "Bazurg", "بزرگ", "بزرگ (پوڙها)"),
    "who3": ("Asthma & heart patients", "Dama aur dil ke mareez", "دمے اور دل کے مریض", "دمي ۽ دل جا مريض"),
    "details": ("📊 Sensor details", "📊 Sensor ki details", "📊 سینسر کی تفصیل", "📊 سينسر جا تفصيل"),
    "age_radio": (
        "How old can the sensor data be?",
        "Sensor ka data kitna purana ho sakta hai?",
        "سینسر کا ڈیٹا کتنا پرانا ہو سکتا ہے؟",
        "سينسر جو ڊيٽا ڪيترو پراڻو هجي؟",
    ),
    "hours_fmt": ("{h} hours", "{h} ghante tak", "{h} گھنٹے تک", "{h} ڪلاڪ تائين"),
    "old_warn": (
        "{n} sensor(s) older than {h} hours.",
        "{n} sensor {h} ghante se purane hain.",
        "{n} سینسر {h} گھنٹے سے پرانے ہیں۔",
        "{n} سينسر {h} ڪلاڪن کان پراڻا آهن۔",
    ),
    "col_sensor": ("Sensor", "Sensor", "سینسر", "سينسر"),
    "col_dist": ("Distance (km)", "Doori (km)", "فاصلہ (km)", "فاصلو (km)"),
    "col_aqi": ("AQI", "AQI", "AQI", "AQI"),
    "col_pm": ("PM2.5", "PM2.5", "PM2.5", "PM2.5"),
    "col_age": ("Hours old", "Ghante purana", "کتنے گھنٹے پرانا", "ڪلاڪ پراڻو"),
    "no_data": (
        "Weather data is not available right now. Try again later.",
        "Abhi mausam ka data nahi mil raha. Thodi der baad try karein.",
        "ابھی موسم کا ڈیٹا دستیاب نہیں۔ کچھ دیر بعد کوشش کریں۔",
        "هن وقت موسم جو ڊيٽا نٿو ملي. ٿوري دير کان پوءِ ڪوشش ڪريو۔",
    ),
    "no_key": (
        "OpenAQ key not found. Ground sensors are off.",
        "OpenAQ key nahi mili. Zameeni sensors band hain.",
        "OpenAQ کی نہیں ملی۔ زمین پر لگے سینسر بند ہیں۔",
        "OpenAQ جي چاٻي (key) نه ملي. زميني سينسر بند آهن۔",
    ),
    "src": (
        "Data: Open-Meteo and OpenAQ",
        "Data: Open-Meteo aur OpenAQ",
        "ڈیٹا: Open-Meteo اور OpenAQ",
        "ڊيٽا: Open-Meteo ۽ OpenAQ",
    ),
    "tab_sindh": ("🔎 Search", "🔎 Search", "🔎 تلاش", "🔎 ڳولا"),
    "tab_rank": ("🏆 Sindh ranking", "🏆 Sindh ranking", "🏆 سندھ کی درجہ بندی", "🏆 سنڌ جي درجابندي"),
    "tab_trend": ("📈 Trends", "📈 Rujhan", "📈 رجحان", "📈 رجحان"),
    "tab_about": ("ℹ️ About", "ℹ️ Maloomat", "ℹ️ معلومات", "ℹ️ معلومات"),
    "rank_title": (
        "Cleanest to most polluted in Sindh (right now)",
        "Sindh ke shehar: sab se saaf se sab se aalooda (abhi)",
        "سندھ کے شہر: سب سے صاف سے سب سے آلودہ تک (ابھی)",
        "سنڌ جا شهر: سڀ کان صاف کان سڀ کان گندي تائين (هاڻي)",
    ),
    "rank_note": (
        "Each city shows the current model AQI. Lower is cleaner.",
        "Har shehar ka abhi ka model AQI. Kam number, zyada saaf hawa.",
        "ہر شہر کا موجودہ AQI۔ کم نمبر، زیادہ صاف ہوا۔",
        "هر شهر جو هاڻوڪو AQI. ننڍو نمبر، وڌيڪ صاف هوا.",
    ),
    "rank_bottom": (
        "This is a model estimate, not from a ground sensor.",
        "Ye model ka andaza hai, zameeni sensor ka nahi.",
        "یہ ماڈل کا اندازہ ہے، زمینی سینسر کا نہیں۔",
        "هي ماڊل جو اندازو آهي، زميني سينسر جو ناهي.",
    ),
    "hourly_title": (
        "Next 24 hours ({place})", "Agle 24 ghante ({place})",
        "اگلے 24 گھنٹے ({place})", "ايندڙ 24 ڪلاڪ ({place})",
    ),
    "now_lbl": ("Now", "Abhi", "ابھی", "هاڻي"),
    "trend_select": (
        "Select city for 72-hour and 30-day trends",
        "72 ghante aur 30 din ka rujhan dekhne ke liye shehar chunein",
        "72 گھنٹے اور 30 دن کا رجحان دیکھنے کے لیے شہر چنیں",
        "72 ڪلاڪ ۽ 30 ڏينهن جو رجحان ڏسڻ لاءِ شهر چونڊيو",
    ),
    "trend72": (
        "Last 72 hours ({city})", "Pichle 72 ghante ({city})",
        "پچھلے 72 گھنٹے ({city})", "گذريل 72 ڪلاڪ ({city})",
    ),
    "trend30": (
        "Last 30 days daily average ({city})", "Pichle 30 din roz ka average ({city})",
        "پچھلے 30 دن کی روزانہ اوسط ({city})", "گذريل 30 ڏينهن جي روزاني سراسري ({city})",
    ),
    "cleanest": (
        "🌿 Cleanest hour (24h)", "🌿 Sab se saaf ghanta (24h)",
        "🌿 سب سے صاف گھنٹہ (24 گھنٹے)", "🌿 سڀ کان صاف ڪلاڪ (24 ڪلاڪ)",
    ),
    "peak": (
        "⚠️ Peak pollution (24h)", "⚠️ Sab se zyada pollution (24h)",
        "⚠️ سب سے زیادہ آلودگی (24 گھنٹے)", "⚠️ سڀ کان وڌيڪ گدلاڻ (24 ڪلاڪ)",
    ),
    "tz": (
        "Time is in PKT (UTC+5).", "Waqt Pakistan ke hisaab se hai.",
        "وقت پاکستان کے مطابق ہے۔", "وقت پاڪستان جي حساب سان آهي (UTC+5)۔",
    ),
    "about_title": ("How it works", "Ye kaise kaam karta hai?", "یہ کیسے کام کرتا ہے؟", "هي ڪيئن ڪم ڪري ٿو؟"),
    "about_body": (
        "<b>Sindh AirWatch</b> provides real-time weather, air quality (AQI), and tomorrow's forecast for every city, town, and village in Sindh.<br><br>"
        "• <b>Exact Browser GPS + 1-Click Buttons:</b> The app uses your browser GPS to open your exact city, and offers 1-click buttons in English, Roman Urdu, Urdu, and Sindhi.<br>"
        "• <b>Smart Forecasting:</b> For 20 cities, a local Random Forest model is used. For other places, Open-Meteo's next-day forecast is shown.<br>"
        "• <b>Honest Note:</b> Most places have no ground sensors, so readings are satellite and weather model estimates. Forecasts are estimates, not guaranteed values. Patients should always follow their doctor's advice.<br><br>"
        "<b>Model vs. simple baseline ('tomorrow = today'), test MAE:</b><br>"
        "<table style='width:100%;font-size:13px;border-collapse:collapse;'>"
        "<tr><th align='left'>City</th><th>Model MAE</th><th>Baseline MAE</th><th>Gain</th></tr>"
        "<tr><td>Karachi</td><td>5.86</td><td>6.31</td><td>7.1%</td></tr>"
        "<tr><td>Tando Adam</td><td>6.25</td><td>6.73</td><td>7.2%</td></tr>"
        "<tr><td>Hyderabad</td><td>5.88</td><td>6.22</td><td>5.5%</td></tr>"
        "<tr><td>Mirpur Khas</td><td>5.90</td><td>6.27</td><td>5.9%</td></tr>"
        "<tr><td>Sukkur</td><td>11.32</td><td>11.78</td><td>3.9%</td></tr>"
        "<tr><td>Larkana (no forecast)</td><td>11.41</td><td>11.52</td><td>1.0%</td></tr>"
        "</table>"
        "<br>The model is only slightly better than the baseline. Please treat all forecasts as estimates.",
        "<b>Sindh AirWatch</b> Sindh ke har shehar ke liye mausam, hawa ka maeyar (AQI) aur kal ka andaza dikhati hai.<br><br>"
        "• <b>Asli Browser GPS + 1-Click Buttons:</b> App GPS se aapka shehar pehchanti hai, aur English, Roman Urdu, Urdu aur Sindhi mein 1-click buttons deti hai.<br>"
        "• <b>Smart Forecasting:</b> 20 shehron ke liye local Random Forest model, baqi jagahon ke liye Open-Meteo ka kal ka andaza.<br>"
        "• <b>Sachai:</b> Zyada tar jagahon par zameeni sensors nahi hain, is liye ye numbers andaza hain. Mareez hamesha apne doctor ki salah maanein.<br><br>"
        "<b>Model vs simple baseline ('kal = aaj'), test MAE:</b><br>"
        "<table style='width:100%;font-size:13px;border-collapse:collapse;'>"
        "<tr><th align='left'>Shehar</th><th>Model MAE</th><th>Baseline MAE</th><th>Faida</th></tr>"
        "<tr><td>Karachi</td><td>5.86</td><td>6.31</td><td>7.1%</td></tr>"
        "<tr><td>Tando Adam</td><td>6.25</td><td>6.73</td><td>7.2%</td></tr>"
        "<tr><td>Hyderabad</td><td>5.88</td><td>6.22</td><td>5.5%</td></tr>"
        "<tr><td>Mirpur Khas</td><td>5.90</td><td>6.27</td><td>5.9%</td></tr>"
        "<tr><td>Sukkur</td><td>11.32</td><td>11.78</td><td>3.9%</td></tr>"
        "<tr><td>Larkana (forecast nahi)</td><td>11.41</td><td>11.52</td><td>1.0%</td></tr>"
        "</table>"
        "<br>Model simple baseline se sirf thoda behtar hai. Tamam forecasts ko sirf andaza samjhein.",
        "<b>سندھ ایئر واچ</b> سندھ کے ہر شہر کے لیے موسم، ہوا کا معیار (AQI) اور کل کا اندازہ دکھاتی ہے۔<br><br>"
        "• <b>درست GPS اور 1-Click بٹن:</b> ایپ GPS سے آپ کا شہر پہچانتی ہے، اور اردو، سندھی، رومن اردو اور انگریزی میں بٹن دیتی ہے۔<br>"
        "• <b>اسمارٹ پیشگوئی:</b> 20 شہروں کے لیے مقامی Random Forest ماڈل، باقی جگہوں کے لیے Open-Meteo کا کل کا اندازہ۔<br>"
        "• <b>سچائی:</b> زیادہ تر جگہوں پر زمینی سینسر نہیں ہیں، اس لیے یہ نمبر اندازے ہیں۔ مریض ہمیشہ اپنے ڈاکٹر کے مشورے پر عمل کریں۔<br><br>"
        "<b>ماڈل بمقابلہ سادہ طریقہ ('کل = آج')، ٹیسٹ MAE:</b><br>"
        "<table style='width:100%;font-size:13px;border-collapse:collapse;'>"
        "<tr><th align='right'>شہر</th><th>ماڈل MAE</th><th>سادہ MAE</th><th>فائدہ</th></tr>"
        "<tr><td>کراچی</td><td>5.86</td><td>6.31</td><td>7.1%</td></tr>"
        "<tr><td>ٹنڈو آدم</td><td>6.25</td><td>6.73</td><td>7.2%</td></tr>"
        "<tr><td>حیدرآباد</td><td>5.88</td><td>6.22</td><td>5.5%</td></tr>"
        "<tr><td>میرپور خاص</td><td>5.90</td><td>6.27</td><td>5.9%</td></tr>"
        "<tr><td>سکھر</td><td>11.32</td><td>11.78</td><td>3.9%</td></tr>"
        "<tr><td>لاڑکانہ (اندازہ نہیں)</td><td>11.41</td><td>11.52</td><td>1.0%</td></tr>"
        "</table>"
        "<br>ماڈل سادے طریقے سے صرف تھوڑا بہتر ہے۔ تمام پیشگوئیوں کو صرف اندازہ سمجھیں۔",
        "<b>سنڌ ايئر واچ</b> سنڌ جي هر شهر لاءِ موسم، هوا جو معيار (AQI) ۽ سڀاڻي جو اندازو ڏيکاري ٿي.<br><br>"
        "• <b>صحيح GPS ۽ 1-Click بٽڻ:</b> ايپ GPS مان شهر سڃاڻي ٿي، ۽ سنڌي، اردو، رومن اردو ۽ انگريزي ۾ بٽڻ ڏئي ٿي.<br>"
        "• <b>سمارٽ اڳڪٿي:</b> 20 شهرن لاءِ مقامي Random Forest ماڊل، باقي هنڌن لاءِ Open-Meteo جو سڀاڻي جو اندازو.<br>"
        "• <b>سچائي:</b> گهڻن هنڌن تي زميني سينسر ناهن، ان ڪري هي انگ اندازا آهن. مريض هميشه پنهنجي ڊاڪٽر جي صلاح مڃين.<br><br>"
        "<b>ماڊل بمقابله سادو طريقو ('سڀاڻي = اڄ')، ٽيسٽ MAE:</b><br>"
        "<table style='width:100%;font-size:13px;border-collapse:collapse;'>"
        "<tr><th align='right'>شهر</th><th>ماڊل MAE</th><th>سادو MAE</th><th>فائدو</th></tr>"
        "<tr><td>ڪراچي</td><td>5.86</td><td>6.31</td><td>7.1%</td></tr>"
        "<tr><td>ٽنڊو آدم</td><td>6.25</td><td>6.73</td><td>7.2%</td></tr>"
        "<tr><td>حيدرآباد</td><td>5.88</td><td>6.22</td><td>5.5%</td></tr>"
        "<tr><td>ميرپور خاص</td><td>5.90</td><td>6.27</td><td>5.9%</td></tr>"
        "<tr><td>سکر</td><td>11.32</td><td>11.78</td><td>3.9%</td></tr>"
        "<tr><td>لاڙڪاڻو (اندازو ناهي)</td><td>11.41</td><td>11.52</td><td>1.0%</td></tr>"
        "</table>"
        "<br>ماڊل سادي طريقي کان صرف ٿورو بهتر آهي. سڀني اندازن کي صرف تخمينو سمجهو.",
    ),
    "load_err": (
        "Could not load data. Check your internet connection.",
        "Data load nahi ho saka. Internet check karein.",
        "ڈیٹا لوڈ نہیں ہو سکا۔ انٹرنیٹ چیک کریں۔",
        "ڊيٽا لوڊ نه ٿي سگهيو. انٽرنيٽ چيڪ ڪريو.",
    ),
}


def tx(key, **kw):
    s = T[key][LIDX]
    return s.format(**kw) if kw else s


def pick(tup):
    return tup[LIDX]


# ------------------------------------------------------------------ AQI CATEGORIES
CATS = [
    dict(
        upper=50, color="#2E9E4F", text="white",
        name=("Good", "Acha", "اچھی", "سٺو"),
        verdict=("Yes, go out normally.", "Haan, bahar ja sakte hain.", "ہاں، باہر جا سکتے ہیں۔", "ها، ٻاهر وڃي سگهو ٿا۔"),
        mask=("No mask needed.", "Mask ki zaroorat nahi.", "ماسک کی ضرورت نہیں۔", "ماسڪ جي ضرورت ناهي۔"),
        adv=[
            ("Normal outdoor activities.", "Bahar ki sargarmiyan normal.", "باہر کے کام معمول کے مطابق۔", "ٻاهر جا ڪم عام طرح ڪريو۔"),
            ("Safe to play outside.", "Bahar khelna bilkul theek.", "باہر کھیلنا محفوظ ہے۔", "ٻاهر کيڏڻ محفوظ آهي۔"),
            ("Normal routine.", "Normal routine.", "معمول کے مطابق۔", "عام معمول مطابق رهو۔"),
            ("Normal routine. Keep medicines handy.", "Dawaiyan saath rakhein.", "دوائیں ساتھ رکھیں۔", "دوائون پاڻ سان گڏ رکو۔"),
        ],
    ),
    dict(
        upper=100, color="#F2C500", text="black",
        name=("Moderate", "Darmiyana", "درمیانی", "وچولو"),
        verdict=("Yes, but take care.", "Haan, lekin ehtiyat karein.", "ہاں، لیکن احتیاط کریں۔", "ها، پر احتياط ڪريو۔"),
        mask=(
            "Mask not needed (optional for sensitive people).",
            "Mask zaroori nahi. Hassas log chahein to pehn sakte hain.",
            "ماسک ضروری نہیں، حساس افراد چاہیں تو پہن سکتے ہیں۔",
            "ماسڪ ضروري ناهي، حساس ماڻهو چاهين ته پائي سگهن ٿا۔",
        ),
        adv=[
            ("Normal routine.", "Normal routine.", "معمول کے مطابق۔", "عام معمول مطابق رهو۔"),
            ("Can play outside.", "Bahar khel sakte hain.", "باہر کھیل سکتے ہیں۔", "ٻاهر کيڏي سگهو ٿا۔"),
            ("Avoid long heavy exertion.", "Lambi bahar ki mehnat se bachein.", "لمبی سخت مشقت سے بچیں۔", "ڊگهي سخت محنت کان بچو۔"),
            ("Limit heavy exertion. Keep inhaler.", "Mehnat kam karein. Inhaler saath rakhein.", "مشقت کم کریں، انہیلر ساتھ رکھیں۔", "محنت گهٽايو، انهيلر پاڻ سان گڏ رکو۔"),
        ],
    ),
    dict(
        upper=150, color="#F28C1E", text="black",
        name=(
            "Unhealthy for Sensitive Groups", "Hassas logon ke liye kharab",
            "حساس افراد کے لیے خراب", "حساس ماڻهن لاءِ خراب",
        ),
        verdict=(
            "Keep trips short. Children and elderly stay in.",
            "Safar chhota rakhein. Bachay aur bazurg ghar mein rahein.",
            "سفر مختصر رکھیں۔ بچے اور بزرگ گھر میں رہیں۔",
            "سفر ننڍو رکو۔ ٻار ۽ بزرگ گهر ۾ رهن۔",
        ),
        mask=(
            "A mask outdoors is recommended for sensitive people.",
            "Bahar jaate waqt mask pehenna behtar hai.",
            "باہر جاتے وقت ماسک پہننا بہتر ہے۔",
            "ٻاهر وڃڻ وقت ماسڪ پائڻ بهتر آهي۔",
        ),
        adv=[
            ("Reduce long outdoor exertion.", "Bahar lambi mehnat kam karein.", "باہر لمبی مشقت کم کریں۔", "ٻاهر ڊگهي محنت گهٽايو۔"),
            ("Avoid playing outside for long.", "Bahar der tak na khelein.", "باہر زیادہ دیر نہ کھیلیں۔", "ٻاهر گهڻي دير تائين نه کيڏو۔"),
            ("Reduce outdoor walks.", "Bahar kam jayein.", "باہر کم جائیں۔", "ٻاهر گهٽ وڃو۔"),
            ("Stay indoors as much as possible.", "Ghar mein rahein, dawaiyan saath rakhein.", "جہاں تک ممکن ہو گھر میں رہیں، دوائیں ساتھ رکھیں۔", "جيترو ٿي سگهي گهر ۾ رهو، دوائون پاڻ سان گڏ رکو۔"),
        ],
    ),
    dict(
        upper=200, color="#D63B3B", text="white",
        name=("Unhealthy", "Kharab", "خراب", "خراب"),
        verdict=(
            "Go out only if needed, with a mask.",
            "Sirf zaroori ho to jayein, mask ke saath.",
            "صرف ضروری ہو تو جائیں، ماسک کے ساتھ۔",
            "صرف ضروري هجي ته وڃو، ماسڪ سان گڏ.",
        ),
        mask=(
            "Wear an N95 / KN95 mask when going outside.",
            "Bahar jana ho to achha mask (N95 / KN95) pehnein.",
            "باہر جانا ہو تو N95 / KN95 ماسک پہنیں۔",
            "ٻاهر وڃڻ وقت N95 / KN95 ماسڪ پائيو۔",
        ),
        adv=[
            ("Avoid outdoor workouts.", "Bahar ki mehnat kam karein.", "باہر ورزش سے بچیں۔", "ٻاهر ورزش کان بچو۔"),
            ("Play indoors.", "Ghar ke andar khelein.", "گھر کے اندر کھیلیں۔", "گهر جي اندر کيڏو۔"),
            ("Stay indoors.", "Ghar mein rahein.", "گھر میں رہیں۔", "گهر ۾ رهو۔"),
            ("Stay indoors. See a doctor if unwell.", "Tabiyat kharab ho to doctor se milein.", "طبیعت خراب ہو تو ڈاکٹر سے ملیں۔", "طبيعت خراب هجي ته ڊاڪٽر کي ڏيکاريو۔"),
        ],
    ),
    dict(
        upper=300, color="#7B3FA0", text="white",
        name=("Very Unhealthy", "Bohat kharab", "بہت خراب", "تمام خراب"),
        verdict=("Avoid going outside.", "Bahar jane se parhez karein.", "باہر جانے سے پرہیز کریں۔", "ٻاهر وڃڻ کان پرهيز ڪريو۔"),
        mask=(
            "An N95 / KN95 mask is mandatory if going outside.",
            "Bahar jana zaroori ho to N95 / KN95 mask pehnein.",
            "باہر جانا ضروری ہو تو N95 / KN95 ماسک پہنیں۔",
            "ٻاهر وڃڻ لازمي هجي ته N95 / KN95 ماسڪ پائيو۔",
        ),
        adv=[
            ("Avoid all outdoor exertion.", "Bahar ki mehnat bilkul na karein.", "باہر کی مشقت بالکل نہ کریں۔", "ٻاهر ڪا به محنت نه ڪريو۔"),
            ("Keep strictly indoors.", "Ghar mein rakhein.", "گھر کے اندر رکھیں۔", "گهر جي اندر رهو۔"),
            ("Keep windows closed.", "Khidkiyan band rakhein.", "کھڑکیاں بند رکھیں۔", "دريون بند رکو۔"),
            ("Seek medical help if needed.", "Tabiyat bigray to doctor se rabta karein.", "ضرورت ہو تو ڈاکٹر سے رجوع کریں۔", "ضرورت هجي ته ڊاڪٽر سان رابطو ڪريو۔"),
        ],
    ),
    dict(
        upper=10_000, color="#7E0023", text="white",
        name=("Hazardous", "Khatarnak", "خطرناک", "خطرناڪ"),
        verdict=("Do not go outside.", "Bahar na niklein.", "باہر نہ نکلیں۔", "ٻاهر نه نڪرو۔"),
        mask=(
            "Strictly wear an N95 / KN95 respirator mask.",
            "Bahar jana ho to N95 / KN95 mask zaroor pehnein.",
            "باہر جانا ہو تو N95 / KN95 ماسک لازمی پہنیں۔",
            "ٻاهر وڃڻ لاءِ N95 / KN95 ماسڪ لازمي پائيو۔",
        ),
        adv=[
            ("Do not go outside.", "Bahar na niklein.", "باہر نہ نکلیں۔", "ٻاهر نه نڪرو۔"),
            ("Keep strictly indoors.", "Ghar mein rakhein.", "گھر کے اندر رکھیں۔", "گهر جي اندر رهو۔"),
            ("Keep windows closed.", "Khidkiyan band rakhein.", "کھڑکیاں بند رکھیں۔", "دريون بند رکو۔"),
            ("Emergency: stay indoors.", "Foran ehtiyat karein.", "ہنگامی احتیاط کریں۔", "هنگامي احتياط ڪريو۔"),
        ],
    ),
]
WHO_ICONS = ["🧑", "🧒", "👴", "🩺"]


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
font_import = ""
FONT = "inherit"
if LANG == "ur":
    font_import = "@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap');"
    FONT = "'Noto Nastaliq Urdu', serif"
elif LANG == "sd":
    font_import = "@import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic&display=swap');"
    FONT = "'Noto Naskh Arabic', serif"

st.markdown(
    f"""<style>{font_import}
.stApp {{ background: linear-gradient(180deg, #0a1633 0%, #25427a 100%) fixed !important; }}
[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container h1, .block-container h2, .block-container h3,
.block-container p, .block-container label, .block-container li,
.block-container [data-testid="stCaptionContainer"],
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] * {{
  color: #ffffff !important; text-shadow: 0 1px 3px rgba(0,0,0,0.35);
}}
.glass {{ background: rgba(255,255,255,0.14); backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.25); border-radius: 18px;
  padding: 14px 18px; margin: 10px 0; color: #fff; }}
.gt {{ font-size: 15px; font-weight: 700; opacity: .95; margin-bottom: 8px; }}
.rtlf {{ font-family: {FONT}; line-height: 2.1; font-size: 17px; }}
div.stButton > button {{
  background: rgba(255,255,255,0.16) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255,255,255,0.32) !important;
  border-radius: 999px !important;
  padding: 4px 10px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  width: 100% !important;
}}
div.stButton > button:hover {{
  background: rgba(255,255,255,0.30) !important;
  border-color: #ffffff !important;
}}
</style>""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ HELPERS & EXACT BROWSER GPS
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


def _nearest_sindh_city(lat, lon):
    if not (23.5 <= lat <= 29.0 and 66.4 <= lon <= 71.2):
        return None
    best_city = None
    best_dist = 999999.0
    for name, (clat, clon) in SINDH_CITIES.items():
        d = ((lat - clat) * 111.0) ** 2 + ((lon - clon) * 100.0) ** 2
        if d < best_dist:
            best_dist = d
            best_city = name
    return best_city


def get_user_sindh_location():
    try:
        loc = get_geolocation(component_key="sindh_gps")
        if isinstance(loc, dict) and "coords" in loc:
            coords = loc["coords"]
            lat = coords.get("latitude")
            lon = coords.get("longitude")
            if lat is not None and lon is not None:
                near = _nearest_sindh_city(float(lat), float(lon))
                if near:
                    st.session_state["gps_city"] = near
                    return near, True
    except Exception:
        pass

    if "gps_city" in st.session_state:
        return st.session_state["gps_city"], True

    return "Karachi", False


def now_pkt():
    return datetime.now(timezone.utc) + timedelta(hours=5)


def fmt(v, suffix=""):
    return "--" if v is None else f"{round(v)}{suffix}"


def glass_html(title, body):
    head = f'<div class="gt">{title}</div>' if title else ""
    return f'<div class="glass {RTLF}" style="{RTL}">{head}{body}</div>'


def suggestions(q):
    ql = q.lower().strip()
    lower_map = {n.lower(): n for n in KNOWN_PLACES}
    starts = [n for n in KNOWN_PLACES if n.lower().startswith(ql)]
    close = [lower_map[c] for c in difflib.get_close_matches(ql, list(lower_map), n=6, cutoff=0.5)]
    out = []
    for n in starts + close:
        if n not in out:
            out.append(n)
    return out[:6]


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


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_place_sensors(api_key, lat, lon, max_hours=6):
    return get_sensors_for_place(api_key, lat, lon, max_age_hours=max_hours)


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_city_tomorrow(city, lat, lon):
    return city_tomorrow(city, lat, lon)


@st.cache_data(ttl=3600, show_spinner=False)
def get_hourly(lat=24.8607, lon=67.0011):
    r = requests.get(
        API_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": "us_aqi,pm2_5,pm10",
            "past_days": 31,
            "forecast_days": 1,
        },
        timeout=60,
    )
    r.raise_for_status()
    hourly = pd.DataFrame(r.json()["hourly"])
    hourly["time"] = pd.to_datetime(hourly["time"])
    return hourly


@st.cache_data(ttl=1800, show_spinner=False)
def get_strip(lat, lon):
    common = {"latitude": lat, "longitude": lon, "timezone": "Asia/Karachi", "forecast_days": 2}
    aq = requests.get(API_URL, params={**common, "hourly": "us_aqi"}, timeout=30).json()
    wx = requests.get(
        WX_URL,
        params={**common, "hourly": "temperature_2m,wind_speed_10m,weather_code,is_day"},
        timeout=30,
    ).json()
    a = pd.DataFrame(aq["hourly"])
    w = pd.DataFrame(wx["hourly"])
    a["time"] = pd.to_datetime(a["time"])
    w["time"] = pd.to_datetime(w["time"])
    df = a.merge(w, on="time", how="inner")
    start = now_pkt().replace(tzinfo=None).replace(minute=0, second=0, microsecond=0)
    return df[df["time"] >= start].dropna(subset=["us_aqi"]).head(24).reset_index(drop=True)


def wx_icon(code, is_day):
    try:
        c = int(code)
    except Exception:
        return "☁️"
    if c in (0, 1):
        return ("☀️" if c == 0 else "🌤️") if is_day else "🌙"
    if c == 2:
        return "⛅" if is_day else "☁️"
    if c in (45, 48):
        return "🌫️"
    if 51 <= c <= 67 or 80 <= c <= 82:
        return "🌧️"
    if c >= 95:
        return "⛈️"
    return "☁️"


def line_chart(df, x, height=270):
    long = df.melt(x, var_name="Series", value_name="AQI")
    lines = (
        alt.Chart(long)
        .mark_line(strokeWidth=2.5)
        .encode(
            x=alt.X(f"{x}:T", title=None),
            y=alt.Y("AQI:Q", title="US AQI", scale=alt.Scale(zero=False)),
            color=alt.Color("Series:N", legend=alt.Legend(orient="bottom", title=None)),
        )
    )
    rules = (
        alt.Chart(pd.DataFrame({"y": [100, 150]}))
        .mark_rule(strokeDash=[4, 4], opacity=0.35)
        .encode(y="y:Q")
    )
    return (lines + rules).properties(height=height, width="container")


# ------------------------------------------------------------------ TAB 1: SEARCH
def render_search(api_key, default_city, is_gps):
    st.caption(tx("quick_lbl"))
    q_cols1 = st.columns(4)
    q_cols2 = st.columns(4)
    all_q_cols = q_cols1 + q_cols2
    for idx, (eng_name, labels) in enumerate(QUICK_CITIES):
        if all_q_cols[idx].button(f"📍 {pick(labels)}", key=f"qbtn_{eng_name}"):
            st.session_state["quick_city"] = eng_name

    query = st.text_input(tx("search_label"), placeholder=tx("placeholder"))
    if query.strip():
        target = query.strip()
    elif "quick_city" in st.session_state:
        target = st.session_state["quick_city"]
        st.caption(tx("btn_note", city=target))
    else:
        target = default_city
        if is_gps:
            st.caption(tx("gps_note", city=default_city))
        else:
            st.caption(tx("auto_note", city=default_city))

    places = find_places(target)
    if not places:
        close = suggestions(target)
        if close:
            st.caption(tx("did_you_mean"))
            chosen = st.selectbox(tx("choose_sugg"), close, key="sugg")
            places = find_places(chosen)
    if not places:
        st.warning(tx("not_found"))
        return

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

    if len(near) >= 2:
        med = statistics.median([s["pm25"] for s in near[:3]])
        aqi_val, _ = pm25_to_aqi(med)
        pm_val = round(med, 1)
        source = tx("src_ground", n=len(near))
    elif m is not None:
        aqi_val, pm_val, source = m["aqi"], m["pm25"], tx("src_model")
    elif near:
        aqi_val, _ = pm25_to_aqi(near[0]["pm25"])
        pm_val, source = round(near[0]["pm25"], 1), tx("src_ground", n=1)
    else:
        st.info(tx("no_data"))
        return

    cat = get_category(aqi_val)
    temp = w.get("temp") if w.get("temp") is not None else (m or {}).get("temp")
    feels = w.get("feels")
    rain = w.get("rain") if w.get("rain") is not None else (m or {}).get("rain")
    stamp = now_pkt().strftime("%H:%M PKT")

    # ---- 1. Hero Card
    temp_html = "--" if temp is None else f"{round(temp)}°"
    feels_html = "" if feels is None else f"{tx('feels')}: {round(feels)}°"
    st.markdown(
        f"""
<div class="{RTLF}" style="{RTL}background:linear-gradient(160deg,rgba(255,255,255,.24),rgba(255,255,255,.08));
  backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.3);border-radius:24px;
  padding:22px;color:#fff;box-shadow:0 10px 30px rgba(0,0,0,.25);margin:10px 0;">
  <div style="font-size:13px;opacity:.85;">{place['district'] or 'Sindh'} · {stamp}</div>
  <div style="font-size:26px;font-weight:700;">{place['name']}</div>
  <div style="display:flex;align-items:flex-end;justify-content:space-between;margin-top:8px;">
    <div>
      <div style="font-size:72px;font-weight:300;line-height:1;direction:ltr;">{temp_html}</div>
      <div style="font-size:13px;opacity:.9;margin-top:4px;">{feels_html}</div>
    </div>
    <div style="text-align:left;">
      <div style="background:{cat['color']};color:{cat['text']};padding:4px 14px;border-radius:999px;font-weight:700;display:inline-block;direction:ltr;">{aqi_val} AQI</div>
      <div style="font-size:14px;margin-top:6px;font-weight:600;">{pick(cat['name'])}</div>
    </div>
  </div>
</div>""",
        unsafe_allow_html=True,
    )

    # ---- 2. Kal ka Card
    matched_city = find_city(place)
    if city_has_forecast(matched_city):
        try:
            hf = fetch_city_tomorrow(matched_city, lat, lon)
        except Exception:
            hf = None
        if hf:
            hc = get_category(hf["tomorrow_aqi"])
            rain_txt = "--" if hf.get("rain") is None else f"{hf['rain']}%"
            tmax, tmin = hf.get("temp_max"), hf.get("temp_min")
            temp_tom_txt = f"{tmin}°–{tmax}°C" if (tmax is not None and tmin is not None) else "--"

            if hf.get("source") == "local_rf" and hf.get("city"):
                card_title = tx("tom_rf_title", city=hf["city"])
                card_note = tx("tom_rf_note", gain=hf["gain"])
            else:
                card_title = tx("tom_om_title")
                card_note = tx("tom_om_note")

            st.markdown(
                f'<div class="{RTLF}" style="{RTL}background:{hc["color"]};color:{hc["text"]};'
                f'border-radius:18px;padding:14px 18px;margin:10px 0;">'
                f'<div style="font-size:13px;font-weight:700;">{card_title}</div>'
                f'<div style="font-size:30px;font-weight:800;direction:ltr;text-align:left;">'
                f'{hf["tomorrow_aqi"]} AQI · {pick(hc["name"])}</div>'
                f'<div style="font-size:13px;">🌡️ {tx("tom_temp")}: {temp_tom_txt} &nbsp;·&nbsp; ☔ {tx("rain")}: {rain_txt}</div>'
                f'<div style="font-size:12px;opacity:.9;margin-top:2px;">{tx("hyd_today")}: {hf["today_aqi"]} AQI · {card_note}</div>'
                "</div>",
                unsafe_allow_html=True,
            )

    # ---- 3. Verdict
    st.caption(tx("verdict_lbl"))
    st.markdown(
        f'<div class="{RTLF}" style="{RTL}background:{cat["color"]};color:{cat["text"]};border-radius:18px;'
        f'padding:14px 18px;font-weight:700;font-size:18px;margin:4px 0 10px;">{pick(cat["verdict"])}</div>',
        unsafe_allow_html=True,
    )

    # ---- 4. Numbers
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tx("rain"), fmt(rain, "%"))
    c2.metric(tx("pm"), f"{pm_val} µg/m³")
    c3.metric(tx("humidity"), fmt(w.get("hum"), "%"))
    c4.metric(tx("wind"), fmt(w.get("wind"), " km/h"))
    st.caption(f"{tx('rain_note')}  ·  {source}")

    # ---- 5. 24 ghante ki patti
    try:
        strip = get_strip(lat, lon)
    except Exception:
        strip = None
    if strip is not None and not strip.empty:
        cells = ""
        for i, row in strip.iterrows():
            a_h = int(round(row["us_aqi"]))
            c_h = get_category(a_h)
            label = tx("now_lbl") if i == 0 else row["time"].strftime("%H:%M")
            icon = wx_icon(row["weather_code"], int(row["is_day"]))
            cells += (
                '<div style="min-width:62px;text-align:center;padding:6px 3px;">'
                f'<div style="font-size:12px;opacity:.9;">{label}</div>'
                f'<div style="background:{c_h["color"]};color:{c_h["text"]};border-radius:6px;font-weight:700;margin:6px 3px;padding:3px 0;">{a_h}</div>'
                f'<div style="font-size:20px;">{icon}</div>'
                f'<div style="font-size:13px;direction:ltr;">{row["temperature_2m"]:.0f}°</div>'
                f'<div style="font-size:11px;opacity:.85;direction:ltr;">{row["wind_speed_10m"]:.0f} km/h</div>'
                "</div>"
            )
        st.markdown(
            glass_html(tx("hourly_title", place=place["name"]), f'<div style="display:flex;overflow-x:auto;direction:ltr;">{cells}</div>'),
            unsafe_allow_html=True,
        )

    # ---- 6. Mask aur sehat
    st.markdown(glass_html(tx("sec_mask"), f"<div>{pick(cat['mask'])}</div>"), unsafe_allow_html=True)

    st.markdown(f"**{tx('sec_health')}**")
    cols = st.columns(2)
    for i in range(4):
        cols[i % 2].markdown(
            glass_html(
                f"{WHO_ICONS[i]} {tx('who' + str(i))}",
                f"<div>{pick(cat['adv'][i])}</div>",
            ),
            unsafe_allow_html=True,
        )

    # ---- 7. Sensor notes
    if len(near) == 1 and m is not None:
        s = near[0]
        st.caption(tx("one_sensor", v=s["pm25"], age=s["age_hours"]))
    elif not near:
        st.caption(tx("model_note"))

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


# ------------------------------------------------------------------ TAB 2: RANKING
def render_ranking():
    st.subheader(tx("rank_title"))
    st.caption(tx("rank_note"))
    rows = []
    for name, (la, lo) in list(SINDH_CITIES.items())[:20]:
        m = fetch_model_aqi(la, lo)
        if m is not None:
            rows.append((name, m["aqi"], m.get("temp")))
    if not rows:
        st.info(tx("no_data"))
        return
    rows.sort(key=lambda r: r[1])
    body = ""
    for i, (name, aqi, temp) in enumerate(rows, 1):
        c = get_category(aqi)
        temp_txt = "--" if temp is None else f"{round(temp)}°"
        body += (
            '<div style="display:flex;justify-content:space-between;align-items:center;'
            'padding:10px 4px;border-bottom:1px solid rgba(255,255,255,.15);">'
            f'<span><b>{i}. {name}</b></span>'
            f'<span>{temp_txt}</span>'
            f'<span style="background:{c["color"]};color:{c["text"]};padding:3px 12px;'
            f'border-radius:999px;font-weight:700;">{aqi} · {pick(c["name"])}</span>'
            "</div>"
        )
    st.markdown(glass_html("", body), unsafe_allow_html=True)
    st.caption(tx("rank_bottom"))


# ------------------------------------------------------------------ TAB 3: TRENDS
def render_trends(default_city):
    city_list = list(SINDH_CITIES.keys())
    default_idx = city_list.index(default_city) if default_city in city_list else 0

    city_name = st.selectbox(tx("trend_select"), city_list, index=default_idx, key="trend_city")
    lat, lon = SINDH_CITIES[city_name]
    try:
        hourly = get_hourly(lat, lon)
    except Exception:
        st.info(tx("load_err"))
        return
    st.subheader(tx("trend72", city=city_name))
    hr = hourly.tail(72).copy()
    hr["time"] = hr["time"] + pd.Timedelta(hours=5)
    last24 = hr.tail(24)
    best_row = last24.loc[last24["us_aqi"].idxmin()]
    worst_row = last24.loc[last24["us_aqi"].idxmax()]
    b1, b2 = st.columns(2)
    b1.success(f"{tx('cleanest')}: {best_row['time'].strftime('%I:%M %p')} (AQI {best_row['us_aqi']:.0f})")
    b2.error(f"{tx('peak')}: {worst_row['time'].strftime('%I:%M %p')} (AQI {worst_row['us_aqi']:.0f})")
    st.altair_chart(line_chart(hr[["time", "us_aqi"]].rename(columns={"us_aqi": "Hourly AQI"}), "time"))
    st.caption(tx("tz"))

    st.subheader(tx("trend30", city=city_name))
    daily = hourly.set_index("time")["us_aqi"].resample("D").mean()
    dd = daily.tail(30).rename("Daily avg AQI").reset_index()
    st.altair_chart(line_chart(dd, "time"))


# ------------------------------------------------------------------ TAB 4: ABOUT
def render_about():
    st.subheader(tx("about_title"))
    st.markdown(
        glass_html("", f"<div style='font-size:15px;line-height:1.7;'>{tx('about_body')}</div>"),
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ PAGE
st.title(tx("title"))
st.caption(tx("subtitle"))

api_key = get_openaq_key()
if not api_key:
    st.caption(tx("no_key"))

default_city, is_gps = get_user_sindh_location()

t_search, t_rank, t_trend, t_about = st.tabs(
    [tx("tab_sindh"), tx("tab_rank"), tx("tab_trend"), tx("tab_about")]
)
with t_search:
    render_search(api_key, default_city, is_gps)
with t_rank:
    render_ranking()
with t_trend:
    render_trends(default_city)
with t_about:
    render_about()