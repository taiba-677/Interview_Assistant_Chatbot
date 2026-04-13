import sqlite3
import os
from chromadb import PersistentClient

# Paths
CHROMA_DB_PATH = "data/chroma_db"

def inspect_chroma():
    print("\n--- ChromaDB (Vector Store) ---")
    if not os.path.exists(CHROMA_DB_PATH):
        print(f"ChromaDB persistent directory not found at: {CHROMA_DB_PATH}")
        return

    client = PersistentClient(path=CHROMA_DB_PATH)
    collections = client.list_collections()
    
    if not collections:
        print("No collections found in ChromaDB.")
        return

    print(f"Found {len(collections)} collection(s):")
    for coll in collections:
        count = coll.count()
        print(f" - Collection: '{coll.name}' - Items: {count}")
        
        if count > 0:
            # Peek at some data
            peek = coll.peek(limit=2)
            print("   Peek data (first 2 items):")
            for i, (id_val, doc, metadata) in enumerate(zip(peek['ids'], peek['documents'], peek['metadatas'])):
                print(f"     [{i}] ID: {id_val}")
                print(f"         Metadata: {metadata}")
                print(f"         Content (first 100 chars): {doc[:100]}...")

def find_sqlite_dbs():
    print("\n--- SQLite Databases ---")
    db_files = []
    for root, dirs, files in os.walk("."):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith((".db", ".sqlite", ".sqlite3")):
                db_files.append(os.path.join(root, file))
    
    if not db_files:
        print("No separate SQLite (.db, .sqlite) files found in the project.")
        return

    for db_path in db_files:
        print(f"Inspecting Database: {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                print("  No tables found in this database.")
            else:
                print(f"  Tables found: {[t[0] for t in tables]}")
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"    - Table '{table_name}': {count} row(s)")
                    
                    if count > 0:
                        cursor.execute(f"PRAGMA table_info({table_name});")
                        cols = [col[1] for col in cursor.fetchall()]
                        print(f"      Columns: {cols}")
                        
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 2;")
                        rows = cursor.fetchall()
                        print("      Sample rows:")
                        for row in rows:
                            print(f"        {row}")
            conn.close()
        except Exception as e:
            print(f"  Error inspecting {db_path}: {e}")

if __name__ == "__main__":
    inspect_chroma()
    find_sqlite_dbs()
