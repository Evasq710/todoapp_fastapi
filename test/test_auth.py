from fastapi.testclient import TestClient
from fastapi import status
from routers.auth import authenticate_user

# TODO: Implement here "tokens" tests

user = {
    "email": "test@email.com",
    "password": "test123",
    "phone_number": "+1 22 22 22",
    "first_name": "test_name",
    "last_name": "test_surname",
}

def test_create_user(client: TestClient, override_get_logged_in_user):
    user["username"] = override_get_logged_in_user.get("username")
    response = client.post("/auth/", json=user)
    assert response.status_code == status.HTTP_201_CREATED

def test_authenticate_user(override_get_db):
    non_existent_user = authenticate_user("Non_existent", "Does not matter", override_get_db)
    assert non_existent_user is None

    wrong_password = authenticate_user(user.get("username"), "Wrong password", override_get_db)
    assert wrong_password is None

    user_model = authenticate_user(user.get("username"), user.get("password"), override_get_db)
    assert user_model is not None
    assert user_model.username == user.get("username")
    assert user_model.email == user.get("email")

def test_login_tokens(client: TestClient):
    body = {"username": user.get("username"), "password": user.get("password")}
    response = client.post("/auth/login", data=body) # data, because we expect a FormData

    json_response = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert json_response.get("access_token") is not None
    assert json_response.get("refresh_token") is not None
    assert json_response.get("token_type") == "bearer"

    user["refresh_token"] = json_response["refresh_token"]
    user["access_token"] = json_response["access_token"]

def test_new_access_token(client: TestClient):
    response = client.get("/auth/refresh", headers={"Authorization": f"Bearer {user.get('refresh_token')}"})

    json_response = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert json_response.get("access_token") is not None
    assert json_response.get("refresh_token") is not None
    assert json_response.get("token_type") == "bearer"

    user["refresh_token"] = json_response["refresh_token"]
    user["access_token"] = json_response["access_token"]