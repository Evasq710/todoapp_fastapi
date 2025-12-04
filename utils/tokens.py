import os, uuid, jwt
from typing import Annotated, Union
from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status, Depends, Cookie, Response
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


def delete_jwt_from_db(db_session: Session, token: str = "", token_model: type[models.RefreshTokens] | None = None):
    if token != "":
        token_model = db_session.query(models.RefreshTokens).filter(models.RefreshTokens.refresh_token == token).first()

    if token_model is not None:
        db_session.delete(token_model)
        db_session.commit()


def is_valid_refresh_token(refresh_token: str, user_id: int, db_session: Session) -> type[models.RefreshTokens] | None:
    # Making sure that the refresh token is not blacklisted (if a token is blacklisted, it is not going to be found on the database)
    # The expiration time is validated before this point
    user_tokens: list[type[models.RefreshTokens]] = (db_session.query(models.RefreshTokens)
                                                     .filter(models.RefreshTokens.user_id == user_id)
                                                     .all())
    for user_token in user_tokens:
        if user_token.refresh_token == refresh_token:
            return user_token
    return None


def create_jwt(db_session: Session, user_data: dict, expires_delta: timedelta = None, is_refresh_token: bool = False, previous_expiry: datetime = None) -> str | tuple[str, datetime]:
    # Scenarios for JWTs creation:
    # 1. Access token..........: expires_delta:timedelta
    # 2. First refresh token...: expires_delta:timedelta, is_refresh_token=True
    # 3. Refresh token rotation: previous_expiry:timedelta, is_refresh_token=True
    if (expires_delta is None and previous_expiry is None) or \
       (expires_delta is not None and previous_expiry is not None) or \
       (expires_delta is None and is_refresh_token is False):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid JTW creation")

    # Preventing refresh token's lifetime extension beyond the lifetime of the initial refresh token
    exp: datetime = datetime.now(timezone.utc) + expires_delta if previous_expiry is None else previous_expiry

    # JWT PAYLOAD
    to_encode = {
        # Registered Claims
        'jti': str(uuid.uuid4()), # Universally Unique Identifier (UUID, 128-bit)
        'sub': user_data.get('username', ''),
        'exp': exp,
        # Custom Claims
        'refresh': is_refresh_token,
        'user': user_data,
    }
    
    new_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # Adding refresh token to database
    if is_refresh_token:
        add_jwt_to_db(token=new_jwt, user_data=user_data, expires_at=to_encode.get('exp'), db_session=db_session)
        # Returning the RT and its expiration datetime, in order to add it to the http-only cookie
        return new_jwt, exp

    return new_jwt


def get_payload_from_jwt(token: str, db_session: Session) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError: # ExpiredSignatureError < DecodeError < InvalidTokenError < PyJWTError
        # If a refresh_token expires, it must be deleted from the database
        delete_jwt_from_db(db_session=db_session, token=token)
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


# refresh_token: Annotated[Union[str, None], Cookie()] = None
#   - Reads a cookie named 'refresh_token' from the request
#   - If the cookie is not present, refresh_token will be None
async def get_payload_from_refresh_token(response: Response, db_session: db_dependency, refresh_token: Annotated[Union[str, None], Cookie()] = None):
    # Making sure that the 'refresh_token' cookie exists
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

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

    rt_object = is_valid_refresh_token(refresh_token, user_data.get('user_id'), db_session)

    if rt_object is not None:
        # Invalidating the used refresh token by deleting it from the database
        delete_jwt_from_db(db_session=db_session, token_model=rt_object)

        # TIMESTAMP is decoded as int, so we are changing it to datetime by getting it directly from the refresh token object
        # This expires_at claim will be used to rotate the refresh token with the same expiration time
        payload['exp'] = rt_object.expires_at
        return payload

    # At this point:
    # - A valid REFRESH TOKEN was received from the 'refresh_token' cookie
    # - The token is not listed as a valid JWT in our database (rt_object is None)
    # - This could happen if we explicitly delete a refresh token to invalidate it
    # - Deleting the http-only cookie:
    response.delete_cookie(key='refresh_token', path="/")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="An invalid refresh token was provided",
        headers={"Set-Cookie": response.headers.get('set-Cookie')},
    )
