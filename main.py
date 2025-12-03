from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import db
from routers import auth, todos, admin, users

app = FastAPI()

# This creates $DATABASE_URI database (todosapp.db), using the configuration of db.py & models.py
db.Base.metadata.create_all(bind=db.engine)

# Frontend Setup
templates = Jinja2Templates(directory="templates")
# "Mounting" means adding a complete "independent" application in a specific path. The OpenAPI and docs won't include anything from here
app.mount(path="/static", app=StaticFiles(directory="static"), name="static_files")

@app.get("/")
def test(req: Request):
    return templates.TemplateResponse("home.html" , {"request": req})

@app.get("/login-page")
def render_login_page(req: Request):
    return templates.TemplateResponse("login.html", {"request": req})

# Health check
@app.get("/healthy")
def health_check():
    return {"status": "Healthy"}


# Including backend routers
app.include_router(todos.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)