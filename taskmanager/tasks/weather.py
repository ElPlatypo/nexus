import asyncio

from ..manager import Task
from util import message
from typing import Tuple, Dict
from dotenv import load_dotenv
import requests
import os
from typing import Optional

WEATHER_FROM_COORD_URL: str = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}"
load_dotenv()

async def parse_location(loc: str) -> Tuple[float, float]:
    return (420, 69)

async def get_weather(lon, lat) -> str:
    print("suus")
    api_key = os.getenv("OPENWEATHER_API_KEY")
    print("saaas")
    print(api_key)
    wtr_response = requests.get(WEATHER_FROM_COORD_URL.format(
        lat, 
        lon, 
        api_key
    )).json()
    print(wtr_response)
    print("sefe")
    reply = (
        "Current weather in " + 
        str(wtr_response["name"]) + ":\n" + 
        str(wtr_response["weather"][0]["main"]) + "\n"
        "Temperature:\n" +
        str(round(wtr_response["main"]["temp"] - 273.15, 2)) + "\n"
        "Humidity:\n" +
        str(wtr_response["main"]["humidity"]) + "%"
    )
    print("rgtght")
    return reply

class Weather(Task):

    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

    def __init__(self, location: str = None, longitude: float = None, latitude: float = None, **kwargs):
        super().__init__(
            name = "weather",
            description = "get weather info from specific coordinates or city names",
        )
        self.location = location
        self.longitude = longitude
        self.latitude = latitude

        
    def cmd_setup(self) -> None:
        if self.cmd_parameter is not None:
            self.location = self.cmd_parameter
        if "latitude" in self.cmd_options.keys():
            self.latitude = self.cmd_options["latitude"]
        if "longitude" in self.cmd_options.keys():
            self.longitude = self.cmd_options["longitude"]

    async def worker(self):
        if self.location is not None:
            self.latitude, self.longitude = await parse_location(self.location)
        if self.latitude is not None and self.longitude is not None:
            forecast = await get_weather(self.latitude, self.longitude)
            #await self.respond(forecast)
        #else:
            #await self.respond("you dind't give me any arguments!")
        print(forecast)

#class WeatherFromCoord(Task):
#    latitude: float
#    longitude: float
#    
#    def __init__(self) -> None:
#        super().__init__(
#            "weatherfromcoord",
#            "get current weather from openweather at the specified latitude and longitude"
#        )
#
#    async def worker(self, **kwargs) -> None:
#
#        wtr_response = await requests.get(WEATHER_FROM_COORD_URL.format(
#            self.latitude, 
#            self.longitude, 
#            os.getenv("OPENWEATHER_API_KEY")
#        )).json()
#
#        reply = (
#            "Current weather in " + 
#            str(wtr_response["name"]) + ":\n" + 
#            str(wtr_response["weather"][0]["main"]) + "\n"
#            "Temperature:\n" +
#            str(round(wtr_response["main"]["temp"] - 273.15, 2)) + "\n"
#            "Humidity:\n" +
#            str(wtr_response["main"]["humidity"]) + "%"
#        )
#
#        msg = message.TextMessage(
#            channel = message.Channel.TELEGRAM,
#            type = message.MessageType.TEXT,
#            text = reply
#        )
#
#        self._retval = msg