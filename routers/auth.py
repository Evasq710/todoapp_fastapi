from fastapi import APIRouter, status, Depends, HTTPException
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import models, db

router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

# Annotated[T, x]: T is the base type, x is the metadata. If the tool do not have logic to interpret x, it is treated simply as T
# Annotated[Session, Depends(get_db)] indicates that the Session type should be resolved using the get_db dependency
db_dependency: type[Session] = Annotated[Session, Depends(get_db)]

@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(db_session: db_dependency, user_validator: models.UserValidator):
    user_model = models.Users(
        is_active=True, # added attribute that does not exist in UserValidator
        hashed_password=bcrypt_context.hash(user_validator.password), # added attribute that does not exist in UserValidator
        **user_validator.model_dump(exclude={'password'}) # excluding password, because 'Users' do not have a password attribute
    )

    try:
        db_session.add(user_model)
        db_session.commit()
    except IntegrityError as err:
        db_session.rollback()
        print('Integrity Error:', str(err))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists!")
    except Exception as err:
        db_session.rollback()
        print('Unexpected Error:', str(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))