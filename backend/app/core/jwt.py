import uuid
from datetime import datetime, timedelta, timezone
import jwt
from pydantic import BaseModel

from .config import get_settings


class TokenPayload(BaseModel):
    sub: str
    email: str
    exp: datetime
    iat: datetime


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
        return TokenPayload(
            sub=str(decoded["sub"]),
            email=str(decoded["email"]),
            exp=datetime.fromtimestamp(decoded["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(decoded["iat"], tz=timezone.utc),
        )
    except jwt.PyJWTError as err:
        raise ValueError(f"Invalid or expired token: {err}") from err
