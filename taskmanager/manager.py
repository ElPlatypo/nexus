#initialize and keep internal list of tasks
import asyncio
from util import log, message
from fastapi import FastAPI, encoders
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel
import importlib
import os
import inspect
import json

logger = log.setup_logger("manager")

class TaskManager:
    fastapp: FastAPI
    task_list = []

    def __init__(self):
        self.fastapp = FastAPI()

class Task(BaseModel):
    name: str
    description: str
    cmd: bool
    cmd_parameter: Optional[str]
    cmd_options: Optional[Dict]
    worker_ : Optional[asyncio.Task]        

    def __init__(self, name: str, description: str) -> None:
        super().__init__(
            name = name,
            description = description,
            cmd = False
        )
        
        self.cmd_parameter = None
        self.cmd_options = None

    class Config:
        arbitrary_types_allowed = True

    async def respond(self, retval: Any):
        pass
        # TODO fare fisicamente la POST o whatever per spedirti indietro il risultato

    #actual logic of the task
    async def worker(self, **kwargs):
        raise NotImplemented
    
    #util function to pass command-like arguments to Task object named attributes
    def cmd_setup(self) -> None:
        raise NotImplemented

    def start(self, **kwargs) -> None:
        # TODO get event loop via fastapi/uvicorn maybe if possible
        self.worker_ = asyncio.get_event_loop().create_task(self.worker())
    
    #outputs a json representation of the object with values
    def json(self) -> str:
        return json.dumps(encoders.jsonable_encoder(self))
    
    #outputs a json representation of the object with attribute variable types (keeps name and desc untouched)
    def descriptor(self) -> str:
        descriptor = self.__annotations__
        descriptor["name"] = self.name
        descriptor["description"] = self.description
        return json.dumps(descriptor)

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
                if inspect.isclass(obj) and issubclass(obj, Task) and obj != Task:
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

@manager.fastapp.post("/api/run_task")
async def run_task(inbound: Dict[Any, Any]):
    print(type(inbound))
    print(inbound)
    for task in manager.task_list:
        task: Task
        if inbound["name"] == task.name:
            #instantiante new task object
            task_type = type(task)
            new_task = task_type()
            #copy all fields from inbound dict to object
            for attribute in inbound.keys():
                if attribute in dir(task):
                    setattr(new_task, attribute, inbound[attribute])
            #if task comes from a /command setup call cmd_setup to set the correct fields in the task
            if new_task.cmd == True:
                new_task.cmd_setup()
            new_task.start()