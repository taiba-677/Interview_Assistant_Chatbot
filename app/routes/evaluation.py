from fastapi import APIRouter
from pydantic import BaseModel
from app.services.evaluation import EvaluationService

router = APIRouter()

class SessionEvaluationRequest(BaseModel):
    user_id: str = None
    chat_history: list

@router.post("/evaluate-session")
def evaluate_session(req: SessionEvaluationRequest):
    service = EvaluationService()
    result = service.evaluate_session(
        chat_history=req.chat_history,
        user_id=req.user_id
    )
    return {"evaluation": result}