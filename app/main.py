from fastapi import FastAPI
from app.routes import upload
from app.core.config import settings
from app.routes import interview

from app.routes import evaluation

from app.routes import prep_chat
from app.db.session import engine, Base
from app.models import sql_models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Interview Chatbot")

@app.get("/")
def home():
    return {"message": "Server running"}

app.include_router(upload.router)
app.include_router(interview.router)
app.include_router(evaluation.router)

app.include_router(prep_chat.router)