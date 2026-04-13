from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.sql_models import Resume, ChatSession, ChatMessage, Evaluation

def inspect_postgres():
    print("\n--- PostgreSQL Data Inspection ---")
    try:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 1. Resumes
        resumes = session.query(Resume).all()
        print(f"Total Resumes: {len(resumes)}")
        for r in resumes:
            print(f" - ID: {r.resume_id}, User: {r.user_id}, File: {r.filename}")

        # 2. Chat Sessions
        sessions = session.query(ChatSession).all()
        print(f"\nTotal Chat Sessions: {len(sessions)}")
        for s in sessions:
            print(f" - ID: {s.session_id}, User: {s.user_id}, Title: {s.title}")
            print(f"   Question Count: {s.question_count}, Score: {s.total_score}, Active: {s.is_active}")
            print(f"   Current Question: {s.current_question[:100] if s.current_question else 'None'}")
            print(f"   Final Verdict: {s.final_verdict[:100] if s.final_verdict else 'None'}")

        # 3. Chat Messages
        messages = session.query(ChatMessage).all()
        print(f"\nTotal Chat Messages: {len(messages)}")
        for m in messages:
            print(f" - ID: {m.message_id}, Session: {m.session_id}, Role: {m.role}, Content Snippet: {m.content[:50]}...")

        # 4. Evaluations
        evaluations = session.query(Evaluation).all()
        print(f"\nTotal Evaluations: {len(evaluations)}")
        for e in evaluations:
            print(f" - ID: {e.evaluation_id}, Session: {e.session_id}, Score: {e.overall_score}, Summary: {e.summary[:50] if e.summary else 'None'}...")

        session.close()
    except Exception as e:
        print(f"Error inspecting PostgreSQL: {e}")

if __name__ == "__main__":
    inspect_postgres()
