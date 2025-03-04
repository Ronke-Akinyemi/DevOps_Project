from fastapi import APIRouter, Depends, HTTPException, status, Query
from db.database import AutomapBase, Session, get_session
from middlewares.auth import get_current_user, admin_role
from sqlmodel import select
from typing import Optional, Literal
from utils.pagination import CustomPagination, query_params
from partner.serializers import MarketersResponse, SingleMarketerResponse
from fastapi.encoders import jsonable_encoder
from merchant.serializers import UserResponse
from auth.serializers import SuspendUser
from uuid import UUID

partners_router = APIRouter(
    prefix= "/api/v1/partners",
    tags = ["partner"]
)


@partners_router.get("/users/")
async def list_partners(session: Session = Depends(get_session), auth: Session = Depends(admin_role), params: dict = Depends(query_params),plan: str = Query(None,description="Filter by plan")):
    Marketer = AutomapBase.classes.marketer
    marketers = session.query(Marketer).order_by(Marketer.created_at.desc())
    search = params["search"]
    if search:
        search_query = f"%{search}%"
        marketers = marketers.filter(
            (Marketer.name.ilike(search_query) | Marketer.phone.ilike(search_query)) | (Marketer.email.ilike(search_query))
        )
    marketers = marketers.all()
    response_data = [MarketersResponse(
        id=user.id, name=user.name,email=user.email,
        phone =user.phone,
        is_active=user.is_active, address=user.address,
        qualification=user.qualification,
        sales_experience = user.sales_experience,
        gender = user.gender,
        is_verified = user.is_verified,
        is_approved = user.is_approved,
        balance = user.balance,
        referral_code = user.referral_code,
        created_at=user.created_at
        ) for user in marketers]
    paginator = CustomPagination(params["page"] or 1, params["limit"] or 10)
    paginated_items = paginator.paginate(response_data)
    return paginator.get_paginated_response(jsonable_encoder(paginated_items), len(response_data))

@partners_router.get("/user/{id}/")
async def single_partner( id: UUID, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    Marketer = AutomapBase.classes.marketer
    marketer = session.query(Marketer).filter(Marketer.id == id).first()
    if not marketer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    User = AutomapBase.classes.User
    partners_customers = session.query(User).filter(User.marketter == marketer.referral_code).all()
    customers = [UserResponse(id=user.id, name=f"{user.firstname} {user.lastname}",email=user.email,
        phone =user.phone,is_active=user.is_active, subscription=user.subscription,
        subscription_start_date=user.subscription_date,
        subscription_end_date = user.subscription_end_date,
        created_at=user.created_at) for user in partners_customers]
    return SingleMarketerResponse(
        id=marketer.id, name=marketer.name,email=marketer.email,
        phone =marketer.phone,is_active=marketer.is_active, address=marketer.address,
        qualification=marketer.qualification,
        sales_experience = marketer.sales_experience,
        gender = marketer.gender,
        is_verified = marketer.is_verified,
        is_approved = marketer.is_approved,
        balance = marketer.balance,
        referral_code = marketer.referral_code,
        created_at=marketer.created_at,business=customers)

@partners_router.post("/suspend/{id}/")
async def suspend_partner( id: UUID,form_data:SuspendUser, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    Marketer = AutomapBase.classes.marketer
    marketer = session.query(Marketer).filter(Marketer.id == id).first()
    if not marketer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    marketer.is_active = True if form_data.status == False else True
    session.commit()
    return {"message": "success"}

@partners_router.get("/approve/{id}/")
async def approve_partner( id: UUID,session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    Marketer = AutomapBase.classes.marketer
    marketer = session.query(Marketer).filter(Marketer.id == id).first()
    if not marketer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    marketer.is_approved = True
    session.commit()
    return {"message": "success"}
