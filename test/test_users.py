from fastapi.testclient import TestClient
from fastapi import status

user = {
    "email": "test@email.com",
    "password": "test123",
    "phone_number": "+1 22 22 22",
    "first_name": "test_name",
    "last_name": "test_surname",
}

def test_unexistent_user(logged_in_client: TestClient):
    response = logged_in_client.get("/user/")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_create_user(client: TestClient, override_get_logged_in_user):
    user["username"] = override_get_logged_in_user.get("username")
    response = client.post("/auth/", json=user)
    assert response.status_code == status.HTTP_201_CREATED

def test_get_user(logged_in_client: TestClient):
    user["id"] = 1
    response = logged_in_client.get("/user/")
    assert response.status_code == status.HTTP_200_OK

    json_response = response.json()
    assert json_response.get("username") == user.get("username")
    assert json_response.get("first_name") == user.get("first_name")
    assert json_response.get("last_name") == user.get("last_name")
    assert json_response.get("phone_number") == user.get("phone_number")
    assert json_response.get("email") == user.get("email")
    assert json_response.get("role") == "user"
    assert json_response.get("is_active") == True

def test_change_password(logged_in_client: TestClient):
    body = {
        "old_password": user.get("password"),
        "new_password": user.get("password") + "4",
    }
    response = logged_in_client.put("/user/change_password", json=body)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    user["password"] = body.get("new_password")

def test_change_password_invalid(logged_in_client: TestClient):
    body = {
        "old_password": "wrong password",
        "new_password": "does not matter"
    }
    response = logged_in_client.put("/user/change_password", json=body)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_change_phone_number(logged_in_client: TestClient):
    user["phone_number"] ="+1 33 33 33"
    response = logged_in_client.put("/user/change_phone_number", json={"phone_number": user.get("phone_number")})
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = logged_in_client.get("/user/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("phone_number") == user.get("phone_number")
