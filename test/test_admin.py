from fastapi.testclient import TestClient
from fastapi import status

todo = {
    "title" : "Learn to code",
    "description" : "Need to learn everyday",
    "priority" : 5,
    "completed" : False,
    "owner_id" : 1,
}

def test_get_empty_todos(logged_in_admin_client: TestClient):
    response = logged_in_admin_client.get("/admin/todo")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_todo(logged_in_admin_client: TestClient):
    response = logged_in_admin_client.post("/todo/", json=todo)
    assert response.status_code == status.HTTP_201_CREATED

def test_get_all_todos(logged_in_admin_client: TestClient):
    todo["id"] = 1
    response = logged_in_admin_client.get("/admin/todo")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [todo]

def test_get_todos_unauthorized(logged_in_client: TestClient):
    response = logged_in_client.get("/admin/todo")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_delete_todo_unauthorized(logged_in_client: TestClient):
    response = logged_in_client.delete("/admin/todo/1")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_delete_todo(logged_in_admin_client: TestClient):
    response = logged_in_admin_client.delete("/admin/todo/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = logged_in_admin_client.get("/todo/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_todo_not_found(logged_in_admin_client: TestClient):
    response = logged_in_admin_client.delete("/admin/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_users_unauthorized(logged_in_client: TestClient):
    response = logged_in_client.get("/admin/user")
    assert response.status_code == status.HTTP_403_FORBIDDEN

