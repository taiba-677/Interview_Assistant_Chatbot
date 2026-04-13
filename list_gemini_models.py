import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY not found in .env")
else:
    try:
        genai.configure(api_key=api_key)
        print("Checking available models...")
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not models:
            print("No models found with 'generateContent' support.")
        else:
            print("Successfully found models:")
            for m in models:
                print(f" - {m}")
    except Exception as e:
        print(f"Error listing models: {str(e)}")
