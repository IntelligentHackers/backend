from enum import Enum
from typing import Optional
import torch
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

