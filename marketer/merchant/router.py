from fastapi import APIRouter, Depends, HTTPException, status, Query
from db.database import AutomapBase, Session, get_session
from middlewares.auth import get_current_user
from sqlmodel import select, case
from sqlalchemy import func
from utils import CustomDateFormatting
from typing import Optional, Literal
from utils.pagination import CustomPagination, query_params, start_end_date_params
from merchant.serializers import UserResponse, SingleUserResponse, BusinessResponse
from fastapi.encoders import jsonable_encoder
from uuid import UUID

merchant_router = APIRouter(
    prefix= "/api/v1/profile",
    tags = ["profile"]
)


@merchant_router.get("/users/")
async def list_users(session: Session = Depends(get_session), auth: Session = Depends(get_current_user), params: dict = Depends(query_params), plan: Literal["ALL", "TRIAL", "STARTER", "SYNC-PLUS", "SYNC-PRO","EXPIRED"] = Query(None,description="Filter by plan name")):
    User = AutomapBase.classes.User
    SyncSubscription = AutomapBase.classes.user_syncsubscription
    users = session.query(User).filter(User.role == "OWNER", User.marketer.has(referral_code=auth.referral_code)).order_by(User.created_at.desc())
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
async def single_user( id: UUID, session: Session = Depends(get_session), auth: Session = Depends(get_current_user)):
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



@merchant_router.get("/overview/")
async def get_earnings(db: Session = Depends(get_session), auth: Session = Depends(get_current_user),
                       start_end_date_params: dict = Depends(start_end_date_params)):
    MarketerCommission = AutomapBase.classes.user_marketercommision
    User = AutomapBase.classes.User
    start_date = start_end_date_params.get("start_date")
    end_date = start_end_date_params.get("end_date")
    start_date, end_date, _ = CustomDateFormatting.start_end_date(start_date, end_date)
    
    results = db.query(
        func.sum(MarketerCommission.amount).label('total_earnings'),
        func.sum(case((MarketerCommission.created_at.between(start_date, end_date), MarketerCommission.amount), else_=0)).label('period_earnings'),
        func.count(User.id).label('total_users'),
        func.count(case((User.created_at.between(start_date, end_date), User.id), else_=None)).label('period_users'),
        func.count(case((User.is_subscribed == True, User.id), else_=None)).label('total_subscribed_users'),
        func.count(case((User.is_subscribed == False, User.id), else_=None)).label('total_unsubscribed_users')
    ).join(User, MarketerCommission.marketer_id == User.marketter_id).filter(MarketerCommission.marketer.has(referral_code=auth.referral_code)).first()
    
    return {
        "total_earnings": results.total_earnings,
        "period_earnings": results.period_earnings,
        "total_users": results.total_users,
        "period_users": results.period_users,
        "total_subscribed_users": results.total_subscribed_users,
        "total_unsubscribed_users": results.total_unsubscribed_users
    }

@merchant_router.get("/earnings/")
async def get_earnings(db: Session = Depends(get_session), auth: Session = Depends(get_current_user)):
    MarketerCommission = AutomapBase.classes.user_marketercommision
    results = db.query(
        func.extract('year', MarketerCommission.created_at).label('year'),
        func.extract('month', MarketerCommission.created_at).label('month'),
        func.sum(MarketerCommission.amount).label('total_earnings')
    ).filter(MarketerCommission.marketer.has(referral_code=auth.referral_code)).group_by(
        func.extract('year', MarketerCommission.created_at),
        func.extract('month', MarketerCommission.created_at)
    ).all()

    earnings = []
    for result in results:
        earnings.append({
            'year': result.year,
            'month': result.month,
            'total_earnings': result.total_earnings
        })

    return earnings

