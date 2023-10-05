from celery import shared_task
from nexutil import types
from typing import Dict
from nexutil import config
from nexutil import log
import json
import traceback

class TranscribeAudio(types.Task):
    name = "transcribe-audio"
    description = "converts an audio file of speech to a string"
    worker_args: Dict[str, str] = {"message": ""}
    
    @shared_task(name = "transcribe")
    def worker(**kwargs) -> bool:
        #fetch user message from **kwargs
        message = json.loads(kwargs.get("message"))
        logger = log.setup_logger("generate-text task")
        conf = config.Config()
        #execute task