from dotenv import load_dotenv
from util import log
from util import message
from taskmanager.manager import Task
import fastapi 
import json
from typing import Union, List, Dict, Any
import requests
import os

load_dotenv()

class Core:
    fastapp: fastapi.FastAPI
    manager_tasks: List[Task]

    def __init__(self):
        self.fastapp = fastapi.FastAPI()

    async def get_aviable_tasks(self) -> List[str]:
        response = requests.get("htpps://localhost:" + os.getenv("MANAGER_PORT") + "/tasks")
        print(response.text)

logger = log.setup_logger("core")

core = Core()

#FastAPI 

@core.fastapp.on_event("startup")
async def startup_routine():
    response = requests.get("http://localhost:" + os.getenv("MANAGER_PORT") + "/tasks")
    tasks = json.loads(response.text)
    core.manager_tasks = tasks["aviable tasks"]
    logger.info("core startup completed")

@core.fastapp.on_event("shutdown")
async def shutdown_routine():
    logger.info("core shutdown completed")

@core.fastapp.get("/status")
async def root():
    return {"message": "Nexus core up and running"}

#intermediary between comms input and taskmanager
@core.fastapp.post("/api/message_from_user")
async def message_from_user(inbound: Union[message.TextMessageModel, message.CommandMessageModel]):
    print(inbound)
    if inbound.type == message.MessageType.TEXT:
        logger.info("[User]: " + inbound.text)

    #if message is a command, instantiate the correct Task with values and send it to taskmanager
    elif inbound.type == message.MessageType.COMMAND:
        logger.info("[User]: Summoned command: " + inbound.command)
        for task in core.manager_tasks:
            if task["name"] == inbound.command:
                #copy task object and set values of copy
                new_task = task
                new_task["cmd"] = True
                new_task["cmd_parameter"] = inbound.parameter
                new_task["cmd_options"] = inbound.options
                response = requests.post("http://localhost:" + os.getenv("MANAGER_PORT") + "/api/run_task", data = json.dumps(new_task))
                print(json.dumps(new_task))
        
    return {"message": "ok"}

#intermediary between task output and comms out
@core.fastapp.post("/api/message_to_user")
async def message_to_user(inbound: message.TextMessageModel):

    #check message type
    if inbound.type == message.MessageType.TEXT:
        logger.info("[Nexus]: " + inbound.text)
        #pass payload to comms service
        response = requests.post("http://localhost:" + os.getenv("COMMS_PORT"), data = inbound)

    else:
        logger.error("Core coudnt handle message type while trying to reply to user")

    return {"message": "ok"}

#Pyrogram

#@core.teleapp.on_message(pyrogram.filters.regex("(\.hello)"))
#async def tele_hello(client, message:pyrogram.types.Message):
#    await message.reply("hello man!")
#
#@core.teleapp.on_message(pyrogram.filters.regex("(\.status)"))
#async def tele_status(client, message:pyrogram.types.Message):
#    await message.reply(core.status[0])
#
#@core.teleapp.on_message(pyrogram.filters.regex("(\.time)"))
#async def tele_time(client, message:pyrogram.types.Message):
#    await message.reply(core.get_time())
#
#@core.teleapp.on_message(pyrogram.filters.regex("(\.locations)"))
#async def tele_location(client, message:pyrogram.types.Message):
#    match:re.Match = re.match("(\.locations){1}\s?(-\w+)?\s?(\w+)?", message.text)
#    if match[2] is not None:
#        if match[2] == "-sethome":
#            print(match[3])
#            location = loc.get_geolocation(match[3])
#            core.locations["home"] = loc.Location(match[3], location[0], location[1])
#            await message.reply("Added {} to locations".format(match[3]))
#
#        if match[2] == "-set":
#            location = loc.get_geolocation(match[3])
#            core.locations[match[3]] = loc.Location(match[3], location[0], location[1])
#            await message.reply("Added {} to locations".format(match[3]))
#
#        if match[2] == "-get":
#
#            await message.reply(
#                "Here are the placed i saved: \n" + 
#                str([place for place in core.locations.values()])
#            )
#    
#
#@core.teleapp.on_message(pyrogram.filters.regex("(\.weather)"))
#async def tele_weather(client, message:pyrogram.types.Message):
#    match = re.match("(\.weather){1}\s(-\w+)?\s?(\w+)?", message.text)
#    print(match[2])
#    if match[2] is None and match[3] is None:
#        location = core.locations["home"]
#
#    elif match[3] is not None and match[2] is None:
#        if not match[3].startswith("-"):
#            location = loc.get_geolocation(match[3])
#
#    forecast = wtr.get_weather(location)
#    reply:str = (
#        "Current weather in " + 
#        str(forecast["name"]) + ":\n" + 
#        str(forecast["weather"][0]["main"]) + "\n"
#        "Temperature:\n" +
#        str(round(forecast["main"]["temp"] - 273.15, 2)) + "\n"
#        "Humidity:\n" +
#        str(forecast["main"]["humidity"]) + "%"
#        )
#
#    await message.reply(reply)


    #todo
    #il core deve instanziare degli oggetti Task che contengono un'astrazione di vari task possibili e lo passa
    #al submodule che sa come interpretarlo e usa le info contenute per eseguirlo
    #worth fare oggetto con sub-oggetti che ereditano