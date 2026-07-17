from io import BytesIO
from app.api.v1.endpoints.auth import SECRET_KEY, ALGORITHM
from .test_auth import create_user,get_authenticated_user
from .test_client import client
import uuid
import jwt
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas

def fake_pdf():
    buffer = BytesIO()

    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Hello world test PDF")
    c.save()

    buffer.seek(0)

    return (
        f"{uuid.uuid4()}.pdf",
        buffer,
        "application/pdf"
    )
def auth_headers(token: str):
    return {
        "Authorization": f"Bearer {token}"
    }

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
    "file": fake_pdf()
}

    response = client.post(
        "/api/v1/document/upload",
        files=file_data,
        cookies=cookies
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json()["message"] == "Document Submitted for processing"

def test_get_documents():
    cookies = get_authenticated_user()

    # upload one document first
    file_data = {
    "file": fake_pdf()
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
        "file": fake_pdf()
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
        "file": fake_pdf()
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
    print(response)

    assert response.status_code == 200
    assert response.json()["message"] == "Document deleted successfully"

def test_delete_document_not_found():
    cookies = get_authenticated_user()

    response = client.delete(
        "/api/v1/document/dklsfjklsdjfs",
        cookies=cookies
    )

    assert response.status_code == 422


# ======================================
# UPLOAD VALIDATION
# ======================================

def test_upload_invalid_extension():
    cookies = get_authenticated_user()

    file_data = {
        "file": (f"{uuid.uuid4()}.txt", BytesIO(b"just some text"), "text/plain")
    }

    response = client.post(
        "/api/v1/document/upload",
        files=file_data,
        cookies=cookies
    )

    assert response.status_code == 400
    assert "pdf" in response.json()["error"]


def test_upload_duplicate_document():
    cookies = get_authenticated_user()

    buffer = BytesIO()
    canvas.Canvas(buffer).save()
    buffer.seek(0)
    pdf_bytes = buffer.read()

    def file_data():
        return {
            "file": (f"{uuid.uuid4()}.pdf", BytesIO(pdf_bytes), "application/pdf")
        }

    first = client.post(
        "/api/v1/document/upload",
        files=file_data(),
        cookies=cookies
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/document/upload",
        files=file_data(),
        cookies=cookies
    )

    assert second.status_code == 400
    assert second.json()["error"] == "You already uploaded this document"


def test_upload_unauthorized():
    file_data = {
        "file": fake_pdf()
    }

    response = client.post(
        "/api/v1/document/upload",
        files=file_data
    )

    assert response.status_code == 401


# ======================================
# NOT FOUND WITH VALID UUID
# ======================================

def test_get_document_valid_uuid_not_found():
    cookies = get_authenticated_user()

    response = client.get(
        f"/api/v1/document/{uuid.uuid4()}",
        cookies=cookies
    )

    assert response.status_code == 404
    assert response.json()["error"] == "Document not found"


def test_delete_document_valid_uuid_not_found():
    cookies = get_authenticated_user()

    response = client.delete(
        f"/api/v1/document/{uuid.uuid4()}",
        cookies=cookies
    )

    assert response.status_code == 404
    assert response.json()["error"] == "Document not found"


# ======================================
# UNAUTHORIZED ACCESS
# ======================================

def test_get_documents_unauthorized():
    response = client.get("/api/v1/document/")

    assert response.status_code == 401


def test_get_document_unauthorized():
    response = client.get(f"/api/v1/document/{uuid.uuid4()}")

    assert response.status_code == 401


def test_delete_document_unauthorized():
    response = client.delete(f"/api/v1/document/{uuid.uuid4()}")

    assert response.status_code == 401


# ======================================
# VIEW UPLOADED DOCUMENT
# ======================================

def test_view_uploaded_document_success():
    cookies = get_authenticated_user()

    file_data = {
        "file": fake_pdf()
    }

    client.post(
        "/api/v1/document/upload",
        files=file_data,
        cookies=cookies
    )

    list_res = client.get("/api/v1/document/", cookies=cookies)
    server_file_name = list_res.json()["documents"][0]["server_file_name"]

    response = client.get(
        f"/api/v1/document/view/{server_file_name}",
        cookies=cookies
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_view_uploaded_document_not_found():
    cookies = get_authenticated_user()

    response = client.get(
        "/api/v1/document/view/does-not-exist.pdf",
        cookies=cookies
    )

    assert response.status_code == 404


def test_view_uploaded_document_of_another_user():
    cookies_owner = get_authenticated_user()
    cookies_other = get_authenticated_user()

    file_data = {
        "file": fake_pdf()
    }

    client.post(
        "/api/v1/document/upload",
        files=file_data,
        cookies=cookies_owner
    )

    list_res = client.get("/api/v1/document/", cookies=cookies_owner)
    server_file_name = list_res.json()["documents"][0]["server_file_name"]

    response = client.get(
        f"/api/v1/document/view/{server_file_name}",
        cookies=cookies_other
    )

    assert response.status_code == 404