import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")

engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}) # allowing multiple threads to connect to our database

# Autocommit dictates whether individual SQL statements are automatically committed to the database.
# Autoflush dictates whether in-memory object changes are automatically written to the database connection before queries, ensuring data consistency within a transaction.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()