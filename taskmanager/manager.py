#initialize and keep internal list of tasks
import asyncio
from util import log, types
from fastapi import FastAPI, encoders
from typing import Any, Dict, List, Optional
import importlib
import os
import inspect
import json

logger = log.setup_logger("manager")

class TaskManager:
    fastapp: FastAPI = FastAPI()
    task_list: List[type[types.Task]] = []
   
def get_task(name: str) -> Optional[type[types.Task]]:
    for task in manager.task_list:
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
                    logger.info("Registered task: " + name)

    #instantiate each class to get defult attributes
    manager.task_list = [task_class() for task_class in task_classes]
    logger.info("Task manager service startup complete")

@manager.fastapp.on_event("shutdown")
async def shutdown_routine():
    
    logger.info("Task manager service shutdown complete")

@manager.fastapp.get("/status")
async def root():
    return {"message": "Task manager is up and running"}

@manager.fastapp.get("/tasks")
async def get_tasks():
    tasks = {'aviable tasks': []}
    for task in manager.task_list:
        tasks["aviable tasks"].append(json.loads(task.json())) 
    return tasks

@manager.fastapp.post("/api/run_command")
async def run_task(inbound: types.Command):
    task_type = get_task(inbound.name)
    if task_type != None:
        task = task_type()
        print(inbound)
        print(task)
        task.cmd_setup(inbound.parameter, inbound.options)
        print(task)
        task.start()

@manager.fastapp.post("/api/run_task")
async def run_task(inbound: Dict[Any, Any]):
    print(type(inbound))
    print(inbound)
    task_type = get_task(inbound["name"])
    new_task = task_type()
    #copy all fields from inbound dict to object
    for attribute in inbound.keys():
        if attribute in dir(new_task):
            setattr(new_task, attribute, inbound[attribute])
    new_task.start()