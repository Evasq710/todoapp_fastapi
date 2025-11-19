from fastapi import FastAPI
from database import db, models

app = FastAPI()

# This creates $DATABASE_URI database (todos.db), using the configuration of db.py & models.py
models.Base.metadata.create_all(bind=db.engine)