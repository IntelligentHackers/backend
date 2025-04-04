from fastapi import APIRouter, Depends
from database import db
from utils.object_id import get_current_user

router = APIRouter()


@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str, page: int = 0, per_page: int = 10, user=Depends(get_current_user)
):
    count = await db.messages.count_documents({"session_id": session_id})
    # sort by time in descending order
    pipeline = [
        {"$match": {"session_id": session_id}},
        {"$sort": {"time": -1}},
        {"$skip": page * per_page},
        {"$limit": per_page},
    ]
    messages = await db.messages.aggregate(pipeline).to_list(length=per_page)
    # reverse the order
    messages.reverse()
    # convert ObjectId to str
    for message in messages:
        message["_id"] = str(message["_id"])
        message["sender"] = str(message["sender"])
        message["session_id"] = str(message["session_id"])
        message["time"] = message["time"].timestamp()

    return {
        "messages": messages,
        "total": count,
    }
