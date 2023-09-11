import log
import os
import requests
from fastapi import APIRouter

logger = log.setup_logger("core.location")
router = APIRouter(
     prefix="/location"
)
openweather_URL: str = "http://api.openweathermap.org/geo/1.0/direct?q={}&limit=1&appid={}"

class Location():
    name: str
    latitude: float
    longitude: float

    def __init__(self, name: str, latitude: float, longitude: float):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

def get_geolocation(place: str) -> list:
        url = openweather_URL.format(place, os.getenv("OPENWEATHER_API_KEY"))
        response = requests.get(url).json()
        return Location(place, float(response[0]["lat"]), float(response[0]["lon"]))