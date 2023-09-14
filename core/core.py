from dotenv import load_dotenv
from nexutil.log import setup_logger
from nexutil.types import Message, Command, Task, Exchange, MessageChannel, Identifiers
from nexutil.config import Config
import fastapi 
from fastapi import encoders
import uuid
from colorama import Fore
import httpx
import json
from typing import List, Dict, Any, Optional
import requests
import os

load_dotenv()
logger = setup_logger("core")
config = Config()

class Core:
    fastapp: fastapi.FastAPI
    httpx_client: httpx.AsyncClient
    manager_tasks: List[Task]
    
    def __init__(self):
        self.fastapp = fastapi.FastAPI()
        self.httpx_client = httpx.AsyncClient()

core = Core()

#add relevant info to message from task manager and start a new exchange if necessary
def handle_manager_message(inbound: Message, exchange: str) -> Message:
    conv_id = None
    channel = None
    for conv in core.conversations:
        for exc in conv.active_exchanges:
            if exc.id == exchange:
                conv_id = conv.id
                channel = exc.channel
    inbound.chat = conv_id
    inbound.channel = channel
    return inbound

#stores in memory the flow of the conversations
def handle_conv(inbound: Message, final: bool = False) -> str:
    exc_id = str(uuid.uuid4())
    for conv in core.conversations:
        if conv.id == inbound.chat:
            #check if there is an active exchange
            for exc in conv.active_exchanges:
                #since every conversation can have one active exchange per channel we can check that
                if inbound.channel == exc.channel:
                    exc.messages.append(inbound)
                    logger.debug("added message to exchange with id: " + Fore.WHITE + exc_id + Fore.CYAN + ", from conversation with id: " + Fore.WHITE + conv.id)
                    if final == True:
                        conv.active_exchanges.remove(exc)
                        conv.history.append(exc)
                    return exc.id
    
            conv.active_exchanges.append(
                Exchange(
                    id = exc_id,
                    channel = inbound.channel,
                    messages = [inbound]
                )
            )
            logger.debug("added message to new exchange with id: " + Fore.WHITE + exc_id + Fore.CYAN + ", from conversation with id: " + Fore.WHITE + conv.id)
            if final == True:
                conv.active_exchanges.remove(exc)
                conv.history.append(exc)
            return exc_id
            
    #if no conversation id found crate a new one
    new_conv = Conversation(
        id = inbound.chat,
        users = [inbound.user],
        active_exchanges = [
            Exchange(
                id = exc_id,
                channel = inbound.channel,
                messages = [inbound]
            ) 
        ],
    )
    core.conversations.append(new_conv)
    logger.debug("added message to new exchange with id: " + Fore.WHITE + exc_id + Fore.CYAN + ", from new conversation with id: " + Fore.WHITE + inbound.chat)
    if final == True:
        conv.active_exchanges.remove(exc)
        conv.history.append(exc)
    return exc_id

#FastAPI 

@core.fastapp.on_event("startup")
async def startup_routine():
    try:
        response = await core.httpx_client.get("http://localhost:" + str(config.taskmanager_port) + "/tasks")
        tasks = json.loads(response.text)
        core.manager_tasks = tasks["aviable tasks"]
    except httpx.ConnectError:
        logger.error("Error fetching tasks from manager")
    logger.info("Core service loading complete")

@core.fastapp.on_event("shutdown")
async def shutdown_routine():
    await core.httpx_client.aclose()
    logger.info("Core shutdown completed")

@core.fastapp.get("/status")
async def root():
    return {"message": "Nexus core up and running"}

#intermediary between comms input and taskmanager
@core.fastapp.post("/api/message_from_user")
async def message_from_user(inbound: Message):
    logger.info("incoming message from user: " + Fore.WHITE + inbound.from_user.username)   
    #handle text input
    if inbound.text != None:
        logger.info(Fore.GREEN + "[{}]: ".format(inbound.from_user.username) + Fore.WHITE + inbound.text)

    #if message is a command, send it to taskmanager
    if inbound.command != None:
        encoded_command = encoders.jsonable_encoder(inbound.command)
        response = await core.httpx_client.post("http://localhost:" + str(config.taskmanager_port) + "/api/run_command?exc_id={}".format(inbound.exchange.id), data = json.dumps(encoded_command)) 
    return {"message": "ok"}

@core.fastapp.post("/api/message_from_group")
async def message_from_user(inbound: Message, chat_id: str):
    return {"message": "ok"}

@core.fastapp.post("/api/task_response")
async def message_to_user(inbound: Message, task_id: str, final: bool):
    message: Message = handle_manager_message(inbound, task_id)
    handle_conv(message, final)
    response = await core.httpx_client.get("http://localhost:" + str(config.taskmanager_port) + "/api/task_complete?task_id={}".format(task_id))
    #check message type
    if message.text != None:
        logger.info(Fore.GREEN + "[{}]: ".format(inbound.user.name) + Fore.WHITE + message.text)
        #pass payload to comms service
        encoded_message = encoders.jsonable_encoder(message)
        response = await core.httpx_client.post("http://localhost:" + str(config.comms_port) + "/api/message_to_user", data = json.dumps(encoded_message))
    return {"message": "ok"}