import uuid
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


# ======================================
# LIST CONVERSATIONS
# ======================================

def test_list_conversations_success():

    cookies = get_authenticated_user()

    client.post(
        "/api/v1/conversation/create",
        json={"name": "Listed Chat"},
        cookies=cookies
    )

    response = client.get(
        "/api/v1/conversation/",
        cookies=cookies
    )

    assert response.status_code == 200

    data = response.json()

    assert "conversations" in data
    assert len(data["conversations"]) >= 1
    assert any(c["name"] == "Listed Chat" for c in data["conversations"])


def test_list_conversations_only_returns_own():

    cookies_a = get_authenticated_user()
    cookies_b = get_authenticated_user()

    client.post(
        "/api/v1/conversation/create",
        json={"name": "User A Chat"},
        cookies=cookies_a
    )

    response = client.get(
        "/api/v1/conversation/",
        cookies=cookies_b
    )

    assert response.status_code == 200

    names = [c["name"] for c in response.json()["conversations"]]

    assert "User A Chat" not in names


def test_list_conversations_unauthorized():

    response = client.get("/api/v1/conversation/")

    assert response.status_code in [401, 403]


def test_list_conversations_pagination():

    cookies = get_authenticated_user()

    for i in range(3):
        client.post(
            "/api/v1/conversation/create",
            json={"name": f"Chat {i}"},
            cookies=cookies
        )

    response = client.get(
        "/api/v1/conversation/",
        cookies=cookies,
        params={"page": 1, "limit": 2}
    )

    assert response.status_code == 200
    assert len(response.json()["conversations"]) <= 2


# ======================================
# GET CONVERSATION MESSAGES
# ======================================

def test_get_messages_empty_conversation():

    cookies = get_authenticated_user()

    create_res = client.post(
        "/api/v1/conversation/create",
        json={"name": "Empty Chat"},
        cookies=cookies
    )
    conversation_id = create_res.json()["conversation_id"]

    response = client.get(
        "/api/v1/conversation/messages",
        params={"conversation_id": conversation_id},
        cookies=cookies
    )

    assert response.status_code == 200
    assert response.json()["messages"] == []


def test_get_messages_not_found():

    cookies = get_authenticated_user()

    response = client.get(
        "/api/v1/conversation/messages",
        params={"conversation_id": str(uuid.uuid4())},
        cookies=cookies
    )

    assert response.status_code == 404


def test_get_messages_of_another_users_conversation():

    cookies_a = get_authenticated_user()
    cookies_b = get_authenticated_user()

    create_res = client.post(
        "/api/v1/conversation/create",
        json={"name": "Private Chat"},
        cookies=cookies_a
    )
    conversation_id = create_res.json()["conversation_id"]

    response = client.get(
        "/api/v1/conversation/messages",
        params={"conversation_id": conversation_id},
        cookies=cookies_b
    )

    assert response.status_code == 404


def test_get_messages_unauthorized():

    response = client.get(
        "/api/v1/conversation/messages",
        params={"conversation_id": str(uuid.uuid4())}
    )

    assert response.status_code in [401, 403]