from dotenv import load_dotenv
from fastapi import FastAPI
from typing import Dict, List
from nexutil.log import setup_logger
from nexutil import types
from nexutil.config import Config
import nexutil.inference as inf
import nexutil.database as db
from colorama import Fore
import uuid
import asyncio
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
    dbconnection = db.psycopg.Connection
    sources_id: List[types.Identifiers] = []
    users_id: List[types.Identifiers] = []
    id_table: Dict[str, List[types.Identifiers]] = {"users": [], "sources": []}
    tele_clients: List[str] = []
    _tele_action_loop: asyncio.Task

    def __init__(self) -> None:
        self.fastapp = FastAPI()
        self.teleapp = pyrogram.Client(
            "nexus_bot",
            api_id = os.environ.get("TELEGRAM_API_ID"),
            api_hash = os.environ.get("TELEGRAM_API_HASH"),
            bot_token = os.environ.get("TELEGRAM_API_TOKEN"),
        )
        self.httpx_client = httpx.AsyncClient()
        self.dbconnection = db.connect()

def parse_command(input: str) -> types.Command:
    match1 = re.match("^/(\S+)\s?(\w\S+)?", input)
    command = match1.group(1)
    parameter = match1.group(2)
    match2 = re.findall("-(\S+){1}\s(\S+){1}", input)
    options = {}
    for match in match2:
        options[match[0]] = match[1]
    if options == {}:
        options = None
    cmd = types.Command(name = command, parameter = parameter, options = options)
    print(cmd)
    return cmd

comms = Comms()

async def loop_tele_action(action: str, chat: str):
    while True:
        if action == "typing":
            await comms.teleapp.send_chat_action(chat, pyrogram.enums.ChatAction.TYPING)
        await asyncio.sleep(3)

#FastAPI 

@comms.fastapp.on_event("startup")
async def startup_routine():
    await comms.teleapp.start()
    db.gen_comms_tables(comms.dbconnection)
    logger.info("Comms service finished loading")

@comms.fastapp.on_event("shutdown")
async def shutdown_routine():
    await comms.teleapp.stop()
    await comms.httpx_client.aclose()
    logger.info("comms service shutdown complete")

@comms.fastapp.get("/status")
async def root():
    return {"message": "Nexus is up and running"}

#endpoint to repond with a message to a user
@comms.fastapp.post("/api/message_to_user/{recipient}")
async def message_to_user(message: types.Message, recipient: str):
    logger.debug("incoming message for chat: {}".format(message.conversation_id))
    exchange = db.get_exchange(comms.dbconnection, recipient)
    if exchange.channel == types.MessageChannel.TELEGRAM:
        chat_id = db.get_user_internal(comms.dbconnection, recipient)
        await comms.teleapp.send_message(chat_id.telegram, message.text)
    return {"message": "ok"}

#send telegram chat actions to users
@comms.fastapp.get("/api/action_to_user/{action}/{recipient}")
async def action_to_user(action: str, recipient: str):
    logger.debug("sending action {} for user: {}".format(action, recipient))
    exchange = db.get_exchange(comms.dbconnection, recipient)
    if exchange.channel == types.MessageChannel.TELEGRAM:
        chat_id = db.get_user_internal(comms.dbconnection, recipient) 
        if action == "cancel" and comms._tele_action_loop != None:
            await comms.teleapp.send_chat_action(chat_id.telegram, pyrogram.enums.ChatAction.CANCEL)
            comms._tele_action_loop.cancel()
            comms._tele_action_loop = None
        else:
            comms._tele_action_loop = asyncio.create_task(loop_tele_action(action, chat_id.telegram))
    return {"message": "ok"}

#pyrogram

@comms.teleapp.on_message()
async def tele_message(client, message:pyrogram.types.Message):

    
    logger.info("incoming message from telegram user: {}, id: {}".format(message.from_user.username, message.chat.id))
    #get internal user id, user and create new entry if necessary
    user = db.get_user_tg(comms.dbconnection, message.chat.id)
    if user == None:
        user = types.Identifiers(
            internal = str(uuid.uuid4()),
            telegram = message.from_user.id,
            discord = None,
            username = message.from_user.username
        )
        
        db.add_user(comms.dbconnection, user)

    #get exchange id
    exchange = db.get_exchange(comms.dbconnection, user.internal)
    if exchange == None:
        exchange = types.Exchange(
            id = str(uuid.uuid4()),
            channel = types.MessageChannel.TELEGRAM,
            concluded = False
        )
        db.add_exchange(comms.dbconnection, exchange)

    inbound = types.Message(
        id = str(uuid.uuid4()),
        exchange = exchange,
        conversation_id = str(message.chat.id),
        from_user = user,
        datetime = message.date,
        channel = types.MessageChannel.TELEGRAM,
        command = None,
        text = None,
        image = None,
        video = None,
        audio = None
    )

    
    #handle text and command messages    
    if message.text != None and message.text.startswith("/"):
        inbound.command = parse_command(message.text)
        inbound.text = message.text  
    elif message.text != None:
        inbound.text = message.text

    #handle voice messages
    if message.voice != None:
        voice = await message.download(in_memory=True)
        tscript = await inf.transcribe_audio(comms.httpx_client, voice)
        inbound.text = tscript
        

    db.add_message(comms.dbconnection, inbound)

    try:
        response = await comms.httpx_client.post("http://localhost:" + str(config.core_port) + "/api/message_from_user", data = inbound.json(), timeout = 30)
    except ConnectionRefusedError:
        logger.warning("Error with request to core")