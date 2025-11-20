from fastapi import FastAPI, Depends, HTTPException, status, Path
from typing import Annotated
from sqlalchemy.orm import Session
from database import db, models

app = FastAPI()

# This creates $DATABASE_URI database (todos.db), using the configuration of db.py & models.py
models.Base.metadata.create_all(bind=db.engine)

# DEPENDENCY FUNCTION
# When the function is invoked by FastAPI, the returned value is provided to the route handler
def get_db():
    dataB = db.SessionLocal() # getting the Session object, that is bound to our db.engine
    try:
        print('Returning a Session object when generator is called...')
        yield dataB
    finally:
        print('Closing the Session object...')
        dataB.close()

# Annotated: Provides a way to add context-specific metadata to existing types without altering the type itself.
# Annotated[T, x]: T is the base type, x is the metadata. If the tool do not have logic to interpret x, it is treated simply as T
# FastAPI use Annotated to specify dependencies for function parameters.
# Annotated[Session, Depends(get_db)] indicates that the Session type should be resolved using the get_db dependency
# FastAPI is able to call "next(get_db())" in order to get the Session object, and getting to the StopIteration exception, so that it can continue to execute dataB.close()
db_dependency: type[Session] = Annotated[Session, Depends(get_db)]

@app.get("/", status_code=status.HTTP_200_OK)
async def read_all(db_session: db_dependency):
    # all() -> SELECT * FROM todos;
    return db_session.query(models.Todos).all()

@app.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_one(db_session: db_dependency, todo_id: int = Path(gt=0)):
    # filter() -> ... WHERE id = todo_id
    todo_model = db_session.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo not found")

@app.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db_session: db_dependency, todo_validator: models.TodoValidator):
    # **: passing key-values to Todos as parameters
    todo_model = models.Todos(**todo_validator.model_dump())
    db_session.add(todo_model)
    db_session.commit()

@app.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db_session: db_dependency,
                      todo_validator: models.TodoValidator,
                      todo_id: int = Path(gt=0)):
    # filter() -> ... WHERE id = todo_id
    todo_model = db_session.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    # We are sure that our todo_validator has all the todo_object attributes, because FastAPI is validating it with pydantic, thanks to the use of BaseModel
    # If the request doesn't have all the required attributes, FastAPI responds with a 422 status code (Unprocessable Content)
    todo_model.title = todo_validator.title
    todo_model.description = todo_validator.description
    todo_model.priority = todo_validator.priority
    todo_model.completed = todo_validator.completed

    # We have to use the same object, so our ORM understands that we are updating a record
    db_session.add(todo_model)
    db_session.commit()


"""
# Understanding the "get_db" function

db_generator = get_db()
print("----------------")
print('Generator:', db_generator)
print("----------------")
try:
    print('Session:', next(db_generator))
    print("----------------")
    print('Shouldn\'t be printed:', next(db_generator)) # This will generate a StopIteration
except StopIteration as s:
    print('No more Session')
"""

"""
# Little remainder of the yield functionality

import time

def my_range(start, end):
    print('Yield init')
    current = start
    while current < end:
        print('Before yield')
        yield current
        print('After yield')
        current += 1

nums_generator = my_range(1, 5)
for num in nums_generator:
    print(num)
    time.sleep(3)
"""