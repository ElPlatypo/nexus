import fastapi
import httpx
import os
import datetime
import uuid
from dotenv import load_dotenv
from nexutil.log import setup_logger
from nexutil.config import Config
from nexutil.types import String
import nexutil.database as db
from llama_cpp import Llama
from whisper_jax import FlaxWhisperPipline

load_dotenv() 
os.environ['TRANSFORMERS_CACHE'] = os.path.dirname(__file__) + "/models"
logger = setup_logger("inference")
config = Config()

class Inference():
    dbconnection: db.psycopg.Connection
    fastapp: fastapi.FastAPI
    httpx_client: httpx.AsyncClient
    llama: Llama
    whisper: FlaxWhisperPipline

    def __init__(self) -> None:
        self.dbconnection = db.connect()
        self.fastapp = fastapi.FastAPI()
        self.httpx_client = httpx.AsyncClient()
        self.llama = Llama(model_path = os.path.dirname(__file__) + "/models/llama-2-7b-chat.Q4_K_M.gguf")
        self.whisper = FlaxWhisperPipline("openai/whisper-base")

inference = Inference()

@inference.fastapp.on_event("startup")
async def startup_routine():

    logger.info("Inference service loading complete")

@inference.fastapp.on_event("shutdown")
async def shutdown_routine():
    await inference.httpx_client.aclose()
    logger.info("Inference service shutdown complete")

@inference.fastapp.get("/status")
async def root():
    return {"message": "Inference service up and running"}

@inference.fastapp.post("/api/generate_text")
async def generate_text(prompt: String) -> String:
    print(prompt.str)
    output = inference.llama("Q: {} A: ".format(prompt.str), max_tokens=256, stop=["Q:", "\n"], echo=True)
    response = String(str = output["choices"][0]["text"].split("A: ")[1])
    return response

@inference.fastapp.post("/api/transcribe_audio")
async def transcribe_audio(files: fastapi.UploadFile):
    output = inference.whisper(await files.read())
    print(output["text"])
    return output["text"]