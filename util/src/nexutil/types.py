from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel
import fastapi.encoders
import datetime
import json
from celery import shared_task
from pyrogram import enums

#pydantic class definitions

#message types

class MessageChannel(Enum):
    API = 0
    TELEGRAM = 1

class Identifiers(BaseModel):
    internal: Optional[str]
    telegram: Optional[int]
    discord: Optional[str]
    username: Optional[str]

    def check(self, id: str) -> bool:
        value = False
        if id == self.internal or id == self.telegram or id == self.discord:
            value = True
        return value
    
    def get_internal(self, external_id: str) -> Optional[str]:
        if external_id == self.telegram or external_id == self.discord:
            return self.internal
        else:
            return None

NEXUSUSER = Identifiers(internal="00000000-0000-0000-0000-000000000000", telegram = None, discord = None, username = "Nexus")

class String(BaseModel):
    str: str

class Command(BaseModel):
    name: str
    parameter: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class Image(BaseModel):
    bytes: Any

class Video(BaseModel):
    bytes: Any

class Audio(BaseModel):
    bytes: Any
    
class Exchange(BaseModel):
    id: str
    channel: MessageChannel
    concluded: bool = False

class Message(BaseModel):
    id: str
    exchange: Exchange
    conversation_id: str
    from_user: Identifiers
    datetime: datetime.datetime
    channel: MessageChannel
    text: Optional[str]
    command: Optional[Command]
    image: Optional[Image]
    video: Optional[Video]
    audio: Optional[Audio]

    def json(self) -> str:
        return json.dumps(fastapi.encoders.jsonable_encoder(self))
    
#main task class
class Task():

    name: str = "parent Task class"
    description: str = "if you see this there's probably something wrong"
    examples: str = "if you see this there's probably something wrong"
    worker_args: Dict[str, str] = {}
    
    @shared_task
    def worker(**kwargs):
        raise NotImplementedError

    #util function to pass command-like arguments to Task object named attributes
    def cmd_setup(self, parameter: str, options: Dict[str, Any]) -> None:
        raise NotImplementedError

    #outputs a json representation of the object with values
    def json(self) -> str:
        return {"name": self.name, "description": self.description}

class Inittask(BaseModel):
    name: str
    #when core initializes a task for the manager the arguments should be passed as strings, to be eventually decoded later
    args: Dict[str, str]