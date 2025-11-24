from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import db, models
from routers.auth import get_current_user

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DEPENDENCY FUNCTION
# When the function is invoked by FastAPI, the returned value is provided to the route handler
def get_db():
    dataB = db.SessionLocal() # getting the Session object, that is bound to our db.engine
    try:
        yield dataB
    finally:
        dataB.close()

# Annotated[T, x]: T is the base type, x is the metadata. If the tool do not have logic to interpret x, it is treated simply as T
# Annotated[Session, Depends(get_db)] indicates that the Session type should be resolved using the get_db dependency
db_dependency: type[Session] = Annotated[Session, Depends(get_db)]

# Every time this is used as a type, FastAPI will interpret it as a dependency, and will call the get_current_user function.
# The get_current_user function gets the JWT in the Authorization header, validates it and returns the username, user_id and user_role if valid.
# If something is wrong with the JWT, the function will raise an exception that is going to be handled by FastAPI.
user_dependency: type[dict] = Annotated[dict, Depends(get_current_user)]


@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(user_data: user_dependency, db_session: db_dependency):
    user_model = db_session.query(models.Users).filter(models.Users.id == user_data.get("user_id")).first()

    if user_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user_model

@router.put("/change_password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user_data: user_dependency, db_session: db_dependency, pass_body: models.UserVerification):
    user_model: models.Users | None = db_session.query(models.Users).filter(models.Users.id == user_data.get("user_id")).first()

    if user_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not bcrypt_context.verify(pass_body.old_password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Error on password change")

    user_model.hashed_password = bcrypt_context.hash(pass_body.new_password)
    db_session.add(user_model)
    db_session.commit()

