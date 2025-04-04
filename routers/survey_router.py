from fastapi import APIRouter


router = APIRouter()


@router.post("/assistant")
async def create_assistant():
    pass
