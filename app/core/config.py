# import os
# from dotenv import load_dotenv

# load_dotenv()

# class Settings:
#     OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# settings = Settings()



# new

# import os
# from dotenv import load_dotenv

# load_dotenv()


# class Settings:
#     def __init__(self):
#         self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#         # Future configs (keep ready)
#         self.CHROMA_DB_DIR = "data/chroma_db"
#         self.UPLOAD_DIR = "data/uploads"

#         # Validate required variables
#         self._validate()

#     def _validate(self):
#         if not self.OPENAI_API_KEY:
#             raise ValueError("OPENAI_API_KEY is not set in .env file")


# settings = Settings()



# gemini open key


import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        # API KEYS
        # self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

        # Paths
        self.CHROMA_DB_DIR = "data/chroma_db"
        self.UPLOAD_DIR = "data/uploads"
        self.DATABASE_URL = os.getenv("DATABASE_URL")

        # Validate
        self._validate()

    def _validate(self):
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in .env file")

        if not self.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is not set in .env file")

        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is not set in .env file")

settings = Settings()
