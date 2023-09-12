import tomli
import os

class Config():
    core_port: str
    comms_port: str
    taskmanager_port: str
    database_port: str

    def __init__(self) -> None:
        dir = os.path.dirname(os.path.realpath(__file__))
        with open(dir + "/config.toml", mode="rb") as file:
            config = tomli.load(file)
            self.core_port = config["core"]["port"]
            self.comms_port = config["communications"]["port"]
            self.database_port = config["database"]["port"]
            self.taskmanager_port = config["taskmanager"]["port"]