from nexutil import log, types
from fastapi import FastAPI, encoders
from typing import Any, Dict, List, Optional
import importlib
from colorama import Fore
from nexutil.config import Config
import nexutil.database as db
import nexutil.inference as inf
import os
import inspect
import httpx
import json
from initcelery import celery

celery.set_default()
logger = log.setup_logger("manager")
config = Config()

class TaskManager:
    fastapp: FastAPI 
    dbconnection: db.psycopg.Connection
    httpx_client: httpx.AsyncClient
    task_list: List[types.Task] = []
    
    def __init__(self):
        self.fastapp = FastAPI()
        self.dbconnection = db.connect()
        self.httpx_client = httpx.AsyncClient()

    def get_task(self, name: str) -> Optional[types.Task]:
        for task in self.task_list:
            if name == task.name:
                return task
        return None


manager = TaskManager()

#FastAPI 

@manager.fastapp.on_event("startup")
async def startup_routine():
    #import all task classes defined inside folder tasks
    task_classes = []
    dir = os.path.join(os.path.dirname(__file__), "tasks")
    tasks_dirs = [os.path.join(dir, name) for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]
    for directory in tasks_dirs:
        if not directory.endswith("_"):
            for file in os.listdir(directory):
                if file.endswith("tasks.py"):
                    mod = "tasks.{}.tasks".format(directory.split("/")[-1])
                    module = importlib.import_module(mod)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, types.Task) and obj != types.Task:
                            task_classes.append(obj)
                            logger.debug("found task: " + name)

    #instantiate each class to get defult attributes
    manager.task_list = [task_class() for task_class in task_classes]

    #create tables on db
    db.gen_task_tables(manager.dbconnection)
    #create embeddings and register to db
    for task in manager.task_list:
        text = types.String(
                str = "<Task name>\n" + task.name + 
                "<Task description>\n" + task.description +
                "<Task examples>\n" + task.examples)
        emb = await inf.gen_embeddings(manager.httpx_client, text)
        db.add_task(manager.dbconnection, task, emb)
        logger.debug("registered task {} in database".format(task.name))
    logger.info("Task manager service finished loading")

@manager.fastapp.on_event("shutdown")
async def shutdown_routine():
    
    logger.info("Task manager service shutdown complete")

@manager.fastapp.get("/status")
async def root():
    return {"message": "Task manager is up and running"}

#get aviable tasks
@manager.fastapp.get("/tasks")
async def get_tasks():
    tasks = []
    for task in manager.task_list:
        tasks.append(task.json()) 
    return {"aviable_tasks": tasks}

@manager.fastapp.post("/api/run_task")
async def run_task(initializer: types.Inittask):
    logging.info("requested task: {}, starting...".format(initializer.name))
    task = manager.get_task(initializer.name)
    if task != None:
        #the ** converts the args dictionary into keyword-value pairs to feed the worker
        print(task)
        task.worker.delay(**initializer.args)
        return {"message": "ok"}
    else:
        return {"message": "unable to find specified task"}
