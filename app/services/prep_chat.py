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
        old_message: Optional[str] = None
    ) -> Dict[str, Any]:
        
        # 0. Handle Editing: Delete old question/answer if editing
        if old_message:
            db_delete = SessionLocal()
            try:
                from app.models.sql_models import MessagesData
                # Find the user message to be edited
                target_msg = db_delete.query(MessagesData).filter(
                    MessagesData.user_id == user_id,
                    MessagesData.content == old_message,
                    MessagesData.role == "user"
                ).order_by(MessagesData.created_at.desc()).first()

                if target_msg:
                    # Find the assistant message that follows it in the same session
                    next_msg = db_delete.query(MessagesData).filter(
                        MessagesData.session_id == target_msg.session_id,
                        MessagesData.created_at > target_msg.created_at,
                        MessagesData.role == "assistant"
                    ).order_by(MessagesData.created_at.asc()).first()

                    db_delete.delete(target_msg)
                    if next_msg:
                        db_delete.delete(next_msg)
                    db_delete.commit()
            finally:
                db_delete.close()
        
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
                    # final_prompt = f"""
                    # You are a precise Resume Data Extraction Assistant.
                    # Your goal is to extract ONLY the specific information requested by the user from the Resume Context below.

                    # RESUME CONTEXT:
                    # {resume_context}

                    # USER QUESTION: "{user_message}"

                    # STRICT RULES:
                    # 1. **Targeted Extraction**: Extract ONLY the information requested. If the user asks for "skills", do NOT include "education", "experience", or any other unrelated sections.
                    # 2. **Handling Masked Data (PII)**: If the context contains placeholders like [EMAIL_ADDRESS], [PHONE_NUMBER], <EMAIL>, etc., and the user asks for that specific contact info, you MUST respond exactly with: "I don't have access to the information you asked."
                    # 3. **Formatting**:
                    #    - Use **Markdown headings** (e.g., ### Skills) for sections.
                    #    - Use **bullet points** (- ) for lists.
                    #    - Use **bold** for key terms.
                    # 4. **Missing Info**: If the information is not in the context, say "The resume does not provide this information."
                    # 5. **No Hallucinations**: Do not invent any details. Use the exact wording from the resume where possible.
                
                    # """


                  final_prompt = f"""
You are an expert Resume Parsing and Formatting Assistant.

Your job is to extract ONLY the information requested by the user from the resume and present it in a clean, professional CV format.

========================
RESUME CONTEXT:
{resume_context}
========================

USER QUESTION:
"{user_message}"

========================
STRICT RULES:
========================

1. 🎯 TARGETED EXTRACTION
- Extract ONLY what the user asks.
- Do NOT include extra sections.

2. 📄 PROFESSIONAL CV FORMATTING

- The MAIN title should be plain text:
  (no bold, no ALL CAPS, no markdown headings)


- Use **Markdown headings** (e.g., ### Projects, ### Skills, ### Experience).

- Follow STANDARD CV STRUCTURE:

👉 For PROJECTS:
Each project MUST follow this format:

**Project Name**
- Description point 1
- Description point 2
- Description point 3
- **Technologies:** listed on a NEW bullet line

⚠️ IMPORTANT:
- NEVER write Technologies in the same line as description
- ALWAYS put Technologies as the LAST bullet
- Add a blank line between projects

---

👉 For EXPERIENCE:

**Job Title – Company Name**
- Responsibility / achievement
- Responsibility / achievement
- Responsibility / achievement

---

👉 For SKILLS:
- Use bullet points
- Group similar skills if possible

---

👉 For EDUCATION:

**Degree – Institution**
- Additional details (if available)

---

3. 🔒 MASKED / SENSITIVE DATA
If the resume contains placeholders like:
[EMAIL], [PHONE], <EMAIL>, etc.

AND user asks for them → respond EXACTLY:
"I don't have access to the information you asked."

---

4. ❌ NO HALLUCINATION
- Do NOT add anything not present in resume
- Use original wording where possible

---

5. ⚠️ MISSING DATA
If requested info is not present:
"The resume does not provide this information."

---

6. ✨ OUTPUT QUALITY
- Clean spacing
- Consistent bullets
- Professional tone
- No extra explanations

========================
ONLY RETURN THE FINAL ANSWER
========================
"""
                elif "RESPONSE" in intent_type:
                    final_prompt = f"""
                    You are an expert Technical Interviewer focusing on depth and clarity.
                    The user has provided an answer to your previous interview question.
                    
                    RESUME CONTEXT: {resume_context}
                    CHAT HISTORY: {chat_history if chat_history else "No previous history."}
                    USER'S LATEST ANSWER: "{user_message}"

                    GOAL:
                    1. **Acknowledge**: Briefly evaluate the user's answer (strength/weakness) with professional feedback.
                    2. **Follow-up**: Based on the Resume Context, ask ONE new, concise follow-up technical or behavioral question that feels like a natural progression.
                    
                    STRICT RULES:
                    - Use **Markdown formatting**.
                    - Keep it professional and concise.
                    - Do not repeat topics already covered in Chat History.
                    - If the user provides PII or asks about it, follow the same privacy rule: "I don't have access to the information you asked."
                    """
                else:
                    search_results = self.search_service.get_web_links(user_message)
                    references = search_results[:3] 
                    
                    final_prompt = f"""
                    You are a world-class Technical Interviewer and Career Coach.
                    Provide a detailed, professional, and well-formatted answer to the user's general question.
                    
                    SEARCH RESULTS (Context):
                    {search_results if search_results else "No relevant web links found."}
                    
                    CHAT HISTORY: {chat_history if chat_history else "No previous history."}
                    USER QUESTION: "{user_message}"
                    RESUME BACKGROUND: {resume_context}
                    
                    INSTRUCTION:
                    - Use the Search Results to provide up-to-date and accurate industry insights.
                    - Format your response using **Markdown headings**, **bullet points**, and **bold text** for a premium reading experience.
                    - If asked about the user's personal private data not in the resume or masked in it, say: "I don't have access to the information you asked."
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




