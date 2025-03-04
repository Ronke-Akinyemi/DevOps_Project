from fastapi import Depends, HTTPException, status
from db.database import Session, get_session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.token import decode_access_token
from db.models import Marketer
from sqlmodel import select

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_session)):
    """Get the currently authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = db.query(Marketer).filter(Marketer.email == username).first()
    print(user.id)
    if not user:
        raise credentials_exception
    return user
