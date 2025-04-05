import socketio

from utils.object_id import get_current_user

sio = socketio.AsyncServer(async_mode="asgi")
socket = socketio.ASGIApp(sio)


@sio.event
async def connect(sid, token: str):
    await get_current_user(token)
    print(f"connect {sid}")

@sio.event
async def disconnect(sid):
    print(f"disconnect {sid}")
