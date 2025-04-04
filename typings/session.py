from typing import Optional
from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime


class SessionLastMoment(BaseModel):
    time: datetime
    sender: str
    message: str


class Session(BaseModel):
    _id: ObjectId
    participants: list[str]
    last: Optional[SessionLastMoment]
    title: str
