from fastapi import APIRouter
from pydantic import BaseModel
from utils.cert import validate_by_cert
router = APIRouter()


class AuthUser(BaseModel):
    id: str
    credential: str


@router.post("/auth")
async def auth_user(auth: AuthUser):
    id = auth.id
    credential = auth.credential

    result = await validate_by_cert(id, credential)

    return {
        "token": result,
        "_id": id,
    }
