from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "b478d903f6307a5002415b4fa6875097"

@app.get("/weather")
def get_weather(city: str = None, lat: float = None, lon: float = None):
    """
    Get current weather, 12-hour forecast, and alerts.
    Accepts either city=<city_name> OR lat=<latitude>&lon=<longitude>
    """
    # Determine API URL for current weather
    if city:
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    elif lat is not None and lon is not None:
        current_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    else:
        raise HTTPException(status_code=400, detail="Provide city name or coordinates")

    response = requests.get(current_url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="City not found or API error")
    
    data = response.json()
    lat = data.get("coord", {}).get("lat")
    lon = data.get("coord", {}).get("lon")
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Coordinates not found")

    # 12-hour forecast
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    forecast_response = requests.get(forecast_url)
    if forecast_response.status_code != 200:
        raise HTTPException(status_code=forecast_response.status_code, detail="Error fetching forecast")
    
    forecast_data = forecast_response.json()
    hourly_forecast = []
    for hour in forecast_data.get("list", [])[:12]:
        hourly_forecast.append({
            "time": hour["dt"] * 1000,  # JS timestamp
            "temperature": hour["main"]["temp"],
            "weather": hour["weather"][0]["description"],
            "icon": f"https://openweathermap.org/img/wn/{hour['weather'][0]['icon']}@2x.png"
        })

    # Fetch weather alerts using One Call API
    alerts = []
    onecall_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,daily&appid={API_KEY}&units=metric"
    onecall_response = requests.get(onecall_url)
    if onecall_response.status_code == 200:
        onecall_data = onecall_response.json()
        if "alerts" in onecall_data:
            for alert in onecall_data["alerts"]:
                alerts.append(f"{alert.get('event')}: {alert.get('description')}")

    result = {
        "city": data.get("name"),
        "country": data.get("sys", {}).get("country"),
        "temperature": data.get("main", {}).get("temp"),
        "weather": data.get("weather")[0]["description"] if data.get("weather") else None,
        "humidity": data.get("main", {}).get("humidity"),
        "wind_speed": data.get("wind", {}).get("speed"),
        "icon": f"https://openweathermap.org/img/wn/{data.get('weather')[0]['icon']}@2x.png" if data.get("weather") else None,
        "hourly_forecast": hourly_forecast,
        "alerts": alerts
    }

    return result
