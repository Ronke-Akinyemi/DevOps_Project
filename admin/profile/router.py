from fastapi import APIRouter, Depends, HTTPException, status, Query
from db.database import AutomapBase, Session, get_session
from middlewares.auth import get_current_user, admin_role
from sqlmodel import select
from sqlalchemy import func
from typing import Optional, Literal
from utils.pagination import CustomPagination, query_params, start_end_date_params
from utils import CustomDateFormatting
from profile.serializers import AdminListResponse, AdminUpdateStaffRequest
from db.models import AdminUser
from auth.serializers import SuspendUser
from fastapi.encoders import jsonable_encoder
from uuid import UUID

profile_router = APIRouter(
    prefix= "/api/v1/profile",
    tags = ["profile"]
)


@profile_router.get("/staffs/")
async def list_staffs(session: Session = Depends(get_session), auth: Session = Depends(admin_role),params: dict = Depends(query_params), status: Literal["active", "inactive"] = Query(None,description="Filter by status")):
    users = session.query(AdminUser).order_by(AdminUser.created_at.desc())
    if status:
        if status.lower() == "active":
            users = users.filter(AdminUser.is_active==True)
        elif status.lower() == "inactive":
            users = users.filter(AdminUser.is_active==False)
    users = users.all()
    response_data = [AdminListResponse(
        id=user.id, firstname=user.firstname, lastname= user.lastname,email=user.email,
        is_active=user.is_active,
        role = user.role
        ) for user in users]
    paginator = CustomPagination(params["page"] or 1, params["limit"] or 10)
    paginated_items = paginator.paginate(response_data)
    return paginator.get_paginated_response(jsonable_encoder(paginated_items), len(response_data))

@profile_router.patch("/staff/{id}/")
async def single_staff(id: UUID,form_data: AdminUpdateStaffRequest, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    user = session.query(AdminUser).filter(AdminUser.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if form_data.status == "active":
        user.is_active = True
    elif form_data.status == "inactive":
        user.is_active = False
    if form_data.role:
        user.role = form_data.role
    session.commit()
    session.refresh(user)
    return AdminListResponse(
        id=user.id, firstname=user.firstname, lastname=user.lastname, email=user.email,
        is_active=user.is_active,
        role = user.role
        )


@profile_router.get("/overview/")
async def admin_overview(
    session: Session = Depends(get_session), 
    auth: Session = Depends(admin_role),
    params: dict = Depends(query_params), 
    start_end_date_params: dict = Depends(start_end_date_params)
):
    start_date = start_end_date_params.get("start_date")
    end_date = start_end_date_params.get("end_date")
    start_date, end_date, _ = CustomDateFormatting.start_end_date(start_date, end_date)

    user_usersubscriptions = AutomapBase.classes.user_usersubscriptions
    total_amount, total_subscriptions = session.query(
        func.coalesce(func.sum(user_usersubscriptions.amount), 0),
        func.count()
    ).filter(user_usersubscriptions.status == "SUCCESSFUL").first() 
    filtered_amount, filtered_subscriptions = session.query(
        func.coalesce(func.sum(user_usersubscriptions.amount), 0),
        func.count()
    ).filter(user_usersubscriptions.created_at.between(start_date, end_date), user_usersubscriptions.status == "SUCCESSFUL").first() 
    User = AutomapBase.classes.User
    total_owners = session.query(func.count()).filter(User.role == "OWNER").scalar()
    filtered_owners = session.query(func.count()).filter(
        User.role == "OWNER",
        User.created_at.between(start_date, end_date)
    ).scalar()

    return {
        "total_subscription_amount": total_amount,
        "filtered_subscription_amount": filtered_amount,
        "total_subscriptions": total_subscriptions,
        "filtered_subscriptions": filtered_subscriptions,
        "total_merchants": total_owners,
        "filtered_merchants": filtered_owners
    }
