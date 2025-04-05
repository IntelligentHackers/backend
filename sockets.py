import socketio
from procedures.survey.chatting import initiate_conversation, develop_conversation, finalize_output
from pydantic import BaseModel
from enum import Enum
from database import db
from utils.object_id import validate_object_id, get_current_user
import json

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket = socketio.ASGIApp(sio)


class AssistantMessageSendType(Enum):
    completed = "completed"
    processing = "processing"

class AssistantMessageReceiveType(Enum):
    initiate = "initiate"
    chatting = "chatting"

class AssistantMessageReceive(BaseModel):
    receive_type: AssistantMessageReceiveType
    session: str # ObjectId
    user_auth: str
    message: str

class AssistantMessageSend(BaseModel):
    send_type: AssistantMessageSendType
    session: str # ObjectId
    user_auth: str
    message: str


@sio.on('registration_message_send')
async def registration_message_send(sid, message: dict):
    message = AssistantMessageReceive(**message)
    if message.receive_type == AssistantMessageReceiveType.initiate:
        # Keys: lang & email
        data = json.loads(message.message)
        lang = data.get("lang")
        email = data.get("email")
        auth = await db.auths.find_one({'_id': validate_object_id(message.user_auth)})
        if not auth:
            raise Exception('User not found')
        if 'ip' not in auth:
            ip = 'unknown'
        else:
            ip = auth['ip']
        msg, id = await initiate_conversation(lang, email, ip)
        response = AssistantMessageSend(send_type=AssistantMessageSendType.processing, session=id, user_auth=message.user_auth, message=msg)
        await sio.emit('registration_message_receive', response.model_dump_json(), to=sid)
    elif message.receive_type == AssistantMessageReceiveType.chatting:
        msg = await develop_conversation(message.session, message.message)
        # Hardcoded matching, as a special token marks for ending up.
        if msg == '<ok>':
            summarize = await finalize_output(message.session)
            response = AssistantMessageSend(send_type=AssistantMessageSendType.completed, session=message.session, user_auth=message.user_auth, message=json.dumps(summarize))
        else:
            response = AssistantMessageSend(send_type=AssistantMessageSendType.processing, session=message.session, user_auth=message.user_auth, message=msg)
        await sio.emit('registration_message_receive', response.model_dump_json(), to=sid)


@sio.event
async def connect(sid, environ, auth):
    token = auth.get('token')
    await get_current_user(token)
    print(f"connect {sid}")

@sio.event
async def disconnect(sid):
    print(f"disconnect {sid}")
