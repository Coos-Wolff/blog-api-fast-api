import random
import jwt
import pytest

from datetime import timedelta, datetime, timezone
from app import security
from app.config import settings

RANDOM_INT_MIN = 0
RANDOM_INT_MAX = 100_000_000

def test_hash_password_verifies_correct_password():
    password = "password1"
    hashed = security.hash_password(password=password)
    assert security.verify_password(password=password, hashed=hashed) is True

def test_hash_password_seventy_three_bytes():
    password_73_bytes = "K9#fX!m2Q9*wzP&L5vT_sY$1xB6Rj7cZ-eN4uA@hK3mW%oG8pD!qX9vF2bN7mK3s_jW8xC5eR"
    with pytest.raises(ValueError):
        security.hash_password(password=password_73_bytes)

def test_hash_password_seventy_two_bytes():
    password_72_bytes = "gX8$mQ2!vB7*pZ4_rN1xK9#wL5tY3eC6jF0sD7uA2hK8mW4oG9pB3qX1vF5bN6mK2s_jW7xC"
    hashed = security.hash_password(password_72_bytes)
    assert security.verify_password(password=password_72_bytes, hashed=hashed) is True

def test_hash_password_uses_random_salt():
    password = "password2"
    assert security.hash_password(password=password) != security.hash_password(password=password)

def test_verify_password_rejects_wrong_password():
    wrong_password = "Wrong Password"
    hashed = security.hash_password("password")
    assert security.verify_password(password=wrong_password, hashed=hashed) is False

def test_verify_password_invalid_hash():
    password = "password3"
    invalid_hashed = "$2z$10$abcdefghijklmnopqrstuvABCDEFGHIJKLMNOPQRSTUV12345"
    with pytest.raises(ValueError):
        security.verify_password(password=password, hashed=invalid_hashed)

def test_decode_token_rejects_invalid_token():
    not_a_real_token="Not.A.Real.Token"
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(token=not_a_real_token)

def test_decode_valid_token():
    user_id = create_user_id()
    access_token = build_test_token(user_id=user_id, secret=settings.jwt_secret_key, expire_minutes=100, payload_type="access")
    expected = security.decode_token(token=access_token)
    assert expected["type"] == "access"
    assert expected["sub"] == str(user_id)

def test_decode_token_expired_token():
    user_id = create_user_id()
    token_expired = build_test_token(user_id=user_id, secret=settings.jwt_secret_key, expire_minutes=-1, payload_type="access")
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_token(token=token_expired)

def test_decode_token_invalid_signature():
    user_id = create_user_id()
    access_token = build_test_token(user_id=user_id, secret="a-different-secret-than-the-app-uses", expire_minutes=100, payload_type="access")
    with pytest.raises(jwt.InvalidSignatureError):
        security.decode_token(token=access_token)

def test_decode_token_malformed_token():
    with pytest.raises(jwt.DecodeError):
        security.decode_token(token="this.is.garbage")

def test_create_access_token_valid():
    user_id = create_user_id()
    access_token = security.create_access_token(user_id=user_id)
    decoded = security.decode_token(token=access_token)
    assert decoded["sub"] == str(user_id)
    assert decoded["type"] == "access"

def test_create_refresh_token_valid():
    user_id = create_user_id()
    refresh_token = security.create_refresh_token(user_id=user_id)
    decoded = security.decode_token(refresh_token)
    assert decoded["sub"] == str(user_id)
    assert decoded["type"] == "refresh"

def build_test_token(user_id: int, secret, expire_minutes, payload_type) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=int(expire_minutes))
    payload = {"sub": str(user_id), "exp": expire, "type": payload_type}
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)

def create_user_id():
    return random.randint(RANDOM_INT_MIN, RANDOM_INT_MAX)