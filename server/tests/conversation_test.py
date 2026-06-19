from .test_auth import get_authenticated_user
from .test_client import client


# ======================================
# CREATE CONVERSATION SUCCESS
# ======================================

def test_create_conversation_success():

    cookies = get_authenticated_user()

    response = client.post(
        "/api/v1/conversation/create",
        json={
            "name": "My First Chat"
        },
        cookies=cookies
    )


    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Conversation created succcessfully"

    assert "conversation_id" in data

    assert data["conversation_id"] is not None



# ======================================
# CREATE WITHOUT AUTH
# ======================================

def test_create_conversation_unauthorized():

    response = client.post(
        "/api/v1/conversation/create",
        json={
            "name": "Test Chat"
        }
    )


    assert response.status_code in [
        401,
        403
    ]



# ======================================
# CREATE EMPTY NAME
# ======================================

def test_create_conversation_empty_name():

    cookies = get_authenticated_user()

    response = client.post(
        "/api/v1/conversation/create",
        json={
            "name": ""
        },
        cookies=cookies
    )


    # depends on your validation
    assert response.status_code in [
        200,
        400
    ]