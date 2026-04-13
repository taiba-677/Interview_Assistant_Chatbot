from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from app.core.config import settings


class RAGPipeline:

    def __init__(self):
        try:
            # ✅ Embeddings
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=settings.GEMINI_API_KEY
            )

            # ✅ Load existing Chroma DB
            self.db = Chroma(
                persist_directory=settings.CHROMA_DB_DIR,
                embedding_function=self.embeddings
            )

            # ✅ LLM (FIXED MODEL)
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite", 
                google_api_key=settings.GEMINI_API_KEY,
                temperature=1
            )

        except Exception as e:
            raise Exception(f"Initialization Error: {str(e)}")

    def generate_questions(self, user_id: str):

        try:
            # ✅ Retriever with filter
            retriever = self.db.as_retriever(
                search_kwargs={
                    "k": 4,
                    "filter": {"user_id": user_id}
                }
            )

            # ✅ Fetch docs
            docs = retriever.invoke("skills experience projects")

            # ❗ If no docs found
            if not docs:
                return "❌ No resume data found. Please upload CV again."

            # ✅ Build context
            context = "\n\n".join([doc.page_content for doc in docs])

            # ✅ Prompt
            
            prompt = f"""
You are a senior technical interviewer conducting a live interview.

Ask ONE sharp, specific interview question based on this candidate's resume.

Rules:
- Ask exactly 1 question — nothing more
- Specific to THIS candidate's real projects, tools, or experience
- Never repeat a topic already covered
- Max 2 sentences, no numbering, no labels, no explanation
- Prefer scenario-based over definitions
  BAD: "What is Redis?"
  GOOD: "In your auction platform, how did Redis and Celery coordinate to expire auctions?"
- Don't ask same concept, intent of questions again   
Resume:
{context}
"""

            # ✅ LLM call
            response = self.llm.invoke(prompt)

            content = response.content
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        parts.append(part["text"])
                    else:
                        parts.append(str(part))
                return "\n".join(parts).strip()
            
            return str(content).strip()

        except Exception as e:
            return f"❌ RAG Error: {str(e)}"

    def generate_title(self, text_input: str):
        try:
            prompt = f"Generate a short, professional 3-5 word title for an interview session based on this: '{text_input[:200]}'. Return only the title text, no quotes."
            response = self.llm.invoke(prompt)
            return str(response.content).strip().strip('"')
        except:
            return "Interview Session"