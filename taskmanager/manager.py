#initialize and keep internal list of tasks
import asyncio
from util import log, types
from fastapi import FastAPI, encoders
from typing import Any, Dict, List, Optional
import importlib
from colorama import Fore
import uuid
import os
import inspect
import json

logger = log.setup_logger("manager")

class TaskManager:
    fastapp: FastAPI = FastAPI()
    task_list: List[type[types.Task]] = []
    active_tasks: List[str] = []
   
    def get_task(self, name: str) -> Optional[type[types.Task]]:
        for task in self.task_list:
            if name == task.name:
                return type(task)
        return None


manager = TaskManager()

#FastAPI 

@manager.fastapp.on_event("startup")
async def startup_routine():

    #import all task classes defined inside folder tasks
    task_classes = []
    dir = os.path.join(os.path.dirname(__file__), "tasks")
    for file in os.listdir(dir):
        if file.endswith(".py"):
            module_name = file[:-3]
            module = importlib.import_module(f"taskmanager.tasks.{module_name}")
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, types.Task) and obj != types.Task:
                    task_classes.append(obj)
                    logger.debug("registered task: " + name)

    #instantiate each class to get defult attributes
    manager.task_list = [task_class(id = -1) for task_class in task_classes]
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
    tasks = {'aviable tasks': []}
    for task in manager.task_list:
        tasks["aviable tasks"].append(json.loads(task.json())) 
    return tasks

#execute task
@manager.fastapp.post("/api/run_command")
async def run_task(inbound: types.Command, exc_id: str):
    logger.info("recieved command: " + Fore.GREEN + inbound.name + Fore.CYAN + ", spawning task with id: "+ Fore.WHITE + exc_id)
    task_type = manager.get_task(inbound.name)
    if task_type != None:
        task = task_type(id = exc_id)
        task.cmd_setup(inbound.parameter, inbound.options)
        manager.active_tasks.append(exc_id)
        task.start()
    return {"message": "ok"}

@manager.fastapp.post("/api/run_task")
async def run_task(inbound: Dict[Any, Any], exc_id: Optional[str] = None):
    task_type = manager.get_task(inbound["name"])
    #if task comes from a command give the same id to task and associated exchange
    if exc_id != None:
        new_task = task_type(id = exc_id)
    else:
        new_task = task_type()
    #copy all fields from inbound dict to object
    for attribute in inbound.keys():
        if attribute in dir(new_task):
            setattr(new_task, attribute, inbound[attribute])
    new_task.start()
    return {"message": "ok"}

#task completion callback
@manager.fastapp.get("/api/task_complete")
async def task_complete(task_id: str):
    manager.active_tasks.remove(task_id)
    logger.info("task: " + Fore.WHITE + task_id + Fore.CYAN + " finished execution")
    return {"message": "ok"}