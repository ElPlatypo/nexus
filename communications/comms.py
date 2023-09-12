from dotenv import load_dotenv
from fastapi import FastAPI
from typing import Dict, List
from nexutil.log import setup_logger
from nexutil.types import Message, Command, MessageChannel, User, Identifiers
from nexutil.config import Config
from colorama import Fore
import uuid
import json
import httpx
import os
import re
import pyrogram


load_dotenv() 
logger = setup_logger("comms")
config = Config()

class Comms():
    fastapp: FastAPI
    teleapp: pyrogram.Client
    httpx_client: httpx.AsyncClient
    sources_id: List[Identifiers] = []
    users_id: List[Identifiers] = []
    id_table: Dict[str, List[Identifiers]] = {"users": [], "sources": []}
    tele_clients: List[str] = []

    def __init__(self) -> None:
        self.fastapp = FastAPI()
        self.teleapp = pyrogram.Client(
            "nexus_bot",
            api_id = os.environ.get("TELEGRAM_API_ID"),
            api_hash = os.environ.get("TELEGRAM_API_HASH"),
            bot_token = os.environ.get("TELEGRAM_API_TOKEN"),
        )
        self.httpx_client = httpx.AsyncClient()

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

    logger.info("Comms service finished loading")

@comms.fastapp.on_event("shutdown")
async def shutdown_routine():
    await comms.teleapp.stop()
    await comms.httpx_client.aclose()
    logger.info("comms service shutdown complete")

@comms.fastapp.get("/status")
async def root():
    return {"message": "Nexus is up and running"}

@comms.fastapp.post("/api/message_to_user")
async def message_to_user(message: Message):
    logger.debug("incoming message for chat: {}".format(message.chat))
    if message.channel == MessageChannel.TELEGRAM:
        for source in comms.sources_id:
            print("awef", source.internal, message.chat)
            if source.internal == message.chat:
                print("awef")
                tele_chat = source.telegram
    await comms.teleapp.send_message(tele_chat, message.text)
    return {"message": "ok"}

#pyrogram

@comms.teleapp.on_message(pyrogram.filters.text)
async def tele_message(client, message:pyrogram.types.Message):
    #get internal user id, user and create new entry if necessary
    logger.info("incoming message from telegram user: {}".format(message.from_user.username))
    source_id = None
    try:
        response = await comms.httpx_client.get("http://localhost:" + str(config.database_port) + "/api/get_user_from_tg/{}".format(message.chat.id))
        if json.load(response)["internal_id"] == "missing":
            new_id = str(uuid.uuid4())
            new_identifier = Identifiers(
                internal = new_id,
                telegram = str(message.chat.id)
            )
            source_id = new_id
            try:
                response = await comms.httpx_client.post("http://localhost:" + str(config.database_port) + "/api/add_user", data = new_identifier)
            except httpx.ConnectError:
                logger.warning("Error creating new user in db")
        else:
            source_id = json.load(response)["internal_id"]

    except httpx.ConnectError:
        logger.warning("Error fetching user info from db")
        return

    #handle text and command messages    
    if message.text.startswith("/"):
        parsed_command = parse_command(message.text)
        inbound = Message(
            id = str(uuid.uuid4()),
            user = User(
                name = message.from_user.username,
                id = "NOT IMPLEMENTED"
            ),
            chat = source_id,
            channel = MessageChannel.TELEGRAM,
            command = parsed_command,
            text = message.text
        )

        try:
            response = await comms.httpx_client.post("http://localhost:" + str(config.core_port) + "/api/message_from_user", data = inbound.json())
            print(response)

        except ConnectionRefusedError:
            logger.warning("Error with request to core")
        
    else:
        inbound = Message(
            id = str(uuid.uuid4()),
            user = User(
                name = message.from_user.username,
                id = "NOT IMPLEMENTED"
            ),
            chat = source_id,
            channel = MessageChannel.TELEGRAM,
            text = message.text 
        )

        try:
            response = await comms.httpx_client.post("http://localhost:" + str(config.core_port) + "/api/message_from_user", data = inbound.json())
            print(response)

        except:
            logger.warning("Error with request to core")

    