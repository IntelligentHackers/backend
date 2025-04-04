import bcrypt
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from fastapi import HTTPException
import jwt
import json
import datetime
from typings.user import UserRole
from database import db
from bson import ObjectId
from bcrypt import checkpw, gensalt, hashpw
from Crypto.Hash import SHA256


class Auth:
    password: str
    time: int


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def check_password(password: str, hashed: str):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


public_key = RSA.import_key(open("rsa_public_key.pem", "rb").read())
private_key = RSA.import_key(open("rsa_private_key.pem", "rb").read())
jwt_private_key = open("aes_key.txt", "r").read()


def rsa_encrypt(plaintext):
    cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
    encrypt_text = cipher.encrypt(bytes(plaintext.encode("utf8")))
    return encrypt_text.hex()


def rsa_decrypt(ciphertext):
    cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
    decrypt_text = cipher.decrypt(bytes.fromhex(ciphertext))
    return decrypt_text.decode("utf8")


def jwt_encode(
    id: str,
    email: str,
    role: UserRole
):
    duration = (
        datetime.timedelta(days=30)
    )
    payload = {
        "iss": "gensync",
        "exp": datetime.datetime.now(datetime.timezone.utc) + duration,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "sub": id,
        "scope": "access_token",
        "role": role,
        "mail": email,
        "jti": str(ObjectId()),
    }
    result = jwt.encode(payload, jwt_private_key, algorithm="HS256")
    return result


def jwt_decode(token):
    return jwt.decode(token, jwt_private_key, algorithms=["HS256"], verify=True)


async def get_renewed_password(id: str, credential: str):
    field = json.loads(rsa_decrypt(credential))
    time = field["time"]
    if time < datetime.datetime.now().timestamp() - 60:
        raise HTTPException(status_code=401, detail="Login expired")
    new_password = hashpw(bytes(field["password"], "utf-8"), gensalt())
    await db.gensync.users.update_one(
        {"_id": ObjectId(id)}, {"$set": {"password": new_password}}
    )


async def validate_by_cert(email: str, cert: str):
    auth_field = json.loads(rsa_decrypt(cert))
    time = auth_field["time"]
    # in a minute
    if time < datetime.datetime.now().timestamp() - 60:
        raise HTTPException(status_code=401, detail="Login expired")
    found = await db.gensync.users.find({"email": email}).to_list(None)
    if len(found) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    user = found[0]
    if checkpw(
        bytes(auth_field["password"], "utf-8"), bytes(user["password"], "utf-8")
    ):
        return jwt_encode(str(found['_id']), email, user["role"])
    else:
        raise HTTPException(status_code=403, detail="Password incorrect")


async def get_hashed_password_by_cert(cert: str):
    auth_field = json.loads(rsa_decrypt(cert))
    time = auth_field["time"]
    # in a minute
    if time < datetime.datetime.now().timestamp() - 60:
        raise HTTPException(status_code=401, detail="Token expired")
    password = auth_field["password"]
    return hashpw(bytes(password, "utf-8"), gensalt()).decode("utf-8")


async def checkpwd(id: str, pwd: str):
    user = await db.gensync.auths.find_one({"_id": ObjectId(id)})
    if checkpw(bytes(pwd, "utf-8"), bytes(user["password"], "utf-8")):
        return True
    return False
