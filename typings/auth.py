from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel


class Auth(BaseModel):
    _id: ObjectId
    email: str
    password_hash: bytes  # Only if password login
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    google_id: Optional[str] = None
    github_id: Optional[str] = None
    apple_id: Optional[str] = None
    microsoft_id: Optional[str] = None
