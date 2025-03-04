from fastapi import APIRouter, Depends, HTTPException, status
from db.database import  Session, get_session
from db.models import Marketer, MarketterPasswordResetToken
from sqlmodel import select, or_
from auth.serializers import (
    ResetPasswordRequest,
    VerifyPasswordResetToken,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangeDefaultPasswordRequest,
    ChangePasswordRequest,
    ForgetPasswordRequest,
    MarketerCreate,
    MarketerResponse
    )
from datetime import datetime, timezone, timedelta
import time
import secrets
import string
import base64
import random
from auth.token import create_access_token, create_refresh_token, decode_refresh_token
from utils import check_password
from middlewares.auth import get_current_user
from utils.config import NOTIFICATION_BASE_URL
from loggers.logging import logger
import requests


auth_router = APIRouter(
    prefix= "/api/v1/auth",
    tags = ["auth"]
)

@auth_router.post("/signup/", response_model=MarketerResponse)
async def sign_up(form_data: MarketerCreate, db: Session = Depends(get_session)):
    existing_marketer = db.exec(select(Marketer).where(or_(Marketer.email == form_data.email.lower(), Marketer.phone == form_data.phone))).first()
    
    if existing_marketer:
        if existing_marketer.email == form_data.email.lower():
            raise HTTPException(status_code=400, detail="Email already exists")
        elif existing_marketer.phone == form_data.phone:
            raise HTTPException(status_code=400, detail="Phone number already exists")
    check_password(form_data.password)
    hashed_password = Marketer.hash_password(form_data.password)
    referral_code = None
    while not referral_code:
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        existing_code = db.exec(select(Marketer).where(Marketer.referral_code == code)).first()
        if not existing_code:
            referral_code  = code
    new_user = Marketer(
        name=form_data.name,
        email=form_data.email.lower(),
        phone = form_data.phone,
        address = form_data.address,
        qualification= form_data.qualification,
        sales_experience = form_data.sales_experience,
        gender = form_data.gender,
        balance = 0,
        referral_code=referral_code,
        password = hashed_password
    )
    db.add(new_user)
    token = ''.join(random.choices('0123456789', k=6))
    token_expiry = datetime.now() + timedelta(minutes=10)
    new_password_reset = MarketterPasswordResetToken(
        user_id=new_user.id,
        token=token,
        expire= token_expiry,
        is_valid = True
        )
    db.add(new_password_reset)
    db.commit()
    url = f'{NOTIFICATION_BASE_URL}/send-email/'
    payload = {"email": form_data.email, "title": "Sync Verification token", "message": f"Your code is {token}. Valid for 10 minutes, one-time use only."}
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(url, headers=headers, json=payload)
    except BaseException as e:
        logger.error(f"Error sending email: {str(e)}")
    return new_user

@auth_router.post("/verify-email/")
async def verify_email(form_data: VerifyPasswordResetToken, db: Session = Depends(get_session)):
    user = db.query(Marketer).filter(Marketer.email == form_data.email.lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid User",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.password_reset:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Request for a password reset",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if (not user.password_reset.is_valid) or (user.password_reset.expire < datetime.now()) or (user.password_reset.token != form_data.token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token, Request for a password reset",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.password_reset.expire= datetime.now()
    user.password_reset.is_valid = False
    user.is_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"ref": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "name": user.name, "email": user.email}


@auth_router.post("/change-password/")
async def change_password(form_data: ChangePasswordRequest, db: Session = Depends(get_session), user: Session = Depends(get_current_user)):
    if not Marketer.verify_password(form_data.current_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    check_password(form_data.new_password)
    hashed_password = Marketer.hash_password(form_data.new_password)
    user.password = hashed_password
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "success"}

@auth_router.post("/forget-password/")
async def forget_password(form_data: ForgetPasswordRequest, db: Session = Depends(get_session)):
    user = db.query(Marketer).filter(Marketer.email == form_data.email.lower()).first()
    if not user:
        return {"message":"success"}
    token = ''.join(random.choices('0123456789', k=6))
    token_expiry = datetime.now() + timedelta(minutes=6)
    if user.password_reset:
        user.password_reset.token = token
        user.password_reset.expire= token_expiry
        user.password_reset.is_valid = True
        db.add(user.password_reset)
    else:
        new_password_reset = MarketterPasswordResetToken(
        user_id=user.id,
        token=token,
        expire= token_expiry,
        is_valid = True
        )
        db.add(new_password_reset)
    db.commit()
    url = f'{NOTIFICATION_BASE_URL}/send-email/'
    body = f'Your one time OTP is {token}, valid for 5 mins'
    payload = {"email": user.email, "title": "Password reset code", "message": body}
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(url, headers=headers, json=payload)
    except BaseException as e:
        logger.error(f"Error sending email: {str(e)}")
    return {"message":"success"}

@auth_router.post("/verify-password-token/")
async def verify_password_reset(form_data:VerifyPasswordResetToken, db: Session = Depends(get_session)):
    user = db.query(Marketer).filter(Marketer.email == form_data.email.lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid User",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.password_reset:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No pending password reset request",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if (not user.password_reset.is_valid) or (user.password_reset.expire < datetime.now()) or (user.password_reset.token != form_data.token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.password_reset.expire= datetime.now()
    user.password_reset.is_valid = False
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    timestamp = int(time.time())
    combined_value = f"{user_id}-{timestamp}"
    uid64 = base64.urlsafe_b64encode(combined_value.encode('utf-8')).decode('utf-8')
    return {"uid64":uid64}
@auth_router.post("/reset-password/")
async def reset_password(form_data:ResetPasswordRequest, db: Session=Depends(get_session)):
    try:
        decoded_value = base64.urlsafe_b64decode(form_data.uid64).decode('utf-8')
        user_id, timestamp = decoded_value.rsplit('-', 1)
    except BaseException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid User",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if int(timestamp) < int(time.time()) - 300 or int(timestamp) > int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Timeframe expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(Marketer).filter(Marketer.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid User",
            headers={"WWW-Authenticate": "Bearer"},
        )
    check_password(form_data.password)
    hashed_password = Marketer.hash_password(form_data.password)
    user.password = hashed_password
    user.is_default_password = False
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message":"success"}


@auth_router.post("/change-default-password/", response_model=TokenResponse)
async def change_default_password(form_data: ChangeDefaultPasswordRequest, db: Session = Depends(get_session)):
    user = db.query(Marketer).filter(Marketer.email == form_data.email.lower()).first()
    if not user or not Marketer.verify_password(form_data.default_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been suspended",
            headers={"WWW-Authenticate": "Bearer"},
        )

    check_password(form_data.password)
    hashed_password = Marketer.hash_password(form_data.password)
    user.last_login = datetime.now(timezone.utc)
    user.password = hashed_password
    user.is_default_password = False
    db.add(user)
    db.commit()
    db.refresh(user)
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"ref": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "name": user.name, "email": user.email}


@auth_router.post("/login/", response_model=TokenResponse)
async def login(form_data: LoginRequest , db: Session = Depends(get_session)):
    # Find user in the database
    user = db.query(Marketer).filter(Marketer.email == form_data.email.lower()).first()
    if not user or not Marketer.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verify your account first",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been suspended",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.is_default_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Change password to proceed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_login = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"ref": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "name": user.name, "email": user.email}

@auth_router.post("/refresh-token/", response_model=TokenResponse)
async def refresh_token(form_data:RefreshTokenRequest, db: Session = Depends(get_session)):
    payload = decode_refresh_token(form_data.refresh_token)
    credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload is None:
        raise credentials_exception
    username: str = payload.get("ref")
    if username is None:
        raise credentials_exception
    user = db.query(Marketer).filter(Marketer.email == username).first()
    if not user:
        raise credentials_exception
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"ref": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "name": user.name, "email": user.email}

@auth_router.post("/remove/")
async def remove_account(form_data: ForgetPasswordRequest, db: Session = Depends(get_session)):
    try:
        user = db.query(Marketer).filter(Marketer.email == form_data.email.lower()).first()
        if not user:
            return {"message": "marketter not found"}
        
        password_reset = user.password_reset
        if password_reset:
            db.delete(password_reset)
        db.delete(user)
        db.commit()
        return {"message": "success"}
    except Exception as e:
        db.rollback()
        return {"message": "An error occurred", "error": str(e)}