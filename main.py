from fastapi import FastAPI
from database import db
from routers import auth, todos, admin

app = FastAPI()

# This creates $DATABASE_URI database (todosapp.db), using the configuration of db.py & models.py
db.Base.metadata.create_all(bind=db.engine)

# Including routers
app.include_router(todos.router)
app.include_router(auth.router)
app.include_router(admin.router)