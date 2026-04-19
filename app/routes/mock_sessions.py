from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.sql_models import MessagesData
from pydantic import BaseModel


router = APIRouter(prefix="/mock-sessions", tags=["mock-sessions"])

class MockSessionResponse(BaseModel):
    session_id: str
    user_id: str
    title: str
    created_at: datetime

# GET /mock-sessions - returns all active mock chat sessions
@router.get("", response_model=dict)
def get_mock_sessions(db: Session = Depends(get_db)):
    """
    Returns a list of distinct active chat sessions from messages_data.
    Each session uses the first user message as its title.
    """
    # Subquery to get the first user message for each session
    subquery = (
        db.query(
            MessagesData.session_id,
            func.min(MessagesData.created_at).label("first_created")
        )
        .filter(MessagesData.is_active == True, MessagesData.role == "user")
        .group_by(MessagesData.session_id)
        .subquery()
    )

    # Join to get the title from that first message
    results = (
        db.query(
            MessagesData.session_id,
            MessagesData.user_id,
            func.coalesce(MessagesData.title, "New Chat").label("title"),
            MessagesData.created_at
        )
        .join(
            subquery,
            (MessagesData.session_id == subquery.c.session_id) &
            (MessagesData.created_at == subquery.c.first_created)
        )
        .filter(MessagesData.is_active == True)
        .order_by(MessagesData.created_at.desc())
        .all()
    )

    sessions = [
        {
            "session_id": str(r.session_id),
            "user_id": r.user_id,
            "title": r.title,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in results
    ]
    return {"sessions": sessions}

@router.delete("/{session_id}")
def delete_mock_session(session_id: uuid.UUID, db: Session = Depends(get_db)):

    # Update all messages belonging to this session
    updated_rows = db.query(MessagesData).filter(
        MessagesData.session_id == session_id
    ).update({
        "is_active": False,
        "is_delete": True
    }, synchronize_session=False)

    if updated_rows == 0:
        raise HTTPException(status_code=404, detail="Session not found or already deleted")

    db.commit()
    return {"message": f"Session {session_id} deleted successfully", "rows_affected": updated_rows}



class MessageResponse(BaseModel):
    role: str
    content: str
    references: Optional[dict] = None

# GET /mock-sessions/{session_id}/messages - returns chat history
@router.get("/{session_id}/messages", response_model=dict)
def get_mock_session_messages(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Returns all messages for a given mock session in chronological order.
    """
    messages = (
        db.query(MessagesData)
        .filter(
            MessagesData.session_id == session_id,
            MessagesData.is_active == True
        )
        .order_by(MessagesData.created_at.asc())
        .all()
    )

    if not messages:
        return {"messages": []}

    result = [
        {
            "role": m.role,
            "content": m.content,
            "references": m.references
        }
        for m in messages
    ]
    return {"messages": result}



class RenameRequest(BaseModel):
    new_title: str

@router.patch("/{session_id}/rename")
def rename_mock_session(
    session_id: uuid.UUID,
    request: RenameRequest,
    db: Session = Depends(get_db)
):
    """
    Rename a mock session by updating the title field in messages_data.
    All messages belonging to this session will have their title updated.
    """
    new_title = request.new_title.strip()
    if not new_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    # Update all messages for this session
    updated_rows = db.query(MessagesData).filter(
        MessagesData.session_id == session_id
    ).update({"title": new_title}, synchronize_session=False)

    if updated_rows == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    db.commit()
    return {"message": "Session renamed successfully", "new_title": new_title}