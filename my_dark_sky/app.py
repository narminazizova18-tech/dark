import os
from datetime import datetime

import requests
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

from models import WeatherCache, db

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///weather.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_LABELS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Heavy thunderstorm with hail",
}

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')


def weather_label(code):
    return WEATHER_LABELS.get(code, "Unknown")


def parse_date(date_value):
    if not date_value:
        return datetime.utcnow().date()
    return datetime.strptime(date_value, "%Y-%m-%d").date()


def build_daily_snapshot(target_date, payload, mode):
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        raise ValueError("Weather data is unavailable for the selected date.")

    day_rows = []
    for index, time_value in enumerate(times):
        if not time_value.startswith(target_date.isoformat()):
            continue
        day_rows.append({
            "time": time_value,
            "temp": hourly.get("temperature_2m", [None])[index],
            "humidity": hourly.get("relative_humidity_2m", [None])[index],
            "wind": hourly.get("wind_speed_10m", [None])[index],
            "code": hourly.get("weather_code", [None])[index],
        })

    if not day_rows:
        raise ValueError("No weather data found for the selected date.")

    selected = min(
        day_rows,
        key=lambda row: abs(datetime.fromisoformat(row["time"]).hour - 12)
    )

    return {
        "date": target_date.isoformat(),
        "mode": mode,
        "temperature": round(selected["temp"]) if selected["temp"] is not None else None,
        "description": weather_label(selected["code"]),
        "humidity": round(selected["humidity"]) if selected["humidity"] is not None else None,
        "wind": round(selected["wind"]) if selected["wind"] is not None else None,
        "high": round(max(row["temp"] for row in day_rows if row["temp"] is not None)),
        "low": round(min(row["temp"] for row in day_rows if row["temp"] is not None)),
    }


def fetch_daily_weather(lat, lon, target_date):
    today = datetime.utcnow().date()

    base_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "timezone": "auto",
    }

    if target_date < today:
        params = {
            **base_params,
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
        }
        response = requests.get(ARCHIVE_URL, params=params, timeout=15)
        response.raise_for_status()
        return build_daily_snapshot(target_date, response.json(), "historical")

    params = {
        **base_params,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "forecast_days": 14,
    }
    response = requests.get(FORECAST_URL, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()

    if target_date == today and payload.get("current"):
        current = payload["current"]
        daily = payload.get("daily", {})
        day_index = daily.get("time", []).index(target_date.isoformat())
        return {
            "date": target_date.isoformat(),
            "mode": "current",
            "temperature": round(current["temperature_2m"]),
            "description": weather_label(current["weather_code"]),
            "humidity": round(current["relative_humidity_2m"]),
            "wind": round(current["wind_speed_10m"]),
            "high": round(daily["temperature_2m_max"][day_index]),
            "low": round(daily["temperature_2m_min"][day_index]),
        }

    return build_daily_snapshot(target_date, payload, "forecast")


def fetch_forecast(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "forecast_days": 7,
    }
    response = requests.get(FORECAST_URL, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json().get("daily", {})

    forecast_days = []
    for index, day in enumerate(payload.get("time", [])):
        forecast_days.append({
            "date": day,
            "high": round(payload["temperature_2m_max"][index]),
            "low": round(payload["temperature_2m_min"][index]),
            "description": weather_label(payload["weather_code"][index]),
        })

    return forecast_days


@app.route('/api/weather')
def get_weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    selected_date = request.args.get('date')
    if not lat or not lon:
        return jsonify({"error": "Missing coordinates"}), 400

    try:
        target_date = parse_date(selected_date)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    cache_key = f"{lat}_{lon}_{target_date.isoformat()}"
    cached = WeatherCache.query.filter_by(key=cache_key).first()

    if cached and not cached.is_expired():
        return jsonify(cached.data)

    try:
        selected = fetch_daily_weather(lat, lon, target_date)
        forecast = fetch_forecast(lat, lon)
        res_payload = {"selected": selected, "forecast": forecast}

        if cached:
            cached.data = res_payload
            cached.timestamp = datetime.utcnow()
        else:
            db.session.add(WeatherCache(key=cache_key, data=res_payload))
        
        db.session.commit()
        return jsonify(res_payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search')
def search():
    q = request.args.get('q')
    if not q:
        return jsonify([])

    params = {
        "name": q,
        "count": 5,
        "language": "en",
        "format": "json",
    }
    response = requests.get(GEOCODING_URL, params=params, timeout=15)
    response.raise_for_status()
    results = response.json().get("results", [])

    locations = [{
        "name": item["name"],
        "country": item.get("country", ""),
        "admin1": item.get("admin1", ""),
        "lat": item["latitude"],
        "lon": item["longitude"],
    } for item in results]

    return jsonify(locations)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 80))
    app.run(host='0.0.0.0', port=port, debug=True)
