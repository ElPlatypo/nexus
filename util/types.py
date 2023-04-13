from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
import fastapi.encoders
import httpx
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
    
    def get_internal(self, external_id: str) -> Optional[str]:
        if external_id == self.telegram or external_id == self.discord:
            return self.internal
        else:
            return None

class User(BaseModel):
    name: str
    id: str

NEXUSUSER = User(name = "Nexus", id = 0)

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
    id: str
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
    id: str
    channel: MessageChannel
    messages: List[Message] = []
    concluded: bool = False

class Conversation(BaseModel):
    id: str
    users: List[User]
    history: List[Exchange] = []
    active_exchanges: List[Exchange] = []

    
#main task class

class TaskState(BaseModel):
    

class Task(BaseModel):
    id: str
    name: str = "parent Task class"
    description: str = "if you see this there's probably something wrong"
    
    worker_ : Optional[asyncio.Task]

    class Config:
        arbitrary_types_allowed = True

    #generate a response message without source ids, should be filled by core later
    async def respond(self, final: bool, text: str = None, command: Command = None, image: Image = None, video: Video = None, audio: Audio = None) -> None:
        client = httpx.AsyncClient()
        message = Message(
            id = str(uuid.uuid4()),
            user = NEXUSUSER,
            text = text,
            command = command,
            image = image,
            video = video,
            audio = audio
        )
        encoded_message = fastapi.encoders.jsonable_encoder(message)
        response = await client.post("http://localhost:6040/api/task_response?task_id={}&final={}".format(self.id, final), data = json.dumps(encoded_message))

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
    


