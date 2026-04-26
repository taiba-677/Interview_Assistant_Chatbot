# 💼 AI Interview Assistant Chatbot

A powerful, AI-driven application designed to help job seekers prepare for interviews using their own resumes. This project combines a **FastAPI** backend with a **Streamlit** frontend, leveraging **Google Gemini** for intelligent resume analysis, mock interviews, and performance evaluation.

## 🚀 Features

**📄 Resume-Centric Preparation**: Upload your PDF resume, and the AI will tailor all questions and advice based on your specific background and skills.

**💬 Mock Interview Mode**: A free-form chat interface where you can ask questions about your resume, get career advice, or practice answering specific technical questions.

**🎯 Structured Interview Session**: A formal 6-question interview simulation that tests both technical and behavioral aspects.

**📊 Detailed Evaluation**: Get an instant performance report with:
  - Overall score (%)
  - Technical & Behavioral ratings
  - Strengths and areas for improvement
  - Professional recommendations

**🔒 Privacy First**: Integrated PII masking ensures sensitive contact information (emails, phone numbers) is handled securely.

**🔍 Web-Enhanced Insights**: Uses real-time web search (Tavily) to provide up-to-date industry standards and technical information.

**📂 Session Management**: Save, rename, and manage multiple preparation sessions for different job roles.

## 🛠️ Tech Stack

**Frontend**: Streamlit (Python-based UI)
**Backend**: FastAPI (High-performance API)
**AI Models**: Google Gemini (Pro & Flash) for text generation and embeddings.
**Database**: 
  - **SQLAlchemy**: For session and message persistence (SQLite/PostgreSQL).
  - **ChromaDB**: Vector database for RAG (Retrieval-Augmented Generation).
- **RAG Pipeline**: LangChain for document processing and intelligent retrieval.

## 📋 Prerequisites

- Python 3.9+
- Google Gemini API Key
- Tavily API Key (for web search)

## ⚙️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Interview_Assistant_Chatbot.git
   cd Interview_Assistant_Chatbot
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory and add the following:
   ```env
   GEMINI_API_KEY=your_gemini_key
   TAVILY_API_KEY=your_tavily_key
   DATABASE_URL=sqlite:///./interview_bot.db
   BACKEND_URL=http://localhost:8000
   ```

## 🏃 How to Run

1. **Start the Backend**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Start the Frontend**:
   ```bash
   streamlit run frontend/app.py
   ```

3. Open your browser and navigate to the local Streamlit URL (usually `http://localhost:8501`).

