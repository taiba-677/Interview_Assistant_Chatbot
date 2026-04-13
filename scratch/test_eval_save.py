import requests

BASE_URL = "http://127.0.0.1:8000"

# Test user from current DB
USER_ID = "079321c0-04f7-446f-a16b-cac36b838075"

print("--- Testing /evaluate-session with user_id ---")
payload = {
    "user_id": USER_ID,
    "chat_history": [
        {
            "questions": "In your real-time auction platform, how did you ensure the WebSocket connection remained stable under high traffic?",
            "answers": "Ensured stability using load-balanced WebSocket servers, connection pooling, and heartbeat/ping mechanisms."
        }
    ]
}

response = requests.post(f"{BASE_URL}/evaluate-session", json=payload)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Score: {data['evaluation']['overall_score']}")
    print("SUCCESS - Now checking DB...")
else:
    print(f"Error: {response.text}")
