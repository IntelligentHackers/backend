import json
from datetime import datetime
from bcrypt import hashpw, gensalt
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.cert import validate_by_cert, rsa_decrypt
from typings.auth import Auth
from database import db


router = APIRouter()


@router.post("/assistant")
async def create_assistant():
    pass
