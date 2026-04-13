import sys
import os

# Add the current directory to sys.path to allow imports
sys.path.append(os.getcwd())

from app.services.prep_chat import PrepChatService

def test_init():
    print("Testing PrepChatService initialization...")
    try:
        service = PrepChatService()
        print("Initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize: {e}")

if __name__ == "__main__":
    test_init()
