from .db import Base
from sqlalchemy import Column, Integer, String, Boolean

class Todos(Base):
    __tablename__ = "todos"

    # Is index=True really necessary when we are defining a primary key?
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    completed = Column(Boolean, default=False)
