from io import BytesIO
from app.api.v1.endpoints.auth import SECRET_KEY, ALGORITHM
from .test_auth import create_user
from .test_client import client
import jwt
from datetime import datetime, timedelta

def fake_pdf():
    return ("test.pdf", BytesIO(b"%PDF-1.4 fake content"), "application/pdf")
def auth_headers(token: str):
    return {
        "Authorization": f"Bearer {token}"
    }

def get_authenticated_user():
    email, _ = create_user()

    verify_token = jwt.encode(
        {
            "email": email,
            "type": "verification",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    client.get(f"/api/v1/auth/verify?token={verify_token}")

    signin = client.post(
        "/api/v1/auth/signin",
        json={"email": email, "password": "StrongPassword123"}
    )
    return {"access_token":signin.cookies.get("access_token")}

def test_upload_pdf_success():
    email, _ = create_user()

    verify_token = jwt.encode(
        {
            "email": email,
            "type": "verification",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    client.get(f"/api/v1/auth/verify?token={verify_token}")

    signin = client.post(
        "/api/v1/auth/signin",
        json={"email": email, "password": "StrongPassword123"}
    )
    cookies = {
        "access_token": signin.cookies.get("access_token")
    }

    file_data = {
        "file": ("test.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")
    }

    response = client.post(
        "/api/v1/document/upload",
        files=file_data,
        cookies=cookies
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Document Submitted for processing"

def test_get_documents():
    cookies = get_authenticated_user()

    # upload one document first
    file_data = {
        "file": ("test.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")
    }

    client.post("/api/v1/document/upload", files=file_data, cookies=cookies)

    response = client.get(
        "/api/v1/document/",
        cookies=cookies,
        params={"page": 1, "limit": 10}
    )

    assert response.status_code == 200
    data = response.json()

    assert "documents" in data
    assert data["total"] >= 1
    assert len(data["documents"]) >= 1
    assert data["page"] == 1

def test_get_single_document():
    cookies = get_authenticated_user()

    file_data = {
        "file": ("test.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")
    }

    upload_res = client.post(
        "/api/v1/document/upload",
        files=file_data,
        cookies=cookies
    )

    assert upload_res.status_code == 200

    list_res = client.get("/api/v1/document/", cookies=cookies)
    doc_id = list_res.json()["documents"][0]["id"]

    response = client.get(
        f"/api/v1/document/{doc_id}",
        cookies=cookies
    )

    assert response.status_code == 200
    assert response.json()["id"] == doc_id
    assert "file_name" in response.json()

def test_get_document_not_found():
    cookies = get_authenticated_user()

    response = client.get(
        "/api/v1/document/sdklfhkjsdhf",
        cookies=cookies
    )

    assert response.status_code == 422

def test_delete_document():
    cookies = get_authenticated_user()

    file_data = {
        "file": ("test.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")
    }

    client.post(
        "/api/v1/document/upload",
        files=file_data,
        cookies=cookies
    )

    list_res = client.get("/api/v1/document/", cookies=cookies)
    doc_id = list_res.json()["documents"][0]["id"]

    response = client.delete(
        f"/api/v1/document/{doc_id}",
        cookies=cookies
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Document deleted successfully"

def test_delete_document_not_found():
    cookies = get_authenticated_user()

    response = client.delete(
        "/api/v1/document/dklsfjklsdjfs",
        cookies=cookies
    )

    assert response.status_code == 422