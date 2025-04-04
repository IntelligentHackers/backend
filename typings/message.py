from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime


class Message(BaseModel):
    _id: ObjectId
    affiliation: str
    time: datetime
    sender: str
    original: str
    translated: str
    rating: int
