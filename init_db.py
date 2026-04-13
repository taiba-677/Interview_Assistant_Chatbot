from app.db.session import engine, Base
from app.models.sql_models import Resume, ChatSession, ChatMessage, Evaluation

def init_db():
    print("Creating all tables in the database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    init_db()
