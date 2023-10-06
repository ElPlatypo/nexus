from dotenv import load_dotenv
from nexutil.log import setup_logger
from nexutil import types
from nexutil import config
import nexutil.inference as inf
import nexutil.database as db
import fastapi 
from fastapi import encoders
from colorama import Fore
import httpx
import json
from typing import List

load_dotenv()
logger = setup_logger("core")
config = config.Config()

class Core:
    fastapp: fastapi.FastAPI
    httpx_client: httpx.AsyncClient
    manager_tasks: List[types.Task]
    dbconnection: db.psycopg.Connection
    
    def __init__(self):
        self.fastapp = fastapi.FastAPI()
        self.httpx_client = httpx.AsyncClient()
        self.dbconnection = db.connect()

core = Core()

#FastAPI 

@core.fastapp.on_event("startup")
async def startup_routine():
    try:
        response = await core.httpx_client.get("http://localhost:" + str(config.taskmanager_port) + "/tasks")
        tasks = json.loads(response.text)
        core.manager_tasks = tasks["aviable_tasks"]
    except httpx.ConnectError:
        logger.error("Error fetching tasks from manager")
    logger.info("Core service loading complete")

@core.fastapp.on_event("shutdown")
async def shutdown_routine():
    await core.httpx_client.aclose()
    core.dbconnection.close()
    logger.info("Core shutdown completed")

@core.fastapp.get("/status")
async def root():
    return {"message": "Nexus core up and running"}

#intermediary between comms input and taskmanager
@core.fastapp.post("/api/message_from_user")
async def message_from_user(inbound: types.Message):
    logger.info("incoming message from user: " + Fore.WHITE + inbound.from_user.username)   
    logger.debug("message: {}".format(inbound.json()))
    if inbound.text != None:
        logger.info(Fore.GREEN + "[{}]: ".format(inbound.from_user.username) + Fore.WHITE + inbound.text)

    #if message is a command, send it to taskmanager
    if inbound.command != None:
        encoded_command = encoders.jsonable_encoder(inbound.command)
        response = await core.httpx_client.post("http://localhost:" + str(config.taskmanager_port) + "/api/run_command?exc_id={}".format(inbound.exchange.id), data = json.dumps(encoded_command)) 
    
    #handle text messages
    if inbound.command == None and inbound.text != None:
        logger.info("calling chat task...")
        task = types.Inittask(
            name = "chat",
            args = {"message": inbound.json()}
        )
        response = await core.httpx_client.post("http://localhost:" + str(config.taskmanager_port) + "/api/run_task", data = task.model_dump_json(), timeout = None)

    return {"message": "ok"}

@core.fastapp.post("/api/task_response/{recipient}")
async def message_to_user(inbound: types.Message, recipient: str):
    logger.info(Fore.GREEN + "[NEXUS]: " + Fore.WHITE + inbound.text)
    db.add_message(core.dbconnection, inbound)

    await core.httpx_client.post("http://localhost:" + str(config.comms_port) + "/api/message_to_user/{}".format(recipient), data = inbound.json())
    #end exchange needs to be executed later
    db.end_exchange(core.dbconnection, inbound.exchange.id)

    return {"message": "ok"}