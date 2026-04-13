from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.session import Base

class Resume(Base):
    __tablename__ = "resumes"

    resume_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True, nullable=False)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # Masked text
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("ChatSession", back_populates="resume")

    def __repr__(self):
        return f"<Resume(resume_id={self.resume_id}, user_id={self.user_id}, filename={self.filename})>"

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True, nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.resume_id"))
    
    title = Column(String, nullable=True)
    current_question = Column(Text, nullable=True)
    question_count = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    final_verdict = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="sessions")
    evaluation = relationship("Evaluation", back_populates="session", uselist=False, cascade="all, delete-orphan")

class Evaluation(Base):
    __tablename__ = "evaluations"

    evaluation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.session_id"), unique=True)
    overall_score = Column(Integer)
    technical_score = Column(Integer)
    behavioral_score = Column(Integer)
    summary = Column(Text)
    final_verdict = Column(String)
    strengths = Column(JSON)  # Stores List[str]
    weaknesses = Column(JSON)  # Stores List[str]
    recommendations = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="evaluation")

class InterviewInteraction(Base):
    __tablename__ = "interview_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.session_id"))
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession")

class MessagesData(Base):
    __tablename__ = "messages_data"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False) 
    session_id = Column(UUID(as_uuid=True), nullable=False)
    is_active = Column(Boolean, default=True)
    is_delete = Column(Boolean, default=False)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    references = Column(JSON, nullable=True) # For list of links
    role = Column(String, nullable=False)    # 'user' or 'assistant'
    created_at = Column(DateTime, default=datetime.utcnow)
