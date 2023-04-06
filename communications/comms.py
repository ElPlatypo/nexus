from dotenv import load_dotenv
from fastapi import FastAPI, encoders
from typing import Dict, List, Tuple
from util import setup_logger
from util.message import *
import os
import requests
import pyrogram
import json



load_dotenv() 
logger = setup_logger("comms")

class Comms():
    fastapp: FastAPI
    teleapp: pyrogram.Client

    def __init__(self) -> None:
        self.fastapp = FastAPI()
        self.teleapp = pyrogram.Client(
            "nexus_bot",
            api_id = os.environ.get("TELEGRAM_API_ID"),
            api_hash = os.environ.get("TELEGRAM_API_HASH"),
            bot_token = os.environ.get("TELEGRAM_API_TOKEN"),
        )

def parse_command(input: str) -> Dict:

    if input.split(" ").__len__() == 1:
        return {"command": input[1:], "parameter": None, "options": None}
    
    elif input.split(" ").__len__() > 1:
        #select first word, and remove the "/"
        command = input.split(" ")[0][1:]
        #select up to first option, remove command and return the rest
        if input.split("-")[0].split(" ").__len__() > 1:
            parameter = input.split("-")[0].split(" ")[1]
        else:
            parameter = None
        #remove command, parameters and join back options
        options_str = "-".join(input.split("-")[1:])
        options = {}
        for option in options_str.split("-"):
            if option.split(" ").__len__() > 1:
                options[option.split(" ")[0]] = option.split(" ")[1]
        return {"command": command, "parameter": parameter, "options": options}

    else:
        logger.error("error parsing command")

comms = Comms()

#FastAPI 

@comms.fastapp.on_event("startup")
async def startup_routine():
    await comms.teleapp.start()
    logger.info("comms service startup complete")

@comms.fastapp.on_event("shutdown")
async def shutdown_routine():
    await comms.teleapp.stop()
    logger.info("comms service shutdown complete")

@comms.fastapp.get("/status")
async def root():
    return {"message": "Nexus is up and running"}

#pyrogram

@comms.teleapp.on_message(pyrogram.filters.text)
async def tele_message(client, message:pyrogram.types.Message):

    if message.text.startswith("/"):
        parsed_command = parse_command(message.text)
        print(parsed_command)
        inbound = CommandMessageModel(
            channel = Channel.TELEGRAM,
            type = MessageType.COMMAND,
            command = parsed_command["command"],
            parameter = parsed_command["parameter"],
            options = parsed_command["options"]
        )

        try:
            response = requests.post("http://localhost:" + os.getenv("CORE_PORT") + "/api/message_from_user", data = inbound.json())
            logger.info(response.text)

        except ConnectionRefusedError:
            logger.warning("Error with request to core")
        
    else:

        inbound = TextMessageModel(
            channel = Channel.TELEGRAM,
            type = MessageType.TEXT,
            text = message.text
        )

        try:
            response = requests.post("http://localhost:" + os.getenv("CORE_PORT") + "/api/message_from_user", data = inbound.json())
            logger.info(response)

        except:
            logger.warning("Error with request to core")

    