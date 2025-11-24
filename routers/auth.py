import os, jwt
from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import models, db

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# Variables for JWTs creation
# openssl rand -hex 32 | pbcopy
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 15

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer is a security dependency that handles OAuth2 token authentication using the password flow.
# It tells the application to expect a token in the Authorization: Bearer <token> header
# It also configures the OpenAPI schema and documentation to include an "Authorize" button for testing.
# The tokenUrl specifies the endpoint where the client should send the username and password to obtain an access token.
# When a user interacts with the Swagger UI and enters their credentials, the OAuth2PasswordBearer logic uses this tokenUrl to send a POST request with those credentials to that specific endpoint to retrieve the bearer token.
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

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


def authenticate_user(username: str, password: str, db_session: Session) -> models.Users | None:
    user: models.Users | None = db_session.query(models.Users).filter(models.Users.username == username).first()
    if user is None or not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta) -> str:
    # JWT PAYLOAD
    to_encode = {
        'sub': username,
        'id': user_id,
        'role': role,
        # 'roles': " ".join(roles), # roles that were received in the form data
        'exp': datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Annotated[str, Depends(oauth2_bearer)] tells the application to get the token in the Authorization: Bearer <token> header
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None or user_role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

        return {'username': username, 'user_id': user_id, 'user_role': user_role}
    # except jwt.ExpiredSignatureError: # ExpiredSignatureError < DecodeError < InvalidTokenError < PyJWTError < Exception
    # except jwt.InvalidTokenError: # InvalidTokenError < PyJWTError < Exception
    except jwt.PyJWTError as err: # PyJWTError < Exception
        print('JWT Error:', str(err))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate token. Error: {str(err)}")
    except Exception as err:
        print('Unexpected Error:', str(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))


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
@router.post("/token", response_model=models.Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(db_session: db_dependency,
                                 form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # form_data: {'grant_type', 'username', 'password', 'scopes', 'client_id', 'client_secret'}

    if SECRET_KEY is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not validate credentials due to an internal error")

    user = authenticate_user(form_data.username, form_data.password, db_session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed authentication")

    # FLOW 1, ASSUMING THAT THE USER SEND THE ROLE(S) THROUGH THE FORM DATA
    # For this, we would have to add valid scopes to oauth2_bearer, in order to enable the scopes selection on the Swagger documentation
    """
    # Validating if user selected an unauthorized role
    user_roles = set(user.role.split(' ')) # user roles are divided by spaces
    form_scopes = set(form_data.scopes) # form_data.scopes come in the form of a list[str]
    if not form_scopes.issubset(user_roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role(s)")
    
    # create_access_token would need to receive the form_scopes set, to then send them in the JWT, separated by spaces 
    """

    # FLOW 2, SENDING THE ROLE THAT THE USER ALREADY HAS IN THE DATABASE
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    """
    Bearer Authentication:
    When a user or system presents a bearer token to access a resource, they don't need to provide any other form of identification.
    Whoever "bears" the token can access the associated resources, making it crucial to protect the token.
    """
    return {'access_token': token, 'token_type': 'bearer'}


