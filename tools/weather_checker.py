# REQUIREMENTS: requests
import requests

def get_weather(city_name: str) -> str:
    """
    Get current weather for a city using Open-Meteo (No API key required).
    """
    try:
        # 1. Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=5)
        geo_data = geo_res.json()
        
        if not geo_data.get("results"):
            return f"Could not find location '{city_name}'."
            
        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        name = location["name"]
        country = location.get("country", "")
        
        # 2. Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url, timeout=5)
        weather_data = weather_res.json()
        
        if "current_weather" not in weather_data:
            return "Could not retrieve weather data."
            
        current = weather_data["current_weather"]
        temp = current["temperature"]
        wind = current["windspeed"]
        
        return f"Weather in {name}, {country}:\nTemperature: {temp}°C\nWind Speed: {wind} km/h"
        
    except Exception as e:
        return f"Error checking weather: {str(e)}"
