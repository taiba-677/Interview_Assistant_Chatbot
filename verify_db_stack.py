import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from chromadb import PersistentClient
from app.core.config import settings
from app.models.sql_models import Resume
import sys

def verify_postgres():
    print("[POSTGRES] Testing PostgreSQL Connection...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        connection = engine.connect()
        print("[OK] PostgreSQL: Connection Successful!")
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables found: {tables}")
        
        if 'resumes' in tables:
            Session = sessionmaker(bind=engine)
            session = Session()
            count = session.query(Resume).count()
            print(f"Table 'resumes' has {count} record(s).")
            
            if count > 0:
                latest = session.query(Resume).order_by(Resume.created_at.desc()).first()
                print(f"Last Upload: {latest.filename} (User ID: {latest.user_id})")
            session.close()
        else:
            print("[ERROR] 'resumes' table NOT found. Run the FastAPI server to auto-create it.")
            
        connection.close()
    except Exception as e:
        print(f"[ERROR] PostgreSQL Error - {str(e)}")

def verify_chroma():
    print("\n[CHROMA] Testing Chroma DB Connection...")
    try:
        CHROMA_PATH = settings.CHROMA_DB_DIR
        if not os.path.exists(CHROMA_PATH):
            print(f"[WARN] Chroma DB directory not found at: {CHROMA_PATH}")
            return

        client = PersistentClient(path=CHROMA_PATH)
        collections = client.list_collections()
        
        if not collections:
            print("[WARN] No collections found in Chroma DB.")
            return

        print(f"[OK] Chroma DB Connection: Found {len(collections)} collection(s).")
        for coll in collections:
            count = coll.count()
            print(f"Collection: '{coll.name}' - Items: {count}")
            
            if count > 0:
                peek = coll.peek(limit=1)
                metadata = peek['metadatas'][0] if peek['metadatas'] else {}
                print(f"Sample Metadata: {metadata}")
    except Exception as e:
        print(f"[ERROR] Chroma DB Error - {str(e)}")

if __name__ == "__main__":
    print("--- Database Stack Verification ---")
    verify_postgres()
    verify_chroma()
    print("\n--- Verification Complete ---")
