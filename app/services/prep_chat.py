from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import settings
from app.services.search_service import SearchService
from app.db.session import SessionLocal
from app.models.sql_models import Resume

class PrepChatService:
    def __init__(self) -> None:
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )
        self.db = Chroma(
            persist_directory=settings.CHROMA_DB_DIR,
            embedding_function=self.embeddings,
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1, 
        )
        self.search_service = SearchService()

    def _extract_text(self, response: Any) -> str:
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, str):
                return content.strip()
            elif isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        parts.append(part["text"])
                    else:
                        parts.append(str(part))
                return "\n".join(parts).strip()
            else:
                return str(content).strip()
        return str(response).strip()


    
    def get_response(
        self,
        user_id: str,
        user_message: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        
        # 1. Retrieve Context from Chroma (for search/background)
        retriever = self.db.as_retriever(
            search_kwargs={"k": 5, "filter": {"user_id": user_id}}
        )
        docs = retriever.invoke(user_message)
        chroma_context = "\n\n".join([d.page_content for d in docs]) if docs else "No relevant resume segments found."

        # 2. Determine Intent (Shortcut for Greetings)
        if user_message.lower().strip().strip("!.") == "hi":
            intent_type = "GREETING"
        else:
            intent_prompt = f"""
            Analyze the user message and history to determine the intent:
            - 'RESUME': User is asking for specific facts from their resume (e.g. "What is my GPA?", "Which projects did I do?").
            - 'RESPONSE': User is answering an interview question you previously asked.
            - 'GENERAL': Any other general, technical, or career coaching question.
            
            User Message: "{user_message}"
            Answer only 'RESUME', 'RESPONSE', or 'GENERAL'.
            """
            intent_type = self._extract_text(self.llm.invoke(intent_prompt)).upper()

        references = []
        resume_context = chroma_context

        # 3. DB Operations (Read Resume + Save Chat)
        db = SessionLocal()
        try:
            # A. Fetch Resume
            resume_record = db.query(Resume).filter(Resume.user_id == user_id).first()
            if resume_record:
                resume_context = resume_record.content

            # B. Get or Create Session ID from messages_data (instead of chat_sessions)
            from app.models.sql_models import MessagesData, ChatSession
            import uuid
            
            # 1. For messages_data: Find the most recent active prep session
            last_msg = db.query(MessagesData).filter(
                MessagesData.user_id == user_id, 
                MessagesData.is_active == True,
                MessagesData.is_delete == False
            ).order_by(MessagesData.created_at.desc()).first()

            if last_msg:
                prep_session_id = last_msg.session_id
                session_is_active = last_msg.is_active
                session_title = last_msg.title
                # ✅ If user asks about Resume, force title to "CV Data" even for existing sessions
                if "RESUME" in intent_type:
                    session_title = "CV Data"
            else:
                prep_session_id = uuid.uuid4()
                # ✅ Dynamic Title Generation based on Intent
                if "RESUME" in intent_type:
                    session_title = "CV Data"
                elif intent_type == "GREETING":
                    session_title = "User Greeting"
                else:
                    title_prompt = f"Generate a short, professional topic-based title (max 4 words) for an interview prep chat starting with: '{user_message}'. Return ONLY the title text without quotes."
                    session_title = self._extract_text(self.llm.invoke(title_prompt)).strip('"')
                
                session_is_active = True
            
            # 2. For interview_interactions: Link to the active interview session from chat_sessions
            active_interview = db.query(ChatSession).filter(
                ChatSession.user_id == user_id, 
                ChatSession.is_active == True,
                ChatSession.is_deleted == False
            ).order_by(ChatSession.created_at.desc()).first()
            interview_session_id = active_interview.session_id if active_interview else None

            # ✅ Save User Message to messages_data
            msg_data_user = MessagesData(
                user_id=user_id,
                session_id=prep_session_id,
                is_active=session_is_active,
                is_delete=False,
                title=session_title,
                content=user_message,
                role="user",
                references=None
            )
            db.add(msg_data_user)
            db.commit()

            # 4. Generate Answer based on Intent
            if intent_type == "GREETING":
                answer_text = "Hey! 👋\n\nWhat can I help you with today?"
            else:
                if "RESUME" in intent_type:
                    final_prompt = f"""
                    You are a precise Data Extraction Assistant.
                    Extract EXACT information from the Resume Context below.
                    
                    RULES: No paraphrasing. If missing, say "The resume does not provide this information."
                    
                    Resume Context: {resume_context}
                    User Question: {user_message}
                    """
                elif "RESPONSE" in intent_type:
                    final_prompt = f"""
                    You are an expert Technical Interviewer. 
                    The user just answered your previous question in the Chat History below.
                    
                    GOAL:
                    1. Briefly acknowledge/evaluate the answer.
                    2. Based on the Resume Context, ask ONE new concise, follow-up technical or behavioral question.
                    
                    Rules: Keep it professional and concise. Don't repeat topics.
                    
                    Resume Context: {resume_context}
                    Chat History: {chat_history if chat_history else "No previous history."}
                    User's Latest Answer: {user_message}
                    """
                else:
                    references = self.search_service.get_web_links(user_message)
                    final_prompt = f"""
                    You are an expert Technical Interviewer and Career Coach.
                    Provide a professional answer to the user's general question.
                    
                    Chat History: {chat_history if chat_history else "No previous history."}
                    User Question: {user_message}
                    Resume Context (for background reference): {resume_context}
                    """

                raw_response = self.llm.invoke(final_prompt)
                answer_text = self._extract_text(raw_response)

            # ✅ Save Assistant Message to messages_data only
            msg_data_assistant = MessagesData(
                user_id=user_id,
                session_id=prep_session_id,
                is_active=session_is_active,
                is_delete=False,
                title=session_title,
                content=answer_text,
                role="assistant",
                references=references if references else None
            )
            db.add(msg_data_assistant)

            # ✅ Save Interview-related Interactions to interview_interactions (linked to correct session)
            if "RESPONSE" in intent_type and interview_session_id:
                from app.models.sql_models import InterviewInteraction
                
                # 1. Save User's Answer
                interaction_user = InterviewInteraction(
                    user_id=user_id,
                    session_id=interview_session_id,
                    role="user",
                    content=user_message
                )
                db.add(interaction_user)

                # 2. Save Assistant's Follow-up Question
                interaction_assistant = InterviewInteraction(
                    user_id=user_id,
                    session_id=interview_session_id,
                    role="assistant",
                    content=answer_text
                )
                db.add(interaction_assistant)

            db.commit()

        finally:
            db.close()

        return {
            "answer": answer_text,
            "references": references
        }

