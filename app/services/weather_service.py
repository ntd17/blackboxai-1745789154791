import requests
from flask import current_app
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json

class WeatherService:
    """Service for interacting with OpenWeatherMap API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    def get_forecast(self, location: Dict, start_date: datetime.date, days: int) -> Optional[Dict]:
        """
        Get weather forecast for a location
        
        Args:
            location: Dictionary containing location details (coordinates or city name)
            start_date: Start date for forecast
            days: Number of days to forecast
            
        Returns:
            dict: Weather forecast data if successful, None otherwise
        """
        try:
            # Extract coordinates from location
            if 'coordinates' in location:
                lat = location['coordinates']['lat']
                lon = location['coordinates']['lon']
            else:
                # Get coordinates from city name
                coords = self._get_coordinates(location.get('city'), location.get('country'))
                if not coords:
                    raise ValueError("Could not determine location coordinates")
                lat, lon = coords
            
            # Get forecast data
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'exclude': 'current,minutely,hourly,alerts'
            }
            
            response = requests.get(
                f"{self.base_url}/onecall",
                params=params
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Filter and process forecast data
            processed_data = self._process_forecast(
                data,
                start_date,
                days
            )
            
            return processed_data
            
        except Exception as e:
            current_app.logger.error(f"Weather forecast fetch failed: {str(e)}")
            return None
            
    def _get_coordinates(self, city: str, country: str = None) -> Optional[tuple]:
        """
        Get coordinates for a city
        
        Args:
            city: City name
            country: Country code (optional)
            
        Returns:
            tuple: (latitude, longitude) if found, None otherwise
        """
        try:
            params = {
                'q': f"{city},{country}" if country else city,
                'appid': self.api_key,
                'limit': 1
            }
            
            response = requests.get(
                "http://api.openweathermap.org/geo/1.0/direct",
                params=params
            )
            
            response.raise_for_status()
            results = response.json()
            
            if results:
                return (results[0]['lat'], results[0]['lon'])
            return None
            
        except Exception as e:
            current_app.logger.error(f"Geocoding failed: {str(e)}")
            return None
            
    def _process_forecast(self, data: Dict, start_date: datetime.date, days: int) -> Dict:
        """
        Process and filter forecast data
        
        Args:
            data: Raw forecast data
            start_date: Start date for forecast
            days: Number of days to include
            
        Returns:
            dict: Processed forecast data
        """
        daily_data = data.get('daily', [])
        
        # Filter days and extract relevant information
        processed_days = []
        end_date = start_date + timedelta(days=days)
        
        for day_data in daily_data[:days]:
            date = datetime.fromtimestamp(day_data['dt']).date()
            if start_date <= date < end_date:
                processed_days.append({
                    'date': date.isoformat(),
                    'temp': {
                        'min': day_data['temp']['min'],
                        'max': day_data['temp']['max'],
                        'day': day_data['temp']['day']
                    },
                    'humidity': day_data['humidity'],
                    'wind_speed': day_data['wind_speed'],
                    'rain_prob': day_data.get('pop', 0),  # Probability of precipitation
                    'rain_amount': day_data.get('rain', 0),  # Rain amount in mm
                    'weather': {
                        'main': day_data['weather'][0]['main'],
                        'description': day_data['weather'][0]['description'],
                        'icon': day_data['weather'][0]['icon']
                    }
                })
        
        # Calculate aggregate statistics
        total_rain_prob = sum(day['rain_prob'] for day in processed_days)
        total_rain_amount = sum(day['rain_amount'] for day in processed_days)
        avg_temp = sum(day['temp']['day'] for day in processed_days) / len(processed_days)
        
        return {
            'location': {
                'lat': data['lat'],
                'lon': data['lon']
            },
            'daily': processed_days,
            'summary': {
                'total_days': days,
                'avg_rain_probability': total_rain_prob / days,
                'total_rain_amount': total_rain_amount,
                'avg_temperature': avg_temp,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }
    
    def get_historical_data(self, location: Dict, date: datetime.date) -> Optional[Dict]:
        """
        Get historical weather data for a location
        
        Args:
            location: Dictionary containing location details
            date: Date to get historical data for
            
        Returns:
            dict: Historical weather data if successful, None otherwise
        """
        try:
            # Extract coordinates
            if 'coordinates' in location:
                lat = location['coordinates']['lat']
                lon = location['coordinates']['lon']
            else:
                coords = self._get_coordinates(location.get('city'), location.get('country'))
                if not coords:
                    raise ValueError("Could not determine location coordinates")
                lat, lon = coords
            
            # Convert date to Unix timestamp
            timestamp = int(datetime.combine(date, datetime.min.time()).timestamp())
            
            params = {
                'lat': lat,
                'lon': lon,
                'dt': timestamp,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(
                f"{self.base_url}/onecall/timemachine",
                params=params
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            current_app.logger.error(f"Historical weather data fetch failed: {str(e)}")
            return None
