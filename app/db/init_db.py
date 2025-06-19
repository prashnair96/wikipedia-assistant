import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from app.db.models import Base

# Load environment variables from .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("Done.")

if __name__ == "__main__":
    init_db()
