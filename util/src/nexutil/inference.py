from . import types
from . import log
from . import config
from typing import Optional
import httpx
import json
import traceback
import io

logger = log.setup_logger("Nexutil")
conf = config.Config()

async def generate_text(httpx: httpx.AsyncClient, prompt: str) -> Optional[str]:
    try:
        string = types.String(str = prompt)
        response = await httpx.post("http://localhost:" + str(conf.inference_port) + "/api/generate_text", data = string.model_dump_json(), timeout = 30)
        return response.text
    except:
        logger.warning("Error generating text with inference service") 
        traceback.print_exc()
        return False
    
async def transcribe_audio(httpx: httpx.AsyncClient, audio: bytes) -> Optional[str]:
    try:
        response = await httpx.post("http://localhost:" + str(conf.inference_port) + "/api/transcribe_audio", files = {"audio_file": audio}, timeout = 30)
        return response.text
    except:
        logger.warning("Error transcribing audio with inference service")
        traceback.print_exc()
        return False

async def gen_embeddings(httpx: httpx.AsyncClient, text: types.String) -> Optional[list[float]]:
    try:
        res = await httpx.post("http://localhost:" + str(conf.inference_port) + "/api/gen_embeddings", data = text.model_dump_json())
        emb = res.json()
        return json.loads(emb)["embeddings"]
    except:
        logger.warning("Error generating embeddings with inference service")
        traceback.print_exc()
        return False