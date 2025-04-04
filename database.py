from motor.core import AgnosticCollection
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import settings
import logging


class DataBase:
    client: AsyncIOMotorClient = None   # type: ignore
    gensync: AsyncIOMotorDatabase = None   # type: ignore
    registrations: AgnosticCollection = None
    users: AgnosticCollection = None
    conversations: AgnosticCollection = None
    auths: AgnosticCollection = None


db = DataBase()


async def connect_to_mongo():
    logging.info("Connecting to mongo...")
    db.client = AsyncIOMotorClient(settings.MONGODB_URI,
                                   maxPoolSize=10,
                                   minPoolSize=10,
                                   uuidRepresentation='standard')
    db.gensync = db.client.get_database('gensync')
    db.registrations = db.gensync.get_collection('registrations')
    db.users = db.gensync.get_collection('users')
    db.conversations = db.gensync.get_collection('conversations')
    db.auths = db.gensync.get_collection('auths')
    logging.info("connected to gensync...")


async def close_mongo_connection():
    logging.info("closing connection...")
    db.client.close()
    logging.info("closed connection")
