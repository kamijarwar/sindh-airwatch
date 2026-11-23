# sindh-airwatch
# 🌤️ Sindh AirWatch — Hyper-Local Air Quality & ML Forecasting Platform

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.125-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Scikit-Learn](https://img.shields.io/badge/ML-Random_Forest-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Languages](https://img.shields.io/badge/Languages-Sindhi_%7C_Urdu_%7C_Roman_Urdu_%7C_English-0f766e?style=for-the-badge)

**Sindh AirWatch** is an end-to-end climate-tech and machine learning web application built to deliver real-time Air Quality Index (US AQI), live weather telemetry, and next-day AI pollution forecasts across **Sindh, Pakistan** — accessible to everyday citizens in **Sindhi (`سنڌي`)**, **Urdu (`اردو`)**, **Roman Urdu**, and **English**.

---

## 🎯 The Problem & Vision

Air pollution across Sindh (from industrial Karachi to agricultural and desert districts like Nawabshah, Sukkur, Mirpur Khas, and Mithi) poses a daily health risk. However, existing global air quality apps suffer from three major gaps:
1. **Language Barrier:** Almost all platforms are English-only, leaving millions of Sindhi and Urdu speakers without actionable health guidance.
2. **Sensor Deserts:** Ground sensors exist mostly in Karachi, leaving interior Sindh districts blind to real-time air quality.
3. **Raw Numbers Without Guidance:** Showing "AQI 145" does not tell a parent, motorcyclist, or asthma patient what immediate action to take.

**Sindh AirWatch solves all three** by combining live ground sensors, satellite telemetry, custom local Random Forest ML models, and native RTL localization into a fast, weather-grade interface.

---

## ✨ Key Features

- **🌐 4-Language Native Localization (Full RTL & LTR):** Instant switching between **Urdu (`اردو`)**, **Sindhi (`سنڌي`)**, **Roman Urdu**, and **English** with automatic right-to-left layout adaptation.
- **🤖 Hybrid Data + Local ML Engine:**
  - Pulls live ground-level PM2.5 readings from **OpenAQ** stations when available.
  - Seamlessly fuses real-time satellite air quality and meteorology from **Open-Meteo** for complete Sindh coverage.
  - Predicts **Tomorrow's AQI** using **26 custom-trained Random Forest ML models** (`city_models/*.joblib`) tailored to Sindh's cities.
- **🩺 Actionable 4-Card Health Guidance:** Translates US AQI levels into clear, localized precautions for **Masks**, **Outdoor Exercise**, **Kids / Elderly / Asthma**, and **Home Ventilation**.
- **🏆 Live 20-City Sindh Ranking:** Real-time leaderboard ranking Sindh cities from cleanest to most polluted with one-click inspection.
- **📈 72-Hour & 30-Day Historical Trends:** Interactive SVG trend charts highlighting cleanest hours and peak pollution windows.
- **📍 1-Click Cities & Browser GPS:** Instant access to 18+ major Sindh cities or automatic nearest-city detection via geolocation.
- **🌌 Dynamic Ambient Sky & Glassmorphic UI:** Real-time day/night sky themes, animated clouds/stars/haze, and a semi-circle US AQI gauge.

---

## 🏗️ System Architecture

```text
┌─────────────────────────┐      ┌──────────────────────────┐
│   OpenAQ Ground API     │      │   Open-Meteo Satellite   │
│  (Live PM2.5 Sensors)   │      │  (AQI + Weather + 30d)   │
└────────────┬────────────┘      └────────────┬─────────────┘
             │                                │
             └───────────────┬────────────────┘
                             ▼
             ┌───────────────────────────────┐
             │       FastAPI Backend         │
             │  • US EPA PM2.5 → AQI Engine  │
             │  • 26 Random Forest Models    │
             │  • Fuzzy Sindh Place Search   │
             └───────────────┬───────────────┘
                             │ REST JSON (/api/*)
                             ▼
             ┌───────────────────────────────┐
             │     React + Vite Frontend     │
             │  • 4-Language RTL/LTR Engine  │
             │  • Dynamic Sky & Gauge UI     │
             └───────────────────────────────┘
```

---

## 🏙️ Trained ML Model Coverage (26 Locations)

`Karachi` • `Hyderabad` • `Sukkur` • `Larkana` • `Mirpur Khas` • `Nawabshah` • `Jacobabad` • `Khairpur` • `Dadu` • `Thatta` • `Badin` • `Sanghar` • `Shikarpur` • `Ghotki` • `Jamshoro` • `Umerkot` • `Mithi` • `Tando Allahyar` • `Tando Adam` • `Tando Muhammad Khan` • `Kotri` • `Matiari` • `Sehwan` • `Chhor` • `Kandhkot` • `Kashmore`

---

## 🚀 Quick Local Setup

### 1. Start the FastAPI Backend
```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

### 2. Start the React Frontend
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 👨‍💻 Author

**Kamran Ali Jarwar (Kami Jarwar)**  
*Information Technology & Machine Learning Developer — Sindh, Pakistan*
