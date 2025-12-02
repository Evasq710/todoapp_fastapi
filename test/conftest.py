import os, pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient
from database import db
from utils import tokens
from main import app

SQLITE_TEST_DATABASE_URI = os.getenv("SQLITE_TEST_DATABASE_URI")

"""
FIXTURE SCOPES
- [SCOPE] : [EXECUTION] - [LIFETIME]
- function: Once per test function (default) - Destroyed at the end of each execution test
- class: Once per test class - Destroyed at the end of the last test in the class
- module: Once per test module (file) - Destroyed at the end of the last test in the module
- package: Once per test package - Destroyed at the end of the last test in the package
- session: Once for the entire test session - Destroyed at the end of the test session
"""

# If needed, will be executed only once for the entire TEST SESSION, returning always the same dictionary
# This functions mocks the get_logged_in_user function that looks for a valid JWT on the Authorization header
@pytest.fixture(scope="session")
def override_get_logged_in_admin():
    return {'username': 'evasq', 'user_id': 1, 'user_role': 'admin'}

@pytest.fixture(scope="session")
def override_get_logged_in_user():
    return {'username': 'evasq', 'user_id': 1, 'user_role': 'user'}

# Every TEST FILE will have a fresh test database at the beginning of its execution
@pytest.fixture(scope="module")
def override_get_db():
    engine = create_engine(
        SQLITE_TEST_DATABASE_URI,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db.Base.metadata.create_all(bind=engine)
    database_test_session= testing_session_local()
    try:
        yield database_test_session
    finally:
        database_test_session.close()
        # Drop tables after the execution of a TEST FILE
        db.Base.metadata.drop_all(bind=engine)

# Every TEST FUNCTION will have a fresh logged in TestClient
@pytest.fixture(scope="function")
def logged_in_client(override_get_db, override_get_logged_in_user):
    # If we were to do this override outside the fixture, override_get_db is already a function, so we can do a direct override:
    # > app.dependency_overrides[db.get_db] = override_get_db

    # Doing this inside the fixture, override_get_db and override_get_logged_in_user functions were already called
    # We use lambda so we can override a function with another one
    app.dependency_overrides[db.get_db] = lambda: override_get_db
    app.dependency_overrides[tokens.get_logged_in_user] = lambda: override_get_logged_in_user

    # At this point, our application has the new references for its dependencies

    # Returning a test client
    with TestClient(app) as cl:
        yield cl

    # Clear overrides after all tests in the MODULE (thanks to the scope)
    app.dependency_overrides.clear()

# Every TEST FUNCTION will have a fresh logged in TestClient
@pytest.fixture(scope="function")
def logged_in_admin_client(override_get_db, override_get_logged_in_admin):
    # If we were to do this override outside the fixture, override_get_db is already a function, so we can do a direct override:
    # > app.dependency_overrides[db.get_db] = override_get_db

    # Doing this inside the fixture, override_get_db and override_get_logged_in_admin functions were already called
    # We use lambda so we can override a function with another one
    app.dependency_overrides[db.get_db] = lambda: override_get_db
    app.dependency_overrides[tokens.get_logged_in_user] = lambda: override_get_logged_in_admin

    # At this point, our application has the new references for its dependencies

    # Returning a test client
    with TestClient(app) as cl:
        yield cl

    # Clear overrides after all tests in the MODULE (thanks to the scope)
    app.dependency_overrides.clear()

# Every TEST FUNCTION will have a fresh logged in TestClient
@pytest.fixture(scope="function")
def client(override_get_db):
    app.dependency_overrides[db.get_db] = lambda: override_get_db

    # At this point, our application has the new references for its dependencies
    # Returning a test client
    with TestClient(app) as cl:
        yield cl

    # Clear overrides after all tests in the MODULE (thanks to the scope)
    app.dependency_overrides.clear()
