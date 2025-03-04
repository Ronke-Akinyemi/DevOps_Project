from jose import jwt
from datetime import datetime, timedelta, timezone
from utils.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_REFRESH_SECRET_KEY


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create an access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict):
    """Create a refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str):
    """Decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.JWTError:
        return None
def decode_refresh_token(token: str):
    """Decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_REFRESH_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.JWTError:
        return None