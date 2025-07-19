
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt

from config import settings

def encode_jwt(
    payload: dict[str, Any],
    key: str = settings.jwt.PRIVATE_KEY.read_text(),
    algorithm: str = settings.jwt.ALGORITHM
) -> str:
    payload_copy = payload.copy()
    return jwt.encode(
        payload=payload_copy,
        key=key,
        algorithm=algorithm
    )

def decode_jwt(
    token: str | bytes,
    key: str = settings.jwt.PUBLIC_KEY.read_text(),
    algorithm: str = settings.jwt.ALGORITHM
) -> dict: 
    return jwt.decode(
        jwt=token,
        key=key,
        algorithms=[algorithm]
    )

def generate_tokens(user_id: int, role: str = 'user') -> tuple[str]:
    """Generate access and refresh tokens"""
    now = datetime.now(timezone.utc)
    access_payload: dict = {
        'user_id': user_id,
        'role': role,
        'exp': now + timedelta(minutes=settings.jwt.JWT_ACCESS_TOKEN_EXPIRES),
        'iat': now, 
        'type': 'access'
    }
    refresh_payload: dict = {
        'user_id': user_id,
        'role': role,
        'exp': now + timedelta(minutes=settings.jwt.JWT_REFRESH_TOKEN_EXPIRES),
        'iat': now, 
        'type': 'refresh',
    }

    access_token = encode_jwt(access_payload)
    refresh_token = encode_jwt(refresh_payload)

    return (access_token, refresh_token)

def verify_token(token: str, token_type: str = 'access') -> dict | None:
    """Verify JWT token"""
    try:
        payload: dict = decode_jwt(token)
        if payload.get('type') != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None