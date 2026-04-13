from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.prep_chat import PrepChatService

router = APIRouter()


class PrepChatRequest(BaseModel):
    user_id: str
    message: str
    chat_history: list = []


@router.post("/prep-chat")
def prep_chat(req: PrepChatRequest):
    try:
        service = PrepChatService()
        response = service.get_response(
            user_id=req.user_id,
            user_message=req.message,
            chat_history=req.chat_history
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))