from fastapi.testclient import TestClient
from fastapi import status

todo = {
    "title" : "Learn to code",
    "description" : "Need to learn everyday",
    "priority" : 5,
    "completed" : False,
    "owner_id" : 1,
}

def test_empty_todos(logged_in_client: TestClient):
    response = logged_in_client.get("/todo/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_todo(logged_in_client: TestClient):
    response = logged_in_client.post("/todo/", json=todo)
    assert response.status_code == status.HTTP_201_CREATED

def test_read_all_authenticated(logged_in_client: TestClient):
    todo["id"] = 1
    response = logged_in_client.get("/todo/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [todo]

def test_read_one(logged_in_client: TestClient):
    response = logged_in_client.get("/todo/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == todo

def test_read_one_not_found(logged_in_client: TestClient):
    response = logged_in_client.get("/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_todo(logged_in_client: TestClient):
    todo["completed"] = True
    todo["priority"] = 3
    response = logged_in_client.put("/todo/1", json=todo)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = logged_in_client.get("/todo/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == todo

def test_update_todo_not_found(logged_in_client: TestClient):
    response = logged_in_client.put("/todo/999", json=todo)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_todo(logged_in_client: TestClient):
    response = logged_in_client.delete("/todo/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = logged_in_client.get("/todo/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_todo_not_found(logged_in_client: TestClient):
    response = logged_in_client.delete("/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
