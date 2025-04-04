from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typings.selection import Selection, SelectionResult
from typings.session import Session
from database import db
from utils.object_id import validate_object_id, get_current_user

router = APIRouter()


class SelectionRequest(BaseModel):
    object: str
    action: SelectionResult


@router.post("")
async def record_selection(selection: SelectionRequest, user=Depends(get_current_user)):
    # Validate the object ID
    try:
        object_id = validate_object_id(selection.object)
    except HTTPException as e:
        raise HTTPException(status_code=400, detail="Invalid object ID") from e

    action = selection.action

    # Create a new selection record
    selection = Selection(
        _id=ObjectId(),
        subject=validate_object_id(user['id']),
        object=validate_object_id(object_id),
        result=selection.action,
    )

    selection = selection.model_dump()

    del selection['_id']

    # Insert the selection into the database
    result = await db.selections.insert_one(selection)

    session_id = ''

    if action == SelectionResult.approved:
        session = Session(_id=ObjectId(), participants=[validate_object_id(object_id), validate_object_id(user['id'])],
                          last=None, title='')
        session = session.model_dump()
        del session['_id']
        # Insert the session into the database
        session_result = await db.sessions.insert_one(session)
        session_id = str(session_result.inserted_id)

    return {
        'selection': str(result.inserted_id),
        'session': session_id if action == SelectionResult.approved else None,
    }
