import os
import requests
import json

def get_weather(location: str = None, **kwargs) -> str:
    """
    Fetches the current weather and forecast for a given location.
    If OPENWEATHER_API_KEY is configured, uses OpenWeatherMap API.
    Otherwise, uses the free, no-key service wttr.in.
    """
    if not location:
        location = kwargs.get("city") or kwargs.get("query") or kwargs.get("q")
        
    if not location or not str(location).strip():
        return "Error: 'location' argument is required for get_weather. Please specify the city or location name, e.g., {'location': 'London'}."
        
    location = str(location).strip()
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if api_key and api_key.strip():
        try:
            # Query OpenWeatherMap current weather API
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                weather_desc = data["weather"][0]["description"]
                humidity = data["main"]["humidity"]
                wind = data["wind"]["speed"]
                
                res = (
                    f"Weather in {location.capitalize()} (via OpenWeatherMap):\n"
                    f"Temperature: {temp}°C (Feels like {feels_like}°C)\n"
                    f"Conditions: {weather_desc.capitalize()}\n"
                    f"Humidity: {humidity}%\n"
                    f"Wind Speed: {wind} m/s\n"
                )
                return res
            else:
                print(f"[Warning] OpenWeatherMap returned status {r.status_code}. Falling back to wttr.in.")
        except Exception as e:
            print(f"[Warning] OpenWeatherMap request failed: {e}. Falling back to wttr.in.")
            
    # Fallback: wttr.in
    try:
        url = f"https://wttr.in/{location}?format=j1"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            current = data["current_condition"][0]
            temp_c = current["temp_C"]
            feels_like_c = current["FeelsLikeC"]
            desc = current["weatherDesc"][0]["value"]
            humidity = current["humidity"]
            wind = current["windspeedKmph"]
            
            # Extract 1-day forecast info if available
            forecast_summary = ""
            if "weather" in data and len(data["weather"]) > 0:
                today = data["weather"][0]
                max_temp = today["maxtempC"]
                min_temp = today["mintempC"]
                forecast_summary = f"Forecast for today: Min {min_temp}°C, Max {max_temp}°C\n"
                
            res = (
                f"Weather in {location.capitalize()} (via wttr.in):\n"
                f"Temperature: {temp_c}°C (Feels like {feels_like_c}°C)\n"
                f"Conditions: {desc}\n"
                f"Humidity: {humidity}%\n"
                f"Wind Speed: {wind} km/h\n"
                f"{forecast_summary}"
            )
            return res
        else:
            return f"Error: wttr.in returned status code {r.status_code}."
    except Exception as e:
        return f"Error fetching weather for '{location}': {e}"
