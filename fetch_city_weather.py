import requests
import pandas as pd

AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_city(name, lat, lon, start="2024-01-01", end="2026-11-14"):
    # 1) AQI (pm2.5, pm10, us_aqi)
    aq = requests.get(AQ_URL, params={
        "latitude": lat,
        "longitude": lon,
        "hourly": "us_aqi,pm2_5,pm10",
        "start_date": start,
        "end_date": end,
        "timezone": "Asia/Karachi",
    }, timeout=120).json()
    aq_df = pd.DataFrame(aq["hourly"])

    # 2) Weather history (sirf past data, future leak nahi)
    wx = requests.get(ARCHIVE_URL, params={
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation,surface_pressure,cloud_cover",
        "start_date": start,
        "end_date": end,
        "timezone": "Asia/Karachi",
    }, timeout=120).json()
    wx_df = pd.DataFrame(wx["hourly"])

    # 3) Dono ko time ke hisaab se jod do
    df = aq_df.merge(wx_df, on="time", how="inner")
    df["time"] = pd.to_datetime(df["time"])

    fname = f"data_{name.lower().replace(' ', '_')}.csv"
    df.to_csv(fname, index=False)
    return fname, df


if __name__ == "__main__":
    fname, df = fetch_city("Mirpur Khas", 25.5276, 69.0125)
    print("File:", fname)
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print("Missing us_aqi:", df["us_aqi"].isna().sum())
    print("Missing temperature_2m:", df["temperature_2m"].isna().sum())
    print(df.head(3))