from datetime import date, datetime
from pydantic import BaseModel
from typings.user import UserGender


class UserSurveyResult(BaseModel):
    username: str
    birth: str
    bio: str
    tags: list[str]
    gender: UserGender


class UserSurveyDialogs(BaseModel):
    time: datetime
    username: str
