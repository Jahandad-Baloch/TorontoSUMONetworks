


""" 
1. Randomizing Environmental Parameters
1.1 Weather Conditions Integration
Data Source: Utilize Weather APIs (e.g., WeatherAPI) to fetch real-time and historical weather data for Toronto.
Implementation:
Data Fetching: Develop a script (weather_data_fetcher.py) to collect weather data corresponding to simulation timestamps.
Simulation Impact: Modify vehicle parameters (e.g., maximum speed, acceleration) and road conditions based on weather (rain, snow, fog).
Configuration: Update simulation_config.yaml to include weather-related parameters.
"""


# Free weather APIs: OpenWeatherMap, WeatherAPI, AccuWeather
# For this project first try: WeatherAPI
# Command to store the API key: export WEATHER_API_KEY=<your API key>
# To access the API key: os.getenv('WEATHER_API_KEY')




""" 
Request
Request URL
Request to WeatherAPI.com API consists of base url and API method. You can make both HTTP or HTTPS request to our API.

Base URL: http://api.weatherapi.com/v1

API	API Method
Current weather	/current.json or /current.xml
Forecast	/forecast.json or /forecast.xml
Search or Autocomplete	/search.json or /search.xml
History	/history.json or /history.xml
Alerts	/alerts.json or /alerts.xml
Marine	/marine.json or /marine.xml
Future	/future.json or /future.xml
Time Zone	/timezone.json or /timezone.xml
Sports	/sports.json or /sports.xml
Astronomy	/astronomy.json or /astronomy.xml
IP Lookup	/ip.json or /ip.xml


Change Fields
By default we return all weather fields in response and that may not be ideal for your application. So provided below you could enable or disable the fields you would like to remove from your response.

If you wish any fields to not appear in the json response then simply uncheck that fields below and click on Save button at the bottom of screen.

Current Weather
last_updated_epoch
last_updated
temp_c
temp_f
is_day
text
icon
code
wind_mph
wind_kph
wind_degree
wind_dir
pressure_mb
pressure_in
precip_mm
precip_in
humidity
cloud
feelslike_c
feelslike_f
vis_km
vis_miles
gust_mph
gust_kph
uv
windchill_c
windchill_f
heatindex_c
heatindex_f
dewpoint_c
dewpoint_f
Forecast/Future/History Weather
forecastDay
date
date_epoch
Day
maxtemp_c
maxtemp_f
mintemp_c
mintemp_f
avgtemp_c
avgtemp_f
maxwind_mph
maxwind_kph
totalprecip_mm
totalprecip_in
avgvis_km
avgvis_miles
avghumidity
text
icon
code
daily_will_it_rain
daily_will_it_snow
daily_chance_of_rain
daily_chance_of_snow
uv
totalsnow_cm

"""


""" 


APIs Relevant to our project:
1. Current Weather Data (Real-time)
2. Forecast Weather Data (Future)
3. History Weather Data (Past)
4. Alerts (Weather Alerts)

Fields to consider:
1. Current Weather Data
- temp_c: Temperature in Celsius
- temp_f: Temperature in Fahrenheit
- wind_kph: Wind speed in km/h
- wind_degree: Wind direction in degrees
- wind_dir: Wind direction as 16 point compass 
- pressure_mb: Pressure in millibars
- precip_mm: Precipitation in mm
- humidity: Humidity in percentage
- cloud: Cloud cover in percentage
- uv: UV index (not relevant for simulation)
- visibility_km: Visibility in km
- gust_kph: Wind gust in km/h 
- feelslike_c: Feels like temperature in Celsius
- dewpoint_c: Dew point in Celsius
- windchill_c: Wind chill in Celsius
- heatindex_c: Heat index in Celsius

2. Forecast Weather Data
- maxtemp_c: Maximum temperature in Celsius
- mintemp_c: Minimum temperature in Celsius
- avgtemp_c: Average temperature in Celsius
- maxwind_kph: Maximum wind speed in km/h
- totalprecip_mm: Total precipitation in mm
- avgvis_km: Average visibility in km
- avghumidity: Average humidity in percentage
- uv: UV index
- totalsnow_cm: Total snowfall in cm
- daily_will_it_rain: Will it rain (Yes/No)
- daily_chance_of_rain: Chance of rain in percentage
- daily_will_it_snow: Will it snow (Yes/No)
- daily_chance_of_snow: Chance of snow in percentage

3. History Weather Data
- date: Date of the weather data
- maxtemp_c: Maximum temperature in Celsius
- mintemp_c: Minimum temperature in Celsius
- avgtemp_c: Average temperature in Celsius
- maxwind_kph: Maximum wind speed in km/h
- totalprecip_mm: Total precipitation in mm
- avgvis_km: Average visibility in km
- avghumidity: Average humidity in percentage
- uv: UV index
- totalsnow_cm: Total snowfall in cm
- daily_will_it_rain: Will it rain (Yes/No)
- daily_chance_of_rain: Chance of rain in percentage
- daily_will_it_snow: Will it snow (Yes/No)
- daily_chance_of_snow: Chance of snow in percentage

4. Alerts
- alert: Weather alert message
- alert_start: Alert start time
- alert_end: Alert end time
- alert_region: Alert region
- alert_severity: Alert severity
- alert_type: Alert type

Example API Request:
http://api.weatherapi.com/v1/current.json?key=YOUR_API_KEY&q=Toronto&aqi=no
http://api.weatherapi.com/v1/forecast.json?key=YOUR_API_KEY&q=Toronto&days=3&aqi=no&alerts=no
http://api.weatherapi.com/v1/history.json?key=YOUR_API_KEY&q=Toronto&dt=2021-10-01&aqi=no
http://api.weatherapi.com/v1/alerts.json?key=YOUR_API_KEY&q=Toronto

For specific areas in Toronto, use the latitude and longitude coordinates or postal code:
- q=43.65107,-79.347015 (latitude,longitude)
- q=Toronto (city name)
- q=postal_code (e.g., M5V 1J9)

Idea of a class to fetch weather data and integrate its aspects into the simulation to introduce complexities:
- WeatherDataFetcher
    - fetch_current_weather_data()
    - fetch_forecast_weather_data()
    - fetch_history_weather_data()
    - fetch_weather_alerts()
    - update_simulation_config()
    - modify_vehicle_parameters()
    - modify_road_conditions()
    - update_simulation_timestamps()
    - update_simulation_weather_data()
    - update_simulation_traffic_data()
    - update_simulation_network_data()
Other methods that may be useful:
- get_weather_data()
- process_weather_data()
- save_weather_data()
- log_weather_data()

"""


from scripts.common.network_base import NetworkBase
from scripts.common.utils import FileIO
from scripts.traffic_data_processing.network_parser import NetworkParser

# imports for Weather API
import requests
import json
import datetime
import os

""" 
This script is used to fetch weather data for the simulation and update the simulation configuration.
path: scripts/introduce_complexities/weather_data_fetcher.py
"""

# Weather API URL
BASE_URL = "http://api.weatherapi.com/v1"
API_KEY = os.getenv('WEATHER_API_KEY')

# Weather API Endpoints
CURRENT_WEATHER = "/current.json"
FORECAST_WEATHER = "/forecast.json"
HISTORY_WEATHER = "/history.json"
ALERTS = "/alerts.json"

class WeatherDataFetcher(NetworkBase):
    def __init__(self, config_file: str):
        super().__init__(config_file)
        self.prepare_directories()
        self.network_parser = NetworkParser(self.net_file, self.logger)
        self.network_parser.load_network()

    def fetch_current_weather_data(self, location: str = "Toronto"):
        """
        Fetch the current weather data for the specified location.
        """
        url = f"{BASE_URL}{CURRENT_WEATHER}?key={API_KEY}&q={location}&aqi=no"
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
            current_weather = weather_data['current']
            self.logger.info("Current weather data fetched successfully.")
            return current_weather
        else:
            self.logger.error("Failed to fetch current weather data.")
            return None

    def fetch_forecast_weather_data(self, location: str = "Toronto", days: int = 3):
        """
        Fetch the forecast weather data for the specified location.
        """
        url = f"{BASE_URL}{FORECAST_WEATHER}?key={API_KEY}&q={location}&days={days}&aqi=no&alerts=no"
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
            forecast_weather = weather_data['forecast']['forecastday']
            self.logger.info("Forecast weather data fetched successfully.")
            return forecast_weather
        else:
            self.logger.error("Failed to fetch forecast weather data.")
            return None

    def fetch_history_weather_data(self, location: str = "Toronto", date: str = "2021-10-01"):
        """
        Fetch the history weather data for the specified location and date.
        """
        url = f"{BASE_URL}{HISTORY_WEATHER}?key={API_KEY}&q={location}&dt={date}&aqi=no"
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
            history_weather = weather_data['forecast']['forecastday']
            self.logger.info("History weather data fetched successfully.")
            return history_weather
        else:
            self.logger.error("Failed to fetch history weather data.")
            return None

    def fetch_weather_alerts(self, location: str = "Toronto"):
        """
        Fetch the weather alerts for the specified location.
        """
        url = f"{BASE_URL}{ALERTS}?key={API_KEY}&q={location}"
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
            alerts = weather_data['alerts']
            self.logger.info("Weather alerts fetched successfully.")
            return alerts
        else:
            self.logger.error("Failed to fetch weather alerts.")
            return None
        
    def update_simulation_config(self, config: dict, weather_data: dict):
        """
        Update the simulation configuration with the fetched weather data.
        """
        config['weather_data'] = weather_data
        FileIO.save_yaml(self.config_file, config)
        self.logger.info("Simulation configuration updated successfully.")


    def modify_vehicle_parameters(self, weather_data):
        # Extract relevant weather information
        condition = weather_data.get('condition', {}).get('text', '').lower()
        if 'rain' in condition or 'snow' in condition:
            # Reduce max speed and acceleration
            for veh_id in self.sumo_interface.vehicle.getIDList():
                current_max_speed = self.sumo_interface.vehicle.getMaxSpeed(veh_id)
                new_max_speed = current_max_speed * 0.8  # Example reduction
                self.sumo_interface.vehicle.setMaxSpeed(veh_id, new_max_speed)
                # Similarly adjust acceleration, deceleration, and sigma

    
    def modify_road_conditions(self, weather_data: dict):
        """
        Modify road conditions based on the fetched weather data.
        """
        # Modify road conditions based on weather data
        pass
    
    def update_simulation_timestamps(self, weather_data: dict):
        
        """
        Update the simulation timestamps based on the fetched weather data.
        """
        # Update simulation timestamps based on weather data
        pass
    
    def update_simulation_weather_data(self, weather_data: dict):
        """
        Update the simulation weather data based on the fetched weather data.
        """
        # Update simulation weather data based on weather data
        pass
    
    def update_simulation_traffic_data(self, weather_data: dict):
        """
        Update the simulation traffic data based on the fetched weather data.
        """
        # Update simulation traffic data based on weather data
        pass
    
    def update_simulation_network_data(self, weather_data: dict):
        """
        Update the simulation network data based on the fetched weather data.
        """
        # Update simulation network data based on weather data
        pass
    
    def fetch_weather_data(self, location: str = "Toronto"):
        """
        Fetch weather data for the specified location.
        """
        current_weather = self.fetch_current_weather_data(location)
        forecast_weather = self.fetch_forecast_weather_data(location)
        history_weather = self.fetch_history_weather_data(location)
        alerts = self.fetch_weather_alerts(location)
        return current_weather, forecast_weather, history_weather, alerts
    
    def process_weather_data(self, weather_data: dict):
        """
        Process the fetched weather data.
        """
        # Process the fetched weather data
        pass
    
    def save_weather_data(self, weather_data: dict):
        """
        Save the fetched weather data.
        """
        # Save the fetched weather data
        pass
    
    def log_weather_data(self, weather_data: dict):
        """
        Log the fetched weather data.
        """
        # Log the fetched weather data
        pass
    
    def fetch_and_update_weather_data(self, location: str = "Toronto"):
        """
        Fetch and update the weather data for the simulation.
        """
        weather_data = self.fetch_weather_data(location)
        self.process_weather_data(weather_data)
        self.save_weather_data(weather_data)
        self.log_weather_data(weather_data)
        self.update_simulation_config(self.config, weather_data)
        self.modify_vehicle_parameters(weather_data)
        self.modify_road_conditions(weather_data)
        self.update_simulation_timestamps(weather_data)
        self.update_simulation_weather_data(weather_data)
        self.update_simulation_traffic_data(weather_data)
        self.update_simulation_network_data(weather_data)
        self.logger.info("Weather data fetched and updated successfully.")
        return weather_data
    
    def run(self):
        """
        Run the weather data fetching and updating process.
        """
        self.fetch_and_update_weather_data()
        self.logger.info("End of weather data fetching and updating process.")
        
if __name__ == "__main__":
    weather_fetcher = WeatherDataFetcher("config/simulation_config.yaml")
    weather_fetcher.run()