from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.rag_pipeline import RAGPipeline
from app.db.session import get_db
from app.models.sql_models import ChatSession, Resume, InterviewInteraction

router = APIRouter()


class QuestionRequest(BaseModel):
    user_id: str


@router.post("/generate-questions")
def generate_questions(req: QuestionRequest, db: Session = Depends(get_db)):
    try:
        rag = RAGPipeline()
        questions = rag.generate_questions(req.user_id)

        # Update or Create Chat Session in DB
        session = db.query(ChatSession).filter(
            ChatSession.user_id == req.user_id, 
            ChatSession.is_active == True,
            ChatSession.is_deleted == False
        ).order_by(ChatSession.created_at.desc()).first()

        if not session:
            resume = db.query(Resume).filter(Resume.user_id == req.user_id).first()
            session = ChatSession(
                user_id=req.user_id,
                resume_id=resume.resume_id if resume else None,
                title=rag.generate_title(questions),
                is_active=True
            )
            db.add(session)
            db.flush()

        session.current_question = questions
        session.question_count += 1
        
        # ✅ Save to New Table: interview_interactions
        interaction = InterviewInteraction(
            user_id=req.user_id,
            session_id=session.session_id,
            role="assistant",
            content=questions
        )
        db.add(interaction)
        
        db.commit()

        return {"questions": questions}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))