from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
import fastapi.encoders
import os
import uuid
import requests
import json
import asyncio

#pydantic class definitions

#message types

class MessageChannel(Enum):
    API = 0
    TELEGRAM = 1

class Identifiers(BaseModel):
    internal: Optional[str]
    telegram: Optional[str]
    discord: Optional[str]

    def check(self, id: str) -> bool:
        value = False
        if id == self.internal or id == self.telegram or id == self.discord:
            value = True
        return value

class User(BaseModel):
    name: str
    ids: Identifiers

NEXUSUSER = User(name = "Nexus", identifiers = Identifiers(internal = 0))

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

class Message(BaseModel):
    user: User
    chat: Optional[str]
    channel: Optional[MessageChannel]
    text: Optional[str]
    command: Optional[Command]
    image: Optional[Image]
    video: Optional[Video]
    audio: Optional[Audio]

    def json(self) -> str:
        return json.dumps(fastapi.encoders.jsonable_encoder(self))
    
class Exchange(BaseModel):
    channel: MessageChannel
    messages: List[Message] = []

class Conversation(BaseModel):
    ids: Identifiers
    users: List[User]
    history: List[Exchange] = []
    active_exchanges: List[Exchange] = []

    
#main task class

class Task(BaseModel):
    name: str = "parent Task class"
    description: str = "if you see this there's probably something wrong"
    worker_ : Optional[asyncio.Task]

    class Config:
        arbitrary_types_allowed = True

    def respond_final(self, text: str = None, command: Command = None, image: Image = None, video: Video = None, audio: Audio = None) -> None:
        message = Message(
            user = NEXUSUSER,
            text = text,
            command = command,
            image = image,
            video = video,
            audio = audio
        )
        encoded_message = fastapi.encoders.jsonable_encoder(message)
        response = requests.post("http://localhost:6040" + "/api/task_final_output", data = json.dumps(encoded_message))

    #actual logic of the task
    async def worker(self, **kwargs):
        raise NotImplemented
    
    #util function to pass command-like arguments to Task object named attributes
    def cmd_setup(self, parameter: str, options: Dict[str, Any]) -> None:
        raise NotImplemented

    def start(self, **kwargs) -> None:
        # TODO get event loop via fastapi/uvicorn maybe if possible
        self.worker_ = asyncio.get_event_loop().create_task(self.worker())
    
    #outputs a json representation of the object with values
    def json(self) -> str:
        return json.dumps(fastapi.encoders.jsonable_encoder(self))
    
    #outputs a json representation of the object with attribute variable types (keeps name and desc untouched)
    def descriptor(self) -> str:
        descriptor = self.__annotations__
        descriptor["name"] = self.name
        descriptor["description"] = self.description
        return json.dumps(descriptor)
    

