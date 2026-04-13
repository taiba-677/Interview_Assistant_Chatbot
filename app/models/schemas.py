from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class ChatSessionBase(BaseModel):
    user_id: str
    resume_id: Optional[UUID] = None
    title: Optional[str] = None
    current_question: Optional[str] = None
    question_count: int = 0
    total_score: int = 0
    is_active: bool = True
    final_verdict: Optional[str] = None
    is_deleted: bool = False

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    session_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class EvaluationBase(BaseModel):
    session_id: UUID
    overall_score: int
    technical_score: int
    behavioral_score: int
    summary: str
    final_verdict: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: str

class Evaluation(EvaluationBase):
    evaluation_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
