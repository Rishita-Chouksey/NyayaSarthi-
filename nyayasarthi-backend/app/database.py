"""
Sets up the connection to PostgreSQL.
Every other file that needs to talk to the database imports `get_db` from here.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nyayasarthi:nyayasarthi@localhost:5432/nyayasarthi")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI calls this before running any endpoint that needs the database,
    and makes sure the connection is closed afterwards even if something goes wrong."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
