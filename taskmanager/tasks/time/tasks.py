import requests
from celery import shared_task
from nexutil import types
from nexutil import config
from nexutil import log
import json
import uuid
import datetime

class Time(types.Task):
    name: str = "time"
    description: str = "get current time, or time in a different city"
    examples: str = "what time is it?, whats the time in paris right now?"
    worker_args: dict[str, str] = {"message": "", "city": ""}

    def parse_arguments(self, message: types.Message) -> dict:
        #perform logic to extract city name
        city = "none"
        return {"message": message.json(), "city": city}
    
    @shared_task(name = "time")
    def worker(**kwargs) -> bool:
        #fetch user message from **kwargs
        message = json.loads(kwargs.get("message"))
        city = kwargs.get("city")
        logger = log.setup_logger("generate-text task")
        conf = config.Config()
        #execute task
        logger.debug("started time task")
        if city == "none":
            time = datetime.datetime.now()
            hour = time.strftime("%H:%M")

            reply = types.Message( 
                id = str(uuid.uuid4()),
                exchange = message["exchange"],
                conversation_id = message["conversation_id"],
                from_user = types.NEXUSUSER,
                datetime = datetime.datetime.now(),
                channel = message["channel"],
                text = hour,
                command = None,
                image = None,
                video = None,
                audio = None
            )
            requests.post("http://localhost:" + str(conf.core_port) + "/api/task_response/{}".format(message["from_user"]["internal"]), data = reply.json())