from datetime import timedelta
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import models, db
from utils import  tokens

router = APIRouter(
    prefix=tokens.PREFIX,
    tags=["auth"],
)

# Variables for JWTs creation
ACCESS_TOKEN_EXPIRE_MINUTES = 10
REFRESH_TOKEN_EXPIRE_DAYS = 2

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Annotated[T, x]: T is the base type, x is the metadata. If the tool do not have logic to interpret x, it is treated simply as T
# Annotated[Session, Depends(get_db)] indicates that the Session type should be resolved using the get_db dependency
db_dependency: type[Session] = Annotated[Session, Depends(db.get_db)]


# Every time this is used as a type, FastAPI will interpret it as a dependency, and will call the get_user_from_refresh_token function.
# The get_user_from_refresh_token function do the following things:
# - Gets the JWT in the Authorization header
# - Validates it and deletes it from the database
# - Returns the JWT user_data
# - If the refresh token is not in the database, it is considered INVALID
# If something is wrong with the JWT, the function will raise an exception that is going to be handled by FastAPI.
token_dependency: type[dict] = Annotated[dict, Depends(tokens.get_payload_from_refresh_token)]


def authenticate_user(username: str, password: str, db_session: Session) -> models.Users | None:
    user: models.Users | None = db_session.query(models.Users).filter(models.Users.username == username).first()
    if user is None or not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db_session: db_dependency, user_validator: models.UserValidator):
    user_model = models.Users(
        is_active=True, # added attribute that does not exist in UserValidator
        hashed_password=bcrypt_context.hash(user_validator.password), # added attribute that does not exist in UserValidator
        **user_validator.model_dump(exclude={'password'}) # excluding password, because 'Users' do not have a password attribute
        # role attribute is assigned to 'user' by default
        # TODO: Admins creation only by other admins.
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

# OAuth 2.0: an open standard for authorization that allows a third-party app to access limited user data, without exposing the user's password.
# OAuth2PasswordRequestForm is a CLASS DEPENDENCY provided in FastAPI, for handling form-based authentication. That's why we use Depends(). It declares a FastAPI dependency.
# The response_model allows Swagger to add documentation of the endpoint response
@router.post(tokens.TOKEN_URL, response_model=models.TokenResponse, status_code=status.HTTP_200_OK)
async def login_for_access_token(db_session: db_dependency,
                                 form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # form_data: {'grant_type', 'username', 'password', 'scopes', 'client_id', 'client_secret'}

    user = authenticate_user(form_data.username, form_data.password, db_session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed authentication")

    # FLOW 1, ASSUMING THAT THE USER SEND THE ROLE(S) THROUGH THE FORM DATA
    # For this, we would have to add valid scopes to oauth2_bearer, in order to enable the scopes selection on the Swagger documentation

    # FLOW 2, SENDING THE ROLE THAT THE USER ALREADY HAS IN THE DATABASE
    user_data = {
        'username': user.username,
        'user_id': user.id,
        'user_role': user.role,
    }

    access_token = tokens.create_jwt(
        user_data=user_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        db_session=db_session
    )
    refresh_token = tokens.create_jwt(
        user_data=user_data,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        db_session=db_session,
        is_refresh_token=True
    )

    """
    Bearer Authentication:
    When a user or system presents a bearer token to access a resource, they don't need to provide any other form of identification.
    Whoever "bears" the token can access the associated resources, making it crucial to protect the token.
    """
    return {
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }

@router.get(tokens.REFRESH_URL, response_model=models.TokenResponse, status_code=status.HTTP_200_OK)
async def get_new_access_token(rt_payload: token_dependency, db_session: db_dependency):
    # If the code enters here, the app was able to obtain the payload from a valid refresh JWT, thanks to the token_dependency
    # REFRESH TOKENS ROTATION: At this point, the used refresh token is already deleted from the database

    new_access_token = tokens.create_jwt(
        user_data=rt_payload.get('user'),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        db_session=db_session
    )

    # Preventing refresh token's lifetime extension beyond the lifetime of the initial refresh token
    new_refresh_token = tokens.create_jwt(
        user_data=rt_payload.get('user'),
        previous_expiry=rt_payload.get('exp'),
        db_session=db_session,
        is_refresh_token=True
    )
    
    return {
        'message': 'Valid refresh token',
        'access_token': new_access_token,
        'refresh_token': new_refresh_token,
        'token_type': 'bearer',
    }

