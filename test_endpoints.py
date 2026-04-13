import requests

BASE_URL = "http://127.0.0.1:8000"
USER_ID = "d8eca59b-5344-40b6-ae31-100d1d898fd1"  # Updated active ID

def test_interview_flow():
    print("--- Testing Interview Flow (Next Question) ---")
    payload = {
        "user_id": USER_ID,
        "message": "I have experience in Python and FastAPI from my previous job at TechCorp.",
        "chat_history": [
            {"role": "assistant", "content": "Can you tell me about your experience with backend development?"}
        ]
    }
    response = requests.post(f"{BASE_URL}/prep-chat", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"AI Response: {data['response']['answer']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_evaluation_session():
    print("\n--- Testing Session Evaluation ---")
    payload = {
        "user_id": USER_ID, # Added
        "chat_history": [
            {"role": "assistant", "content": "Can you tell me about your experience with backend development?"},
            {"role": "user", "content": "I have 3 years of experience in Python and FastAPI. I built REST APIs for a fintech startup."},
            {"role": "assistant", "content": "That sounds great. Which database did you use?"},
            {"role": "user", "content": "We used PostgreSQL and Redis for caching."}
        ]
    }
    response = requests.post(f"{BASE_URL}/evaluate-session", json=payload)
    if response.status_code == 200:
        data = response.json()
        evaluation = data['evaluation']
        print(f"Overall Score: {evaluation['overall_score']}")
        print(f"Technical Score: {evaluation['technical_score']}")
        print(f"Summary: {evaluation['summary']}")
        print(f"Strengths: {evaluation['strengths']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_interview_flow()
    test_evaluation_session()
