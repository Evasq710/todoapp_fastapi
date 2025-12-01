from fastapi import FastAPI
from database import db
from routers import auth, todos, admin, users

app = FastAPI()

# This creates $DATABASE_URI database (todosapp.db), using the configuration of db.py & models.py
db.Base.metadata.create_all(bind=db.engine)

# Health check
@app.get("/healthy")
def health_check():
    return {"status": "Healthy"}


# Including routers
app.include_router(todos.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)