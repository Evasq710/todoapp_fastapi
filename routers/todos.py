from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Annotated
from sqlalchemy import and_
from sqlalchemy.orm import Session
from database import db, models
from utils.tokens import get_logged_in_user

router = APIRouter(
    prefix="/todo",
    tags=["todo"]
)

# Annotated: Provides a way to add context-specific metadata to existing types without altering the type itself.
# Annotated[T, x]: T is the base type, x is the metadata. If the tool do not have logic to interpret x, it is treated simply as T
# FastAPI use Annotated to specify dependencies for function parameters.
# Annotated[Session, Depends(get_db)] indicates that the Session type should be resolved using the get_db dependency
# FastAPI is able to call "next(get_db())" in order to get the Session object, and getting to the StopIteration exception, so that it can continue to execute dataB.close()
db_dependency: type[Session] = Annotated[Session, Depends(db.get_db)]

# Every time this is used as a type, FastAPI will interpret it as a dependency, and will call the get_logged_in_user function.
# The get_logged_in_user function gets the JWT in the Authorization header, validates it and returns the username, user_id and user_role if valid.
# If something is wrong with the JWT, the function will raise an exception that is going to be handled by FastAPI.
user_dependency: type[dict] = Annotated[dict, Depends(get_logged_in_user)]

@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user_data: user_dependency, db_session: db_dependency):
    # If the code enters here, the app was able to obtain the user data from a valid JWT, thanks to the user_dependency
    # user_data { 'username', 'user_id', 'user_role' }
    return db_session.query(models.Todos).filter(models.Todos.owner_id == user_data.get("user_id")).all()

@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def read_one(user_data: user_dependency, db_session: db_dependency, todo_id: int = Path(gt=0)):
    # If the code enters here, the app was able to obtain the user data from a valid JWT, thanks to the user_dependency
    # user_data { 'username', 'user_id', 'user_role' }
    todo_model = (db_session.query(models.Todos)
                  .filter(and_(models.Todos.id == todo_id, models.Todos.owner_id == user_data.get("user_id")))
                  .first())
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo not found")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(db_session: db_dependency, user_data: user_dependency,
                      todo_validator: models.TodoValidator):
    # If the code enters here, it means that the app was able to obtain the user data from a valid JWT, thanks to the user_dependency
    # user_data { 'username', 'user_id', 'user_role' }
    # **: passing key-values to Todos as parameters
    todo_model = models.Todos(
        owner_id=user_data.get("user_id"),
        **todo_validator.model_dump()
    )
    db_session.add(todo_model)
    db_session.commit()

@router.put("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user_data: user_dependency, db_session: db_dependency,
                      todo_validator: models.TodoValidator,
                      todo_id: int = Path(gt=0)):
    # If the code enters here, the app was able to obtain the user data from a valid JWT, thanks to the user_dependency
    # user_data { 'username', 'user_id', 'user_role' }
    todo_model = (db_session.query(models.Todos)
                  .filter(and_(models.Todos.id == todo_id, models.Todos.owner_id == user_data.get("user_id")))
                  .first())
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

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user_data: user_dependency, db_session: db_dependency, todo_id: int = Path(gt=0)):
    # If the code enters here, the app was able to obtain the user data from a valid JWT, thanks to the user_dependency
    # user_data { 'username', 'user_id', 'user_role' }
    todo_model = (db_session.query(models.Todos)
                  .filter(and_(models.Todos.id == todo_id, models.Todos.owner_id == user_data.get("user_id")))
                  .first())
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db_session.delete(todo_model)
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