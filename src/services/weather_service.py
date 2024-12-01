import logging
import requests
from typing import Optional, Dict, Any
from src.config import OPENWEATHER_API_KEY

logger = logging.getLogger(__name__)

class WeatherService:
    BASE_URL = "http://api.openweathermap.org/data/2.5"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_weather(self, location: str, units: str = 'metric') -> Optional[Dict[str, Any]]:
        """
        Get current weather for a location
        Args:
            location: City name or coordinates
            units: metric (Celsius) or imperial (Fahrenheit)
        """
        try:
            params = {
                'q': location,
                'appid': self.api_key,
                'units': units
            }
            
            response = requests.get(
                f"{self.BASE_URL}/weather",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed'],
                'location': data['name'],
                'country': data['sys']['country']
            }
            
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            return None
    
    def get_forecast(self, location: str, units: str = 'metric') -> Optional[Dict[str, Any]]:
        """Get 5-day weather forecast for a location"""
        try:
            params = {
                'q': location,
                'appid': self.api_key,
                'units': units
            }
            
            response = requests.get(
                f"{self.BASE_URL}/forecast",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            forecast_list = []
            
            # Group forecasts by day
            for item in data['list']:
                forecast_list.append({
                    'datetime': item['dt_txt'],
                    'temperature': item['main']['temp'],
                    'description': item['weather'][0]['description'],
                    'humidity': item['main']['humidity']
                })
            
            return {
                'location': data['city']['name'],
                'country': data['city']['country'],
                'forecast': forecast_list[:5]  # Return next 5 forecasts
            }
            
        except requests.RequestException as e:
            logger.error(f"Error fetching forecast data: {str(e)}")
            return None 