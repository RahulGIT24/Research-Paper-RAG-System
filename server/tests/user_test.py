from .test_auth import get_authenticated_user
from .test_client import client


# ======================================
# GET CURRENT USER
# ======================================

def test_get_current_user_success():
    cookies = get_authenticated_user()

    response = client.get(
        "/api/v1/user/",
        cookies=cookies
    )

    assert response.status_code == 200

    data = response.json()

    assert "id" not in data
    assert "email" in data
    assert "name" in data
    assert data["name"] == "Rahul"


def test_get_current_user_unauthorized():
    response = client.get("/api/v1/user/")

    assert response.status_code == 401


def test_get_current_user_invalid_token():
    response = client.get(
        "/api/v1/user/",
        cookies={"access_token": "invalidtoken"}
    )

    assert response.status_code == 403
