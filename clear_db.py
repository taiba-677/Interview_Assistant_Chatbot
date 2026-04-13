import shutil
import os

# Paths from config (manually inferred)
CHROMA_DB_DIR = "data/chroma_db"
UPLOAD_DIR = "data/uploads"

def clear_databases():
    print("--- Clearing Databases ---")

    # Clear ChromaDB
    if os.path.exists(CHROMA_DB_DIR):
        print(f"Deleting ChromaDB directory: {CHROMA_DB_DIR}")
        try:
            shutil.rmtree(CHROMA_DB_DIR)
            print("ChromaDB cleared successfully.")
        except Exception as e:
            print(f"Failed to delete ChromaDB: {e}")
    else:
        print("ChromaDB directory not found.")

    # Optional: Clear Uploads
    if os.path.exists(UPLOAD_DIR):
        print(f"Clearing Uploads directory: {UPLOAD_DIR}")
        try:
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print("Uploads cleared successfully.")
        except Exception as e:
            print(f"Failed to clear Uploads: {e}")
    else:
        print("Uploads directory not found.")

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete all database and upload files? (y/n): ")
    if confirm.lower() == 'y':
        clear_databases()
    else:
        print("Aborted.")
