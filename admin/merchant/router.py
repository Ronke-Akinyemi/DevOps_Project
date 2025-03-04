from fastapi import APIRouter, Depends, HTTPException, status, Query
from db.database import AutomapBase, Session, get_session
from middlewares.auth import get_current_user, admin_role
from sqlmodel import select
from typing import Optional, Literal
from auth.serializers import SuspendUser
from utils.pagination import CustomPagination, query_params
from merchant.serializers import UserResponse, SingleUserResponse, BusinessResponse
from fastapi.encoders import jsonable_encoder
from uuid import UUID

merchant_router = APIRouter(
    prefix= "/api/v1/merchant",
    tags = ["merchant"]
)


@merchant_router.get("/users/")
async def list_users(session: Session = Depends(get_session), auth: Session = Depends(admin_role), params: dict = Depends(query_params), plan: Literal["ALL","TRIAL", "STARTER", "SYNC-PLUS", "SYNC-PRO","EXPIRED"] = Query(None,description="Filter by plan name")):
    User = AutomapBase.classes.User
    SyncSubscription = AutomapBase.classes.user_syncsubscription
    users = session.query(User).filter(User.role == "OWNER").order_by(User.created_at.desc())
    if plan:
        if plan not in ["ALL", "EXPIRED"]:
            sub_plan = session.query(SyncSubscription).filter(SyncSubscription.name == plan).first()
            if sub_plan:
                users = users.filter(User.subscription == sub_plan.code)
        if plan == "EXPIRED":
            users = users.filter(User.is_subscribed.is_(False))
    search = params["search"]
    if search:
        search_query = f"%{search}%"
        users = users.filter(
            (User.firstname.ilike(search_query)) | (User.lastname.ilike(search_query) | User.phone.ilike(search_query)) | (User.email.ilike(search_query))
        )
    users = users.all()
    response_data = [UserResponse(
        id=user.id, name=f"{user.firstname} {user.lastname}",email=user.email,
        phone =user.phone,is_active=user.is_subscribed, subscription=user.subscription,
        subscription_start_date=user.subscription_date,
        subscription_end_date = user.subscription_end_date,
        created_at=user.created_at
        ) for user in users]
    paginator = CustomPagination(params["page"] or 1, params["limit"] or 10)
    paginated_items = paginator.paginate(response_data)
    return paginator.get_paginated_response(jsonable_encoder(paginated_items), len(response_data))

@merchant_router.get("/user/{id}/")
async def single_user( id: UUID, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    User = AutomapBase.classes.User
    user = session.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    Business = AutomapBase.classes.business_business
    user_business = session.query(Business).filter(Business.owner_id == user.id).all()
    businesses = [BusinessResponse(id=b.id, name=b.name, street = b.street) for b in user_business]
    return SingleUserResponse(
        id=user.id,firstname=user.firstname, lastname=user.lastname,
        phone=user.phone, email=user.email, profile_picture=user.profile_picture,is_active= user.is_active,
        subscription=user.subscription,
        subscription_start_date=user.subscription_date,
        subscription_end_date = user.subscription_end_date,
        created_at=user.created_at,business=businesses)

@merchant_router.post("/suspend/{id}/")
async def suspend_user( id: UUID, form_data:SuspendUser, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    User = AutomapBase.classes.User
    user = session.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = True if form_data.status == False else True
    session.commit()
    return {"message": "success"}

