from dotenv import load_dotenv
from nexutil.log import setup_logger
from nexutil.types import Identifiers
from fastapi import FastAPI
import httpx
import sqlite3
import os

load_dotenv()
logger = setup_logger("database")

class Database:
    fastapp: FastAPI
    httpx_client: httpx.AsyncClient
    connection: sqlite3.Connection
    file: str

    def __init__(self) -> None:
        self.fastapp = FastAPI()
        self.httpx_client = httpx.AsyncClient()

database = Database()

def startup() -> None:

    dir = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(dir + "/database.db"):
        logger.warn("database file not found, generating a new one...")
    else:
        logger.info("found database, loading...")

    database.file = dir + "/database.db"
    database.connection = sqlite3.connect(dir + "/database.db")
    cursor = database.connection.cursor()

    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        internal_id TEXT,
                        telegram_id TEXT,
                        discord_id TEXT
                    );
                """)


#FastAPI 

@database.fastapp.on_event("startup")
async def startup_routine():
    startup()
    logger.info("Database service loading complete")

@database.fastapp.on_event("shutdown")
async def shutdown_routine():
    database.connection.close()
    logger.info("Database service shutdown complete")

@database.fastapp.get("/status")
async def root():
    return {"message": "Database is up and running"}

@database.fastapp.get("/api/get_user_from_tg/{tg_id}")
async def get_user(tg_id):
    cursor = database.connection.cursor()
    cursor.execute(f"SELECT * FROM users WHERE telegram_id=\"{tg_id}\";")

    result = cursor.fetchone()

    if result == None:
        return {"internal_id": "missing"}
    else:
        return {"internal_id": result[0], "telegram_id": result[1], "discord_id": result[2]}
    
@database.fastapp.post("/api/add_user")
async def add_user(user: Identifiers):
    logger.debug("Adding new user to database: {}".format(user.internal))

    cursor = database.connection.cursor()
    cursor.execute("""
                   INSERT INTO users (internal_id,telegram_id,discord_id)
                   VALUES (?,?,?);
                   """, (user.internal, user.telegram, user.discord))
    return {"message": "ok"}
