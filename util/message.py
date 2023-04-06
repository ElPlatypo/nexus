from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel
import fastapi.encoders
import json

from dataclasses import dataclass

class Channel(Enum):
    API = 0
    TELEGRAM = 1

class MessageType(Enum):
    TEXT = 0
    COMMAND = 1
    IMAGE = 2
    AUDIO = 3

class Message(BaseModel):
    channel: Channel
    type: MessageType

    def json(self) -> str:
        return json.dumps(fastapi.encoders.jsonable_encoder(self))

class TextMessageModel(Message):
    text: str


class CommandMessageModel(Message):
    command: str
    parameter: Optional[str]
    options: Optional[Dict[str, str]]