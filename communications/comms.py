from dotenv import load_dotenv
from fastapi import FastAPI, encoders
from typing import Dict, List, Tuple
from util import setup_logger
from util.types import Message, Command, MessageChannel, User, Identifiers
import os
import re
import requests
import pyrogram
import json



load_dotenv() 
logger = setup_logger("comms")

class Comms():
    fastapp: FastAPI
    teleapp: pyrogram.Client
    tele_clients: List[str] = []

    def __init__(self) -> None:
        self.fastapp = FastAPI()
        self.teleapp = pyrogram.Client(
            "nexus_bot",
            api_id = os.environ.get("TELEGRAM_API_ID"),
            api_hash = os.environ.get("TELEGRAM_API_HASH"),
            bot_token = os.environ.get("TELEGRAM_API_TOKEN"),
        )

def parse_command(input: str) -> Command:
    match1 = re.match("^/(\S+)\s?(\w\S+)?", input)
    command = match1.group(1)
    parameter = match1.group(2)
    match2 = re.findall("-(\S+){1}\s(\S+){1}", input)
    options = {}
    for match in match2:
        options[match[0]] = match[1]
    if options == {}:
        options = None
    cmd = Command(name = command, parameter = parameter, options = options)
    print(cmd)
    return cmd

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

@comms.fastapp.post("/api/message_to_user")
async def message_to_user(message: Message):
    await comms.teleapp.send_message(comms.tele_clients[0], message.text)
    return {"message": "ok"}

#pyrogram

@comms.teleapp.on_message(pyrogram.filters.text)
async def tele_message(client, message:pyrogram.types.Message):
    #save conversation id
    print(message.chat.type)
    print(message.from_user.username)
    if message.chat.id not in comms.tele_clients:
        comms.tele_clients.append(message.chat.id)
    #handle text and command messages
    if message.text.startswith("/"):
        parsed_command = parse_command(message.text)
        inbound = Message(
            user = User(
                name = message.from_user.username,
                ids = Identifiers(
                    telegram = message.from_user.id
                )
            ),
            chat = message.chat.id,
            channel = MessageChannel.TELEGRAM,
            command = parsed_command,
            text = message.text
        )

        try:
            response = requests.post("http://localhost:" + os.getenv("CORE_PORT") + "/api/message_from_user", data = inbound.json())
            print(response)

        except ConnectionRefusedError:
            logger.warning("Error with request to core")
        
    else:
        inbound = Message(
            user = User(
                name = message.from_user.username,
                ids = Identifiers(
                    telegram = message.from_user.id
                )
            ),
            chat = message.chat.id,
            channel = MessageChannel.TELEGRAM,
            text = message.text 
        )

        try:
            response = requests.post("http://localhost:" + os.getenv("CORE_PORT") + "/api/message_from_user", data = inbound.json())
            print(response)

        except:
            logger.warning("Error with request to core")

    