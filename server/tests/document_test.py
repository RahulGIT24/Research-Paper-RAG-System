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

    cookies = signin.cookies

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