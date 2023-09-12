import uvicorn
from nexutil.config import Config

config = Config()
if __name__ == "__main__":
    uvicorn.run("comms:comms.fastapp", port = config.comms_port, host= "127.0.0.1")