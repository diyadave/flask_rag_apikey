import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

class Config:
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
    BOOKS_DIR = os.path.join(BASE_DIR, 'books')
    FAISS_DB_DIR = os.path.join(BASE_DIR, 'faiss_db')
    
    @staticmethod
    def init_app(app):
        pass