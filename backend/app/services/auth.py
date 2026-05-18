import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from secrets import token_bytes
from typing import Any

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.orm.session import Session

from app.db.database import get_db
from app.db.models import User

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))
PASSWORD_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PASSWORD_ITERATIONS)
    return f'pbkdf2_sha256${PASSWORD_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}'


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected_digest = password_hash.split('$', 3)
    except ValueError:
        return False

    if algorithm != 'pbkdf2_sha256':
        return False

    salt_bytes = _b64decode(salt)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, int(iterations))
    return hmac.compare_digest(_b64encode(digest), expected_digest)


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'name': user.name,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return _encode_jwt(payload)


def get_current_user(
        authorization: str | None = Header(None),
        token: str | None = Query(None),
        db: Session = Depends(get_db),
) -> User:
    raw_token = token or _bearer_token(authorization)
    if not raw_token:
        raise _credentials_exception()

    try:
        payload = _decode_jwt(raw_token)
    except ValueError as exc:
        raise _credentials_exception() from exc

    subject = payload.get('sub')
    if not subject:
        raise _credentials_exception()

    try:
        user_id = int(subject)
    except ValueError as exc:
        raise _credentials_exception() from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise _credentials_exception()
    return user


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, credentials = authorization.partition(' ')
    if scheme.lower() != 'bearer' or not credentials:
        return None
    return credentials


def _encode_jwt(payload: dict[str, Any]) -> str:
    header = {'alg': JWT_ALGORITHM, 'typ': 'JWT'}
    signing_input = f'{_json_b64(header)}.{_json_b64(payload)}'
    signature = hmac.new(JWT_SECRET_KEY.encode('utf-8'), signing_input.encode('utf-8'), hashlib.sha256).digest()
    return f'{signing_input}.{_b64encode(signature)}'


def _decode_jwt(token: str) -> dict[str, Any]:
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError('Invalid token format')

    signing_input = f'{parts[0]}.{parts[1]}'
    expected_signature = hmac.new(JWT_SECRET_KEY.encode('utf-8'), signing_input.encode('utf-8'), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64encode(expected_signature), parts[2]):
        raise ValueError('Invalid token signature')

    payload = json.loads(_b64decode(parts[1]))
    expires_at = payload.get('exp')
    if not isinstance(expires_at, int) or datetime.now(timezone.utc).timestamp() > expires_at:
        raise ValueError('Token expired')
    return payload


def _json_b64(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(',', ':'), sort_keys=True).encode('utf-8')
    return _b64encode(raw)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def _b64decode(value: str) -> bytes:
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(f'{value}{padding}')


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
