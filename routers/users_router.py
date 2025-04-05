import json
import random
from datetime import datetime
from io import BytesIO
from PIL import Image
from bcrypt import hashpw, gensalt
from bson import ObjectId
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from utils.cert import validate_by_cert, rsa_decrypt
from typings.auth import Auth
from database import db
from utils.ip import get_user_ip
from utils.object_id import validate_object_id, get_current_user

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB
ALLOWED_FORMATS = {"jpeg", "png"}


def validate_image(file: bytes) -> str:
    try:
        img = Image.open(BytesIO(file))
        image_format = img.format.lower()
        if image_format not in ALLOWED_FORMATS:
            raise ValueError("Unsupported file format.")
        return image_format
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.")


router = APIRouter()


class AuthUser(BaseModel):
    email: str
    credential: str


@router.post("")
async def create_user(user: AuthUser, ip=Depends(get_user_ip)):
    if await db.auths.find_one({'email': user.email}) is not None:
        return RedirectResponse(url='/api/users/auth')
    auth_field = json.loads(rsa_decrypt(user.credential))
    time = auth_field["time"]
    # in a minute
    if time < datetime.now().timestamp() - 60:
        raise HTTPException(status_code=400, detail="Request expired")
    # Check if email already exists
    if await db.auths.count_documents({"email": user.email}) > 0:
        raise HTTPException(status_code=400, detail="Email already exists")
    auth = Auth(
        _id=ObjectId(),
        email=user.email,
        password_hash=hashpw(auth_field["password"].encode("utf-8"), gensalt()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        register_ip=ip
    )
    user_auth = auth.model_dump()
    result = await db.auths.insert_one(user_auth)
    return JSONResponse(status_code=201, content=str(result.inserted_id))


@router.post("/auth")
async def auth_user(auth: AuthUser):
    email = auth.email
    credential = auth.credential

    result, user_id = await validate_by_cert(email, credential)

    return JSONResponse({
        "token": result,
        "_id": user_id,
    })


@router.post("/{user_id}/avatar")
async def upload_avatar(user_id: str, file: UploadFile = File(...)):
    contents = await file.read()

    # Check file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 1MB.")

    image_format = validate_image(contents)

    await db.users.update_one(
        {"_id": validate_object_id(user_id)},
        {"$set": {"avatar": contents, "format": image_format}},
        upsert=True,
    )

    return JSONResponse(content={"message": "Avatar uploaded successfully."})


@router.get("/{user_id}/sessions")
async def get_user_sessions(
    user_id: str, page: int, per_page: int, search: str, user=Depends(get_current_user)
):
    if user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    count = await db.sessions.count_documents(
        {"participants": validate_object_id(user_id)}
    )
    pipeline = [
        {
            "$match": {
                "participants": validate_object_id(user_id),
                "$or": [
                    {"title": {"$regex": search, "$options": "i"}},
                    {"last.message": {"$regex": search, "$options": "i"}},
                ],
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "participants",
                "foreignField": "_id",
                "as": "participants_info",
            }
        },
        {
            "$unwind": {
                "path": "$participants_info",
                "preserveNullAndEmptyArrays": True,
            }
        },
        {
            "$project": {
                "_id": 1,
                "participants_info.email": 1,
                "last": 1,
                "title": 1,
            }
        },
        {"$sort": {"last.time": -1}},
        {"$skip": page * per_page},
        {"$limit": per_page},
    ]
    sessions = await db.sessions.aggregate(pipeline).to_list(length=None)
    for session in sessions:
        session["participants_info"] = [
            p["email"] for p in session["participants_info"]
        ]
        if session["last"]:
            session["last"]["sender"] = str(session["last"]["sender"])

    return {
        "sessions": sessions,
        "total": count,
    }


@router.get("")
async def recommend_user(
    user=Depends(get_current_user), page: int = 1, per_page: int = 1
):
    """
    This function should return recommended users based on some criteria.
    But the model is under training yet, We should randomly select.
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be greater than 0")

    fetched = await db.users.find({}).to_list(length=None)

    result = random.choice(fetched)

    while str(result["_id"]) == user["id"]:
        # Ensure we don't recommend the current user
        result = random.choice(fetched)

    result["_id"] = str(result["_id"])

    return result
