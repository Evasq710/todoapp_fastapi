from database import db
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from pydantic import BaseModel, Field

### USERS ###
class Users(db.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    hashed_password = Column(String) # password already hashed
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    # default -> client side (python) | server_default -> server side (database default)
    role = Column(String, default="user") # role: str, TODO: user roles as strings separated by spaces

    """
    SQLITE3 SCHEMA:
    CREATE TABLE users (
        id INTEGER NOT NULL,
        email VARCHAR,
        username VARCHAR,
        hashed_password VARCHAR,
        first_name VARCHAR,
        last_name VARCHAR,
        is_active BOOLEAN,
        role VARCHAR,
        PRIMARY KEY (id),
        UNIQUE (email),
        UNIQUE (username)
    );
    CREATE INDEX ix_users_id ON users (id);
    """

class UserValidator(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str = Field(min_length=6) # as plain text

    # This will be added to Swagger documentation > Request body > Example value
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "evasquez",
                "email": "elias@test.com",
                "first_name": "Elias",
                "last_name": "Vasquez",
                "password": "test1234"
            }
        }
    }

class UserVerification(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


### TOKENS ###
class RefreshTokens(db.Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey('users.id'), index=True)
    refresh_token = Column(String, index=True, unique=True)
    expires_at = Column(DateTime(timezone=True))

    """
    SQLITE3 SCHEMA:
    CREATE TABLE refresh_tokens (
        id INTEGER NOT NULL,
        user_id INTEGER,
        refresh_token VARCHAR,
        expires_at DATETIME,
        PRIMARY KEY (id),
        FOREIGN KEY(user_id) REFERENCES users (id)
    );
    CREATE INDEX ix_refresh_tokens_id ON refresh_tokens (id);
    CREATE UNIQUE INDEX ix_refresh_tokens_refresh_token ON refresh_tokens (refresh_token);
    CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id);
    """


class TokenResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str


### USERS ###
class Todos(db.Base):
    __tablename__ = "todos"

    # Is index=True really necessary when we are defining a primary key?
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    completed = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey('users.id'))

    """
    SQLITE3 SCHEMA:
    CREATE TABLE todos (
        id INTEGER NOT NULL,
        title VARCHAR,
        description VARCHAR,
        priority INTEGER,
        completed BOOLEAN,
        owner_id INTEGER,
        PRIMARY KEY (id),
        FOREIGN KEY(owner_id) REFERENCES users (id)
    );
    CREATE INDEX ix_todos_id ON todos (id);
    """


# TodoValidator inherits from BaseModel, in order to implement data validation
class TodoValidator(BaseModel):

    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(ge=1, le=5)
    completed: bool

