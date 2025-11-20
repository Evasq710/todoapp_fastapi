from database import db
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from pydantic import BaseModel, Field


class Users(db.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    hashed_password = Column(String) # password already hashed
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)

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
    password: str # as plain text
    role: str


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

