from fastapi import APIRouter, status
from passlib.context import CryptContext
from database import models

router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(user_validator: models.UserValidator):
    user_model = models.Users(
        is_active=True, # added attribute that does not exist in UserValidator
        hashed_password=bcrypt_context.hash(user_validator.password), # added attribute that does not exist in UserValidator
        **user_validator.model_dump(exclude={'password'}) # excluding password, because 'Users' do not have a password attribute
    )

    return user_model