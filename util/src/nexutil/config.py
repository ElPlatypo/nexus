import tomli
import os

class Config():
    core_port: str
    comms_port: str
    taskmanager_port: str
    database_host: str
    database_name: str
    database_username: str
    database_password: str
    inference_port: str

    def __init__(self) -> None:
        dir = os.path.dirname(os.path.realpath(__file__))
        with open(dir + "/config.toml", mode="rb") as file:
            config = tomli.load(file)
            self.core_port = config["core"]["port"]
            self.comms_port = config["communications"]["port"]
            self.taskmanager_port = config["taskmanager"]["port"]
            self.database_host = config["postgresql"]["host"]
            self.database_name = config["postgresql"]["database_name"]
            self.database_username = config["postgresql"]["username"]
            self.database_password = config["postgresql"]["password"]
            self.inference_port = config["inference"]["port"]