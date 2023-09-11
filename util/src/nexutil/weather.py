import modules.logging as log
from modules.location import Location
import requests
import os

logger = log.setup_logger("core.weather")

openweather_URL: str = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}"

def get_weather(place: Location) -> dict:
    response = requests.get(openweather_URL.format(
        place.latitude, 
        place.longitude, 
        os.getenv("OPENWEATHER_API_KEY")
    )).json()

    return response