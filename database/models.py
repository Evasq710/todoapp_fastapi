from .db import Base
from sqlalchemy import Column, Integer, String, Boolean
from pydantic import BaseModel, Field


class Todos(Base):
    __tablename__ = "todos"

    # Is index=True really necessary when we are defining a primary key?
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    completed = Column(Boolean, default=False)

# TodoValidator inherits from BaseModel, in order to implement data validation
class TodoValidator(BaseModel):

    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(ge=1, le=5)
    completed: bool

