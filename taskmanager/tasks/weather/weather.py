import asyncio
from nexutil.types import Task
from typing import Tuple, Dict, Any
from dotenv import load_dotenv
import requests
import os
from typing import Optional


WEATHER_FROM_COORD_URL: str = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}"
load_dotenv()

async def parse_location(loc: str) -> Tuple[float, float]:
    return (420, 69)

async def get_weather(lat, lon) -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = WEATHER_FROM_COORD_URL.format(lat, lon, api_key)
    wtr_response = requests.get(url).json()
    reply = (
        "Current weather in " + 
        str(wtr_response["name"]) + ":\n" + 
        str(wtr_response["weather"][0]["main"]) + "\n"
        "Temperature:\n" +
        str(round(wtr_response["main"]["temp"] - 273.15, 2)) + "\n"
        "Humidity:\n" +
        str(wtr_response["main"]["humidity"]) + "%"
    )
    return reply

class Weather(Task):
    #parent class fields
    name: str = "weather"
    description: str = "get weather info from specific coordinates or city names"
    worker_: Optional[asyncio.Task] = None
    #own fields
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    

        
    def cmd_setup(self, parameter: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> None:
        self.location = parameter
        if options != None:
            self.latitude = options["latitude"]
            self.longitude = options["longitude"]

    async def worker(self, state: Tuple[str, Dict[str, str]]):
        if state[0] == "begin":
            if self.location is not None:
                self.latitude, self.longitude = await parse_location(self.location)
            if self.latitude is not None and self.longitude is not None:
                forecast = await get_weather(self.latitude, self.longitude)
                await self.respond(text = forecast, final = True)
            else:
                new_state = ("awaiting city name")
                await self.respond(text = "please specify the city")