import fastapi
import httpx
import os
import datetime
import json
import uuid
from dotenv import load_dotenv
from nexutil.log import setup_logger
from nexutil.config import Config
from nexutil import types
import nexutil.database as db
from llama_cpp import Llama
from whisper_jax import FlaxWhisperPipline
from sentence_transformers import SentenceTransformer

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
    stransformer: SentenceTransformer

    def __init__(self) -> None:
        self.dbconnection = db.connect()
        self.fastapp = fastapi.FastAPI()
        self.httpx_client = httpx.AsyncClient()
        self.llama = Llama(model_path = os.path.dirname(__file__) + "/models/llama2_7b_chat_uncensored.Q4_K_M.gguf")
        self.whisper = FlaxWhisperPipline("openai/whisper-base")
        self.stransformer = SentenceTransformer('all-mpnet-base-v2', device="cpu")

inference = Inference()

def gen_prompt(messages: list[types.Message], usr_str: str, ai_str: str) -> str:
    prompt = ""
    for mes in reversed(messages):
        if mes["user"] == "00000000-0000-0000-0000-000000000000":
            prompt = prompt + ai_str + mes["message"]
        else:
            prompt = prompt + usr_str + mes["message"]
        prompt = prompt + "\n"
    return prompt

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

@inference.fastapp.post("/api/gen_embeddings")
async def gen_embeddings(text: types.String) -> str:
    print(text)
    logger.info("requested embedding generation")
    embeddings = inference.stransformer.encode(text.str).tolist()
    return json.dumps({"embeddings": embeddings})

@inference.fastapp.post("/api/chat")
async def chat(message: types.Message) -> types.String:
    logger.debug("Requested chat")
    history = db.get_messages(inference.dbconnection, message.conversation_id, 5)
    msglist = []
    msglist.append({"user": str(message.from_user.internal), "message": message.text})
    for mes in history:
        msglist.append({"user": mes.from_user.internal, "message": mes.text})
    prompt = gen_prompt(msglist, usr_str = "### HUMAN:\n", ai_str ="### RESPONSE:\n")
    output = inference.llama(prompt, max_tokens=256, stop=["### HUMAN:"], echo=True)
    response = types.String(str = output["choices"][0]["text"].split("### RESPONSE:\n")[-1])
    return response

@inference.fastapp.post("/api/transcribe_audio")
async def transcribe_audio(audio_file: fastapi.UploadFile):
    output = inference.whisper(await audio_file.read(), language = "en")
    print(output["text"])
    return output["text"]