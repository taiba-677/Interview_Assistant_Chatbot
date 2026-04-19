from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List
from app.core.config import settings

class EvaluationResult(BaseModel):
    overall_score: int = Field(description="Total score out of 100 based on all answers")
    technical_score: int = Field(description="Score out of 10 for technical proficiency")
    behavioral_score: int = Field(description="Score out of 10 for communication and soft skills")
    summary: str = Field(description="High-level executive summary of the performance")
    final_verdict: str = Field(description="Final verdict: hire, consider, or reject")
    strengths: List[str] = Field(description="Key strengths demonstrated during the interview")
    weaknesses: List[str] = Field(description="Areas needing improvement")
    recommendations: str = Field(description="Actionable advice for future interviews")

class EvaluationService:

    def __init__(self):
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3
        )
        self.structured_llm = llm.with_structured_output(EvaluationResult)

    def evaluate_session(self, chat_history: List[dict], user_id: str = None):
        """
        Evaluates the entire interview session based on the chat history.
        """
        prompt = f"""
        You are a Senior Technical Recruiter and Career Coach.
        Analyze the following interview conversation and provide a detailed evaluation.
        
        CONVERSATION HISTORY:
        {chat_history}
        
        Evaluate:
        - Technical depth
        - Behavior
        
        Give:
        - Score /100
        - Final Verdict: 'hire', 'consider', or 'reject'
          * hire: Overall score >= 80
          * consider: Overall score 60-79
          * reject: Overall score < 60
        - Professional, constructive feedback
        
        IMPORTANT: Do NOT include examples like (e.g., ...) in your recommendations, strengths, or weaknesses. Give direct, clear, actionable advice without parenthetical examples.
        
        Only output evaluation.
        """
        response = self.structured_llm.invoke(prompt)
        result = response.model_dump()

        # --- SAVE TO DB LOGIC ---
        if user_id:
            from app.db.session import SessionLocal
            from app.models.sql_models import ChatSession, Evaluation
            
            db = SessionLocal()
            try:
                # Find the most recent session for this user
                session = db.query(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.is_deleted == False).order_by(ChatSession.created_at.desc()).first()
                if session:
                    # Check if evaluation already exists for this session
                    existing_eval = db.query(Evaluation).filter(Evaluation.session_id == session.session_id).first()
                    if existing_eval:
                        db.delete(existing_eval) # Overwrite
                        db.flush() # Force delete execution before subsequent insert
                    
                    db_eval = Evaluation(
                        session_id=session.session_id,
                        overall_score=result.get("overall_score"),
                        technical_score=result.get("technical_score"),
                        behavioral_score=result.get("behavioral_score"),
                        summary=result.get("summary"),
                        final_verdict=result.get("final_verdict"),
                        strengths=result.get("strengths"),
                        weaknesses=result.get("weaknesses"),
                        recommendations=result.get("recommendations")
                    )
                    db.add(db_eval)

                    # Update ChatSession metadata
                    session.total_score = result.get("overall_score")
                    session.final_verdict = result.get("final_verdict")
                    session.is_active = False # Session is now evaluated/complete

                    # ✅ Sync Chat History to interview_interactions
                    from app.models.sql_models import InterviewInteraction
                    # Clear existing for this session to avoid duplicates during final sync
                    db.query(InterviewInteraction).filter(InterviewInteraction.session_id == session.session_id).delete()
                    db.flush()
                    
                    for entry in chat_history:
                        # Handle {"role": "...", "content": "..."} format first
                        role = entry.get("role")
                        content = entry.get("content")
                        
                        if role and content:
                            db.add(InterviewInteraction(
                                user_id=user_id,
                                session_id=session.session_id,
                                role=role,
                                content=content
                            ))
                        else:
                            # Fallback for old custom {"questions": "...", "answers": "..."} format
                            q_text = entry.get("questions")
                            a_text = entry.get("answers")
                            
                            if q_text:
                                db.add(InterviewInteraction(
                                    user_id=user_id,
                                    session_id=session.session_id,
                                    role="assistant",
                                    content=q_text
                                ))
                            if a_text:
                                db.add(InterviewInteraction(
                                    user_id=user_id,
                                    session_id=session.session_id,
                                    role="user",
                                    content=a_text
                                ))

                    db.commit()
            finally:
                db.close()
        # ------------------------

        return result
