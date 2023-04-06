import fastapi
import io
from TTS.api import TTS, Synthesizer
from log import setup_logger
from pydantic import BaseModel

class TtsRequest(BaseModel):
    text: str
    model_name: str

fastapp = fastapi.FastAPI()
logger = setup_logger("Speech-syntesis", 20)
model_name = TTS.list_models()[0]
tts = TTS(model_name)

@fastapp.on_event("startup")
async def startup_routine():
    
    logger.info("startup completed")

@fastapp.on_event("shutdown")
async def shutdown_routine():
    tts = None

@fastapp.get("/status")
async def status():
    return {"message": "Speech syntesis up and running"}

@fastapp.get("/locales")
async def locales():
    locales = tts.languages
    return {"message": "Aviable locales for currently loaded model", "locales": ", ".join(locales)}

@fastapp.get("/models")
async def models():
    models = tts.models
    return {"message": "Aviable speech syntesis models", "models": ", ".join(models)}

@fastapp.get("/models/{lang}")
async def models_lang(lang):
    models = [model for model in tts.models if model.find("/" + lang + "/") != -1]
    return {"message": "Aviable speech syntesis models", "models": ", ".join(models)}

@fastapp.post("/api/syntesize")
async def syntesize(body: TtsRequest):
    tts.load_model_by_name(body.model_name)
    wav_bytes = tts.tts(text=body.text)
    out = io.BytesIO()
    tts.synthesizer.save_wav(wav_bytes, out)
    return fastapi.responses.StreamingResponse(content=out , media_type="audio/wav")

#todo, dig deeper in Syntesizer class and synthesize step-by-step to have more control
