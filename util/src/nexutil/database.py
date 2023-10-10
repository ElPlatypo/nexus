import psycopg
from typing import Optional
import traceback
import uuid
import numpy
from pgvector.psycopg import register_vector
from . import types
from . import log
from . import config

logger = log.setup_logger("Nexutil")
conf = config.Config()

def connect() -> psycopg.Connection:
    con = psycopg.connect(host = conf.database_host, dbname = conf.database_name, user = conf.database_username, password = conf.database_password)
    return con

def gen_task_tables(con: psycopg.Connection) -> bool:
    try:
        cur = con.cursor()
        register_vector(con)

        cur.execute("""DROP TABLE IF EXISTS tasks""")
        con.commit()
        cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
                    id UUID PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    embeddings vector(768));
                    """)
        con.commit()
        return True
    except:
        logger.warning("Error creating task tables in db")
        traceback.print_exc()
        return False

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

#gets a number of messages ordered by date
def get_messages(con: psycopg.Connection, conv_id: str, number: int) -> Optional[list[types.Message]]:
    try:
        cur = con.cursor()

        cur.execute("""SELECT * FROM messages 
                    INNER JOIN exchanges ON messages.exchange_id = exchanges.id
                    WHERE conversation_id = %s
                    ORDER BY datetime desc
                    LIMIT %s;""",
                    (conv_id, number,))
        
        results: list[types.Message] = cur.fetchall()

        out = []
        for mes in results:
            newmess = types.Message(
                id = str(mes[0]),
                exchange = types.Exchange(
                    id = str(mes[1]),
                    channel = mes[12],
                    concluded = mes[11]
                ),
                conversation_id = mes[2],
                from_user = get_user_internal(con, str(mes[3])),
                datetime = mes[4],
                channel = mes[12],
                text = mes[5],
                command = mes[6],
                image = mes[7],
                video = mes[8],
                audio = mes[9]
            )
            out.append(newmess)
        return out
        
    except:
        logger.warning("Error ending exchange in db")
        traceback.print_exc()
        return False

#register aviable tasks in the database
def add_task(con: psycopg.Connection, task: types.Task, embeds: numpy.array) -> bool:
    try:
        cur = con.cursor()

        cur.execute("""INSERT INTO tasks (
                    id,
                    name,
                    description,
                    embeddings)
                    VALUES (%s,%s,%s,%s);""",
                    (str(uuid.uuid4()), task.name, task.description, embeds,))
        con.commit()
        return True
    except:
        logger.warning("Error registering task in db")
        traceback.print_exc()
        return False