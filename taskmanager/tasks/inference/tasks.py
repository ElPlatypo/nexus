from celery import shared_task
import httpx
from nexutil import types
from nexutil import config
from nexutil import log
import traceback

logger = log.setup_logger("inference task")

@shared_task
async def generate_text(prompt: str) -> str:
    conf = config.Config()
    try:
        string = types.String(str = prompt)
        response = await httpx.post("http://localhost:" + str(conf.inference_port) + "/api/generate_text", data = string.model_dump_json(), timeout = 30)
        return response.text
    except:
        logger.warning("Error generating text with inference service")
        traceback.print_exc()
        return False