import requests
from celery import shared_task
from typing import Dict
from nexutil import types
from nexutil import config
from nexutil import log
import json
import uuid
import traceback
import datetime
    
class Chat(types.Task):
    name: str = "chat"
    description: str = "have a casual conversation with an LLM"
    examples: str = "tell me a joke, how are you doing"
    worker_args: Dict[str, str] = {"message": ""}
    
    @shared_task(name = "chat")
    def worker(**kwargs) -> bool:
        #fetch user message from **kwargs
        message = json.loads(kwargs.get("message"))
        logger = log.setup_logger("generate-text task")
        conf = config.Config()
        #execute task
        try:
            logger.debug("started text generation task, prompt: " + message["text"])
            requests.get("http://localhost:" + str(conf.comms_port) + "/api/action_to_user/typing/{}".format(message["from_user"]["internal"]))
            response = requests.post("http://localhost:" + str(conf.inference_port) + "/api/chat", data = json.dumps(message), timeout = None) 
            requests.get("http://localhost:" + str(conf.comms_port) + "/api/action_to_user/cancel/{}".format(message["from_user"]["internal"]))
            gen_text = response.json()["str"]
            reply = types.Message( 
                id = str(uuid.uuid4()),
                exchange = message["exchange"],
                conversation_id = message["conversation_id"],
                from_user = types.NEXUSUSER,
                datetime = datetime.datetime.now(),
                channel = message["channel"],
                text = gen_text,
                command = None,
                image = None,
                video = None,
                audio = None
            )
            requests.post("http://localhost:" + str(conf.core_port) + "/api/task_response/{}".format(message["from_user"]["internal"]), data = reply.json())
        
        except:
            logger.warning("Error generating text with inference service")
            traceback.print_exc()
            return False

        