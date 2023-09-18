import psycopg
from typing import Optional
import traceback
from . import types
from . import log
from . import config

logger = log.setup_logger("Nexutil")
conf = config.Config()

def connect() -> psycopg.Connection:
    con = psycopg.connect(host = conf.database_host, dbname = conf.database_name, user = conf.database_username, password = conf.database_password)
    return con

def gen_comms_tables(con: psycopg.Connection) -> bool:
    try:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
                    internal_id UUID PRIMARY KEY,
                    telegram_id INT,
                    discord_id TEXT,
                    username TEXT);
                    """)

        cur.execute("""CREATE TABLE IF NOT EXISTS exchanges (
                    id UUID PRIMARY KEY,
                    concluded BOOL,
                    channel SMALLINT);
                    """)

        cur.execute("""CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY,
                    exchange_id UUID,
                    conversation_id TEXT,
                    from_user UUID,
                    datetime TIMESTAMP,
                    text TEXT,
                    command TEXT,
                    image TEXT,
                    audio TEXT,
                    video TEXT,
                    FOREIGN KEY (exchange_id) REFERENCES exchanges (id),
                    FOREIGN KEY (from_user) REFERENCES users(internal_id));
                    """)
        
        cur.execute("""INSERT INTO users (
                    internal_id,
                    telegram_id,
                    discord_id,
                    username) 
                    VALUES ('00000000-0000-0000-0000-000000000000',null,null,'Nexus')
                    ON CONFLICT DO NOTHING;""")
        
        con.commit()
        return True
    except:
        logger.warning("Error creating comms tables in db")
        traceback.print_exc()
        return False
    
def get_user_tg(con: psycopg.Connection, user_id: str) -> Optional[types.Identifiers]:
    try:
        cur = con.cursor()
        
        cur.execute("""SELECT * FROM users 
                    WHERE telegram_id=%s;""", 
                    (int(user_id),))

        result = cur.fetchone()

        if result == None:
            return None
        else:
            user = types.Identifiers(
                internal = str(result[0]),
                telegram = result[1],
                discord = result[2],
                username = result[3]
            )
            return user
    except:
        logger.warning("Error fetching user from db")
        traceback.print_exc()
        return None
    
def get_user_internal(con: psycopg.Connection, user_id: str) -> Optional[types.Identifiers]:
    try:
        cur = con.cursor()
        
        cur.execute("""SELECT * FROM users 
                    WHERE internal_id=%s;""", 
                    (user_id,))

        result = cur.fetchone()

        if result == None:
            return None
        else:
            user = types.Identifiers(
                internal = str(result[0]),
                telegram = result[1],
                discord = result[2],
                username = result[3]
            )
            return user
    except:
        logger.warning("Error fetching user from db")
        traceback.print_exc()
        return None

def add_user(con: psycopg.Connection, user: types.Identifiers) -> bool:
    try:
        cur = con.cursor()

        cur.execute("""INSERT INTO users (
                    internal_id,
                    telegram_id,
                    discord_id,
                    username) 
                    VALUES (%s,%s,%s,%s);""",
                    (user.internal, user.telegram, user.discord, user.username))
        con.commit()
        return True
    except:
        logger.warning("Error creating user in db")
        traceback.print_exc()
        return False
    
def get_exchange(con: psycopg.Connection, user_internal_id: str) -> Optional[types.Exchange]:
    try:
        cur = con.cursor()

        cur.execute("""SELECT exchanges.id, exchanges.channel, exchanges.concluded FROM messages 
                    INNER JOIN exchanges ON messages.exchange_id = exchanges.id
                    WHERE exchanges.concluded = FALSE
                    AND messages.from_user = %s;""",
                    (user_internal_id,))
        
        result = cur.fetchone()

        if result == None:
            return None
        else:
            exchange = types.Exchange(
                id = str(result[0]),
                channel = result[1],
                concluded = result[2]
            )
            return exchange
    except:
        logger.warning("Error fetching exchange from db")
        traceback.print_exc()
        return None
    
def add_exchange(con: psycopg.Connection, exchange: types.Exchange) -> bool:
    try:
        cur = con.cursor()

        cur.execute("""INSERT INTO exchanges (
                    id,
                    channel,
                    concluded)
                    VALUES (%s,%s,%s);""", 
                    (exchange.id, str(exchange.channel.value), str(exchange.concluded)))
        
        con.commit()
        return True
    except:
        logger.warning("Error creating exchange in db")
        traceback.print_exc()
        return False
    
def add_message(con: psycopg.Connection, message: types.Message) -> bool:
    try:
        cur = con.cursor()

        cur.execute("""INSERT INTO messages (
                    id,
                    exchange_id,
                    conversation_id,
                    from_user,
                    datetime,
                    text,
                    command,
                    image,
                    audio,
                    video)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
                    (message.id, message.exchange.id, message.conversation_id, message.from_user.internal, message.datetime, message.text, message.command, message.image, message.audio, message.video))

        con.commit()
        return True
    except:
        logger.warning("Error fetching message from db")
        traceback.print_exc()
        return False
    
def end_exchange(con: psycopg.Connection, exchange: str) -> bool:
    try:
        cur = con.cursor()

        cur.execute("""UPDATE exchanges
                    SET concluded = TRUE
                    WHERE id = %s;""",
                    (exchange,))

        con.commit()
        return True
    except:
        logger.warning("Error ending exchange in db")
        traceback.print_exc()
        return False