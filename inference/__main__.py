import uvicorn
from nexutil.config import Config

config = Config()
if __name__ == "__main__":
    uvicorn.run("inference:inference.fastapp", port = config.inference_port, host= "127.0.0.1", reload=True, reload_dirs=["./inference"])