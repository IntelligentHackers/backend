from datetime import date, datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel


class UserGender(str, Enum):
    male = "male"
    female = "female"
    nonbinary = "non_binary"
    unknown = "unknown"


class UserLogin(BaseModel):
    id: str
    credential: str


class UserRole(str, Enum):
    young = "young"
    old = "old"


class User(BaseModel):
    _id: ObjectId
    auth_id: str
    username: str
    gender: UserGender
    birth: date  # ISO-8601
    avatar: bytes
    role: UserRole
    email: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    bio: str
    tags: list[str]
    activated: bool

    # Get the attribute of age.
    @property
    def age(self) -> int:
        from datetime import datetime

        birth_date = self.birth
        today = datetime.today()
        return (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )
