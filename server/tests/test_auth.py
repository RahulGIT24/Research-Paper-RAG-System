import jwt
import uuid

from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.endpoints.auth import SECRET_KEY, ALGORITHM

client = TestClient(app)


def random_email():
    return f"{uuid.uuid4()}@example.com"


def create_user():
    email = random_email()

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Rahul",
            "email": email,
            "password": "StrongPassword123"
        }
    )

    return email, response


# =========================================================
# SIGNUP TESTS
# =========================================================

def test_signup_success():
    email, response = create_user()

    assert response.status_code == 201

    data = response.json()

    assert data["message"] == "User created successfully"
    assert "user_id" in data
    assert data["email"] == email


def test_signup_duplicate_email():
    email, _ = create_user()

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Rahul",
            "email": email,
            "password": "StrongPassword123"
        }
    )

    assert response.status_code == 409
    assert response.json()["error"] == "User already exists"


# =========================================================
# SIGNIN TESTS
# =========================================================

def test_signin_unverified_user():
    email, _ = create_user()

    response = client.post(
        "/api/v1/auth/signin",
        json={
            "email": email,
            "password": "StrongPassword123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["message"]
        == "User not verified, verification email sent"
    )


def test_signin_wrong_password():
    email, _ = create_user()

    response = client.post(
        "/api/v1/auth/signin",
        json={
            "email": email,
            "password": "WrongPassword"
        }
    )

    assert response.status_code == 401


def test_signin_verified_user():
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

    client.get(
        f"/api/v1/auth/verify?token={verify_token}"
    )

    response = client.post(
        "/api/v1/auth/signin",
        json={
            "email": email,
            "password": "StrongPassword123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Logged In Successfully"

    # Cookies should exist
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


# =========================================================
# VERIFY ACCOUNT TESTS
# =========================================================

def test_verify_success():
    email, _ = create_user()

    token = jwt.encode(
        {
            "email": email,
            "type": "verification",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = client.get(
        f"/api/v1/auth/verify?token={token}"
    )

    assert response.status_code == 200

    assert (
        response.json()["message"]
        == "Account Verified Successfully!!"
    )


def test_verify_invalid_token():
    response = client.get(
        "/api/v1/auth/verify?token=invalidtoken"
    )

    assert response.status_code == 403


def test_verify_expired_token():
    email, _ = create_user()

    expired_token = jwt.encode(
        {
            "email": email,
            "type": "verification",
            "exp": datetime.utcnow() - timedelta(minutes=1)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = client.get(
        f"/api/v1/auth/verify?token={expired_token}"
    )

    assert response.status_code == 403

    assert (
        response.json()["error"]
        == "Token Expired"
    )


def test_verify_wrong_token_type():
    email, _ = create_user()

    wrong_token = jwt.encode(
        {
            "email": email,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = client.get(
        f"/api/v1/auth/verify?token={wrong_token}"
    )

    assert response.status_code in [401, 403]


# =========================================================
# REFRESH TOKEN TESTS
# =========================================================

def test_refresh_token_success():
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

    client.get(
        f"/api/v1/auth/verify?token={verify_token}"
    )

    signin_response = client.post(
        "/api/v1/auth/signin",
        json={
            "email": email,
            "password": "StrongPassword123"
        }
    )

    refresh_token = signin_response.cookies.get(
        "refresh_token"
    )

    response = client.post(
        "/api/v1/auth/refresh",
        cookies={
            "refresh_token": refresh_token
        }
    )

    assert response.status_code == 200

    assert (
        response.json()["message"]
        == "Tokens refreshed successfully"
    )

    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_refresh_token_invalid():
    response = client.post(
        "/api/v1/auth/refresh",
        cookies={
            "refresh_token": "invalidtoken"
        }
    )

    assert response.status_code == 401


def test_refresh_token_expired():
    email, _ = create_user()

    expired_refresh_token = jwt.encode(
        {
            "email": email,
            "type": "refresh",
            "exp": datetime.utcnow() - timedelta(minutes=1)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = client.post(
        "/api/v1/auth/refresh",
        cookies={
            "refresh_token": expired_refresh_token
        }
    )

    assert response.status_code == 401


# =========================================================
# FORGOT PASSWORD TESTS
# =========================================================

def test_forgot_password_success():
    email, _ = create_user()

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": email
        }
    )

    assert response.status_code == 200

    assert (
        response.json()["message"]
        == "Forgot password email sent successfully"
    )


def test_forgot_password_user_not_found():
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "nouser@example.com"
        }
    )

    assert response.status_code == 404


# =========================================================
# RESET PASSWORD TESTS
# =========================================================

def test_reset_password_success():
    email, _ = create_user()

    reset_token = jwt.encode(
        {
            "email": email,
            "type": "forgot_password",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": email
        }
    )

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewStrongPassword123"
        }
    )

    assert response.status_code == 200

    assert (
        response.json()["message"]
        == "Password reset successfully"
    )


def test_reset_password_invalid_token():
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "invalidtoken",
            "new_password": "NewStrongPassword123"
        }
    )

    assert response.status_code == 401


def test_reset_password_expired_token():
    email, _ = create_user()

    expired_token = jwt.encode(
        {
            "email": email,
            "type": "forgot_password",
            "exp": datetime.utcnow() - timedelta(minutes=1)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": expired_token,
            "new_password": "NewStrongPassword123"
        }
    )

    assert response.status_code == 401

    assert (
        response.json()["error"]
        == "Reset token expired"
    )


def test_reset_password_wrong_token_type():
    email, _ = create_user()

    wrong_token = jwt.encode(
        {
            "email": email,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": wrong_token,
            "new_password": "NewStrongPassword123"
        }
    )

    assert response.status_code == 401


def test_reset_password_user_not_found():
    token = jwt.encode(
        {
            "email": "nouser@example.com",
            "type": "forgot_password",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": token,
            "new_password": "NewStrongPassword123"
        }
    )

    assert response.status_code == 404