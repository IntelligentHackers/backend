from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from typing import Optional
from datetime import datetime, UTC
from database import db
from bson import ObjectId
from utils.cert import jwt_decode

# Secret key and algorithm for JWT
SECRET_KEY = open("aes_key.txt", "r").read()
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def validate_object_id(id: str):
    try:
        _id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Object ID")
    return _id


def string_to_optional_object_id(id: str):
    try:
        _id = ObjectId(id)
    except:
        return None
    return _id


async def get_user(oid: str):
    """
    Get user by oid
    """
    user = await db.gensync.users.find_one({"_id": validate_object_id(oid)})
    if user:
        return user
    print(user)
    return None


async def optional_current_user(token: str = Depends(oauth2_scheme)):
    result = await get_current_user(token, False)
    return result


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme), exception: bool = True
):
    """
    Inject `Depends`, returning user info
    """

    def raise_exception():
        if exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            return None

    try:
        if token is None:
            raise_exception()
        # Decode JWT
        payload = jwt_decode(token)
        oid: str = payload.get("sub", None)
        exp: int = payload.get("exp", None)
        jti: str = payload.get("jti", None)

        # Check if the token is valid
        if oid is None or exp is None or jti is None:
            raise_exception()

        # Check if the token is expired
        if exp is not None and datetime.now(UTC) >= datetime.fromtimestamp(exp):
            raise_exception()
        user = {
            "id": oid,
            "per": payload.get("per", None),
            "scope": payload.get("scope", None),
        }
        if user is None:
            raise_exception()
        return user
    except jwt.PyJWTError:
        raise_exception()
