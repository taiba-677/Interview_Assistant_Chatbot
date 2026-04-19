from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.services.rag_pipeline import RAGPipeline
from app.db.session import get_db
from app.models.sql_models import ChatSession, Resume, InterviewInteraction

router = APIRouter()


class QuestionRequest(BaseModel):
    user_id: str
    answer: Optional[str] = None

class RenameRequest(BaseModel):
    new_title: str




@router.post("/generate-questions")
def generate_questions(req: QuestionRequest, db: Session = Depends(get_db)):
    try:
        rag = RAGPipeline()
        
        # 1. Find or Create Session
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
                is_active=True
            )
            db.add(session)
            db.flush()

        # 2. If an answer is provided, save it to interview_interactions FIRST
        if req.answer:
            user_interaction = InterviewInteraction(
                user_id=req.user_id,
                session_id=session.session_id,
                role="user",
                content=req.answer
            )
            db.add(user_interaction)

        # 3. Generate Next Question
        questions = rag.generate_questions(req.user_id)
        
        # Update session title if it's the first question
        if not session.title:
            session.title = rag.generate_title(questions)

        session.current_question = questions
        session.question_count += 1
        
        # 4. Save Assistant's Question to interview_interactions
        assistant_interaction = InterviewInteraction(
            user_id=req.user_id,
            session_id=session.session_id,
            role="assistant",
            content=questions
        )
        db.add(assistant_interaction)
        
        db.commit()

        return {"questions": questions}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
def get_all_sessions(db: Session = Depends(get_db)):
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.is_deleted == False
        ).order_by(ChatSession.created_at.desc()).all()

        if not sessions:
            return {"sessions": []}

        response = []
        for session in sessions:
            response.append({
                "session_id": str(session.session_id),
                "user_id": session.user_id,
                "resume_id": str(session.resume_id) if session.resume_id else None,
                "title": session.title if session.title else "Untitled Session",
                "question_count": session.question_count,
                "total_score": session.total_score,
                "is_active": session.is_active,
                "created_at": session.created_at
            })

        return {"sessions": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.patch("/sessions/{session_id}/rename")
def rename_session(session_id: str, req: RenameRequest, db: Session = Depends(get_db)):
    try:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_deleted == False
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.title = req.new_title.strip()
        db.commit()
        return {"message": "Session renamed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    try:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_deleted == False
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.is_deleted = True
        session.is_active = False
        db.commit()
        return {"message": "Session deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/details")
def get_session_details(session_id: str, db: Session = Depends(get_db)):
    try:
        from app.models.sql_models import Evaluation

        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_deleted == False
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Fetch interactions
        interactions = db.query(InterviewInteraction).filter(
            InterviewInteraction.session_id == session_id
        ).order_by(InterviewInteraction.created_at.asc()).all()

        chat_history = [
            {"role": i.role, "content": i.content} for i in interactions
        ]

        # Fetch evaluation if exists
        evaluation = db.query(Evaluation).filter(
            Evaluation.session_id == session_id
        ).first()

        eval_data = None
        if evaluation:
            eval_data = {
                "overall_score": evaluation.overall_score,
                "technical_score": evaluation.technical_score,
                "behavioral_score": evaluation.behavioral_score,
                "summary": evaluation.summary,
                "final_verdict": evaluation.final_verdict,
                "strengths": evaluation.strengths,
                "weaknesses": evaluation.weaknesses,
                "recommendations": evaluation.recommendations
            }

        return {
            "session_id": str(session.session_id),
            "is_active": session.is_active,
            "chat_history": chat_history,
            "evaluation": eval_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))