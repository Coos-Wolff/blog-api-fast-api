from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import security
from app.config import settings
from tests.util_test import create_user_id

def build_test_token(user_id: int, secret, expire_minutes, payload_type) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=int(expire_minutes))
    payload = {"sub": str(user_id), "exp": expire, "type": payload_type}
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)

def test_hash_password_verifies_correct_password():
    password = "password1"
    hashed = security.hash_password(password=password)
    assert security.verify_password(password=password, hashed=hashed) is True

def test_hash_password_uses_random_salt():
    password = "password2"
    assert security.hash_password(password=password) != security.hash_password(password=password)

def test_hash_password_accepts_seventy_two_bytes():
    password_72_bytes = "gX8$mQ2!vB7*pZ4_rN1xK9#wL5tY3eC6jF0sD7uA2hK8mW4oG9pB3qX1vF5bN6mK2s_jW7xC"
    hashed = security.hash_password(password_72_bytes)
    assert security.verify_password(password=password_72_bytes, hashed=hashed) is True

def test_hash_password_rejects_seventy_three_bytes():
    password_73_bytes = "K9#fX!m2Q9*wzP&L5vT_sY$1xB6Rj7cZ-eN4uA@hK3mW%oG8pD!qX9vF2bN7mK3s_jW8xC5eR"
    with pytest.raises(ValueError):
        security.hash_password(password=password_73_bytes)

def test_verify_password_rejects_wrong_password():
    hashed = security.hash_password("password")
    assert security.verify_password(password="Wrong Password", hashed=hashed) is False

def test_verify_password_rejects_invalid_hash():
    invalid_hashed = "$2z$10$abcdefghijklmnopqrstuvABCDEFGHIJKLMNOPQRSTUV12345"
    with pytest.raises(ValueError):
        security.verify_password(password="password3", hashed=invalid_hashed)

def test_create_access_token_round_trips():
    user_id = create_user_id()
    token = security.create_access_token(user_id=user_id)
    decoded = security.decode_token(token=token)
    assert decoded["sub"] == str(user_id)
    assert decoded["type"] == "access"

def test_create_refresh_token_round_trips():
    user_id = create_user_id()
    token = security.create_refresh_token(user_id=user_id)
    decoded = security.decode_token(token=token)
    assert decoded["sub"] == str(user_id)
    assert decoded["type"] == "refresh"

def test_decode_token_accepts_valid_token():
    user_id = create_user_id()
    token = build_test_token(user_id=user_id, secret=settings.jwt_secret_key, expire_minutes=100, payload_type="access")
    decoded = security.decode_token(token=token)
    assert decoded["type"] == "access"
    assert decoded["sub"] == str(user_id)

def test_decode_token_rejects_expired_token():
    user_id = create_user_id()
    token = build_test_token(user_id=user_id, secret=settings.jwt_secret_key, expire_minutes=-1, payload_type="access")
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_token(token=token)

def test_decode_token_rejects_invalid_signature():
    user_id = create_user_id()
    token = build_test_token(user_id=user_id, secret="a-different-secret-than-the-app-uses", expire_minutes=100, payload_type="access")
    with pytest.raises(jwt.InvalidSignatureError):
        security.decode_token(token=token)

def test_decode_token_rejects_malformed_token():
    with pytest.raises(jwt.DecodeError):
        security.decode_token(token="this.is.garbage")

def test_decode_token_rejects_non_token_string():
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(token="Not.A.Real.Token")