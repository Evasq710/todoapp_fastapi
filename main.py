from fastapi import FastAPI
from database import db
from routers import todos

app = FastAPI()

# This creates $DATABASE_URI database (todos.db), using the configuration of db.py & models.py
db.Base.metadata.create_all(bind=db.engine)

# Including routers
app.include_router(todos.router)