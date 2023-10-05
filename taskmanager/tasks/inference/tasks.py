from celery import shared_task
from nexutil import types
from nexutil import config
from nexutil import log
import traceback

class Gentext(types.Task):
    name: str = "generate-text"
    description: str = "takes an input string ans uses it as prompt with a LLM"

    def worker(self, prompt):
        generate_text.delay(prompt)

@shared_task
async def generate_text(prompt: str) -> str:
    logger = log.setup_logger("generate-text task")
    conf = config.Config()
    try:
        string = types.String(str = prompt)
        #response = await httpx.post("http://localhost:" + str(conf.inference_port) + "/api/generate_text", data = string.model_dump_json(), timeout = 30)
        return "response.text"
    except:
        logger.warning("Error generating text with inference service")
        traceback.print_exc()
        return False