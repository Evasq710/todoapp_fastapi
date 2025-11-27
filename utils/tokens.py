import os, uuid, jwt
from typing import Annotated
from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import db, models

# Variables for JWTs creation
# openssl rand -hex 32 | pbcopy
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Routes for ACCESS TOKENS and REFRESH TOKENS
PREFIX = "/auth"
TOKEN_URL = "/login"
REFRESH_URL = "/refresh"

# Annotated[T, x]: T is the base type, x is the metadata. If the tool do not have logic to interpret x, it is treated simply as T
# Annotated[Session, Depends(get_db)] indicates that the Session type should be resolved using the get_db dependency
db_dependency: type[Session] = Annotated[Session, Depends(db.get_db)]

# OAuth2PasswordBearer is a security dependency that handles OAuth2 token authentication using the password flow.
# It tells the application to expect a token in the Authorization: Bearer <token> header
# It also configures the OpenAPI schema and documentation to include an "Authorize" button for testing.
# The tokenUrl specifies the endpoint where the client should send the username and password to obtain an access token.
# When a user interacts with the Swagger UI and enters their credentials, the OAuth2PasswordBearer logic uses this tokenUrl to send a POST request with those credentials to that specific endpoint to retrieve the bearer token.
oauth2_bearer = OAuth2PasswordBearer(tokenUrl=PREFIX+TOKEN_URL, refreshUrl=PREFIX+REFRESH_URL)


def add_jwt_to_db(token: str, user_data: dict, expires_at: datetime, db_session: Session):
    new_token = models.RefreshTokens(
        user_id=user_data.get('user_id'),
        refresh_token=token,
        expires_at=expires_at, # Is recommended to execute clean-up scripts to delete expired refresh tokens from the database
    )
    db_session.add(new_token)
    db_session.commit()


def delete_jwt_from_db(token: str, db_session: Session):
    token_model = db_session.query(models.RefreshTokens).filter(models.RefreshTokens.refresh_token == token).first()
    if token_model is not None:
        db_session.delete(token_model)
        db_session.commit()


def is_valid_refresh_token(refresh_token: str, user_id: int, db_session: Session) -> bool:
    # Making sure that the refresh token is not blacklisted (if a token is blacklisted, it is not going to be found on the database)
    # The expiration time is validated before this point
    user_tokens: list[type[models.RefreshTokens]] = (db_session.query(models.RefreshTokens)
                                                     .filter(models.RefreshTokens.user_id == user_id)
                                                     .all())
    for user_token in user_tokens:
        if user_token.refresh_token == refresh_token:
            return True
    return False


def create_jwt(user_data: dict, expires_delta: timedelta, db_session: Session, is_refresh_token: bool = False) -> str:
    # JWT PAYLOAD
    to_encode = {
        # Registered Claims
        'jti': str(uuid.uuid4()), # Universally Unique Identifier (UUID, 128-bit)
        'sub': user_data.get('username', ''),
        'exp': datetime.now(timezone.utc) + expires_delta,
        # Custom Claims
        'refresh': is_refresh_token,
        'user': user_data,
    }
    
    new_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # Adding refresh token to database
    if is_refresh_token:
        add_jwt_to_db(token=new_jwt, user_data=user_data, expires_at=to_encode.get('exp'), db_session=db_session)

    return new_jwt


def get_payload_from_jwt(token: str, db_session: Session) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError: # ExpiredSignatureError < DecodeError < InvalidTokenError < PyJWTError
        # If a refresh_token expires, it must be deleted from the database
        delete_jwt_from_db(token, db_session)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate token.")
    except jwt.PyJWTError as err: # PyJWTError < Exception
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate token. Error: {str(err)}")
    except Exception:
        raise


# Annotated[str, Depends(oauth2_bearer)] tells the application to get the token in the Authorization: Bearer <token> header
async def get_logged_in_user(access_token: Annotated[str, Depends(oauth2_bearer)], db_session: db_dependency):
    # Making sure that the token is a valid JWT
    try:
        payload = get_payload_from_jwt(access_token, db_session)
    except Exception:
        raise

    # Making sure that this is an ACCESS TOKEN, not a REFRESH TOKEN
    if payload.get('refresh'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Provide an access token")

    user_data: dict = payload.get('user')
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    return {
        'username': payload.get('sub'),
        'user_id': user_data.get('user_id'),
        'user_role': user_data.get('user_role')
    }


# Annotated[str, Depends(oauth2_bearer)] tells the application to get the token in the Authorization: Bearer <token> header
async def get_user_from_refresh_token(refresh_token: Annotated[str, Depends(oauth2_bearer)], db_session: db_dependency):
    # Making sure that the token is a valid JWT
    try:
        payload = get_payload_from_jwt(refresh_token, db_session)
    except Exception:
        raise

    # Making sure that this is a REFRESH TOKEN, not an ACCESS TOKEN
    if payload.get('refresh') is not True:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Provide a valid refresh token")

    user_data: dict = payload.get('user')
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    if is_valid_refresh_token(refresh_token, user_data.get('user_id'), db_session):
        delete_jwt_from_db(refresh_token, db_session)
        return user_data

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="An invalid refresh token was provided")
