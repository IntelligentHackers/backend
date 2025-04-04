from datetime import date, datetime
from pydantic import BaseModel
from typings.user import UserGender


class UserSurveyResult(BaseModel):
    username: str
    birth: date
    bio: str
    tags: list[str]
    gender: UserGender

class UserSurveyDialogs(BaseModel):
    time: datetime
    username: str

