import sys
import os

# Add the current directory to sys.path to allow imports
sys.path.append(os.getcwd())

from app.services.evaluation import EvaluationService

def test_evaluation_direct():
    service = EvaluationService()
    user_id = "d8eca59b-5344-40b6-ae31-100d1d898fd1"
    chat_history = [
        {"role": "assistant", "content": "How are you?"},
        {"role": "user", "content": "I am fine, thanks."}
    ]
    print("Directly calling evaluate_session...")
    try:
        result = service.evaluate_session(chat_history, user_id=user_id)
        print("Success!")
        print(result)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_evaluation_direct()
