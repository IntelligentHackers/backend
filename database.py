from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import settings
import logging


class DataBase:
    client: AsyncIOMotorClient = None   # type: ignore
    gensync: AsyncIOMotorDatabase = None   # type: ignore


db = DataBase()


async def connect_to_mongo():
    logging.info("Connecting to mongo...")
    db.client = AsyncIOMotorClient(settings.MONGODB_URI,
                                   maxPoolSize=10,
                                   minPoolSize=10,
                                   uuidRepresentation='standard')
    db.gensync = db.client['gensync']
    logging.info("connected to gensync...")


async def close_mongo_connection():
    logging.info("closing connection...")
    db.client.close()
    logging.info("closed connection")
