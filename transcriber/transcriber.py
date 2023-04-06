from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from transformers import WhisperProcessor, WhisperForConditionalGeneration

class Whisper():

    processor: WhisperProcessor = None
    model: WhisperForConditionalGeneration = None

    def new(self, processor, model) -> None:
        self.processor = processor
        self.model = model

#class TranscriberRequest(BaseModel):
    #wav = Annotated[bytes, File()]

fastapp = FastAPI()
whisper = Whisper()


@fastapp.on_event("startup")
async def startup_routine():
    whisper.processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
    whisper.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny")
    print("startup complete")

@fastapp.on_event("shutdown")
async def shutdown_routine():
    print("shutting down")

@fastapp.get("/status")
async def status():
    return {"message": "Speech transcriber up and running"}

@fastapp.get("/api/transcribe")
async def transcribe():
    with open("test.wav") as audio:
        input_features = whisper.processor(audio, return_tensors="pt").input_features
    predicted_ids = whisper.model.generate(input_features)
    transcription = whisper.processor.batch_decode(predicted_ids, skip_special_tokens=True)
    print(transcription)