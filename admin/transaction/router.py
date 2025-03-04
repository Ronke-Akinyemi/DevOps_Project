from fastapi import APIRouter, Depends, HTTPException, status, Query
from db.database import AutomapBase, Session, get_session
from middlewares.auth import get_current_user, admin_role
from sqlmodel import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import Optional, Literal
from utils.pagination import CustomPagination, query_params, start_end_date_params
from transaction.serializer import TransactionResponse, MarketerResponse
from utils import CustomDateFormatting
from fastapi.encoders import jsonable_encoder
from uuid import UUID

transaction_router = APIRouter(
    prefix= "/api/v1/transaction",
    tags = ["transaction"]
)

@transaction_router.get("/referral/")
async def list_referrals(
    session: Session = Depends(get_session),
    auth: Session = Depends(admin_role),
    params: dict = Depends(query_params),
    start_end_date_params: dict = Depends(start_end_date_params)
):
    start_date = start_end_date_params.get("start_date")
    end_date = start_end_date_params.get("end_date")
    start_date, end_date, _ = CustomDateFormatting.start_end_date(start_date, end_date)
    
    Marketer = AutomapBase.classes.marketer
    User = AutomapBase.classes.User

    # Check if there's an actual relationship attribute (like 'user_collection' or similar)
    all_marketers = session.query(Marketer)
    search = params["search"]
    if search:
        search_query = f"%{search}%"
        all_marketers = all_marketers.filter(
            (Marketer.name.ilike(search_query)) |
            (Marketer.phone.ilike(search_query)) |
            (Marketer.email.ilike(search_query))
        )
    filter_marketters = len(all_marketers.filter(Marketer.created_at.between(start_date, end_date)).all())
    all_marketers = all_marketers.all()
    total_amount_paid = sum([m.balance for m in all_marketers])
    total_marketers = len(all_marketers)


    response_data = [
        {
            "id": marketer.id,
            "name": marketer.name,
            "phone": marketer.phone,
            "email": marketer.email,
            "no_of_merchants": session.query(User).filter(User.marketter_id == marketer.id).count(),  # Query manually
            "total_earning": getattr(marketer, "balance", 0)  # Handle missing balance field
        }
        for marketer in all_marketers
    ]
    total_amount_paid = sum([m.balance for m in all_marketers])
    
    return {
    "total_marketers": total_marketers,
    "filter_marketters": filter_marketters,  # Ensure filter_marketters is defined
    "total_amount_paid": total_amount_paid,
    "total_upcoming": 0,  # Keep as static if no calculation is provided
    "data": response_data
}


@transaction_router.get("/all/")
async def list_transactions(
    session: Session = Depends(get_session),
    auth: Session = Depends(admin_role),
    params: dict = Depends(query_params),
    type: Literal["SUBSCRIPTION", "REFERRAL"] = Query(None, description="Filter by type")
):
    Transaction = AutomapBase.classes.user_usersubscriptions
    User = AutomapBase.classes.User
    Plan = AutomapBase.classes.user_syncsubscription

    # Build query with joins
    transactions_query = session.query(
        Transaction,
        User.firstname,
        User.lastname,
        User.email,
        Plan.name.label("plan_name")
    ).join(User, Transaction.user_id == User.id).outerjoin(Plan, Transaction.plan_id == Plan.id).filter(Transaction.status == "SUCCESSFUL")

    if type:
        # Apply filtering logic if needed
        pass

    search = params["search"]
    if search:
        search_query = f"%{search}%"
        transactions_query = transactions_query.filter(
            (User.firstname.ilike(search_query)) |
            (User.lastname.ilike(search_query)) |
            (User.phone.ilike(search_query)) |
            (User.email.ilike(search_query))
        )

    # Execute query
    transactions = transactions_query.all()

    # Prepare response
    response_data = [
        TransactionResponse(
            id=transaction[0].id,  # Transaction is at index 0
            user=f"{transaction[1]} {transaction[2]}",  # User.firstname and User.lastname
            description=transaction[4],  # Plan.name (aliased as "plan_name")
            amount=transaction[0].amount,
            status=transaction[0].status,
            created_at=transaction[0].created_at
        )
        for transaction in transactions
    ]

    paginator = CustomPagination(params["page"] or 1, params["limit"] or 10)
    paginated_items = paginator.paginate(response_data)
    return paginator.get_paginated_response(jsonable_encoder(paginated_items), len(response_data))



@transaction_router.get("/single/{id}/")
async def single_user( id: UUID, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    Transaction = AutomapBase.classes.user_usersubscriptions
    User = AutomapBase.classes.User
    Plan = AutomapBase.classes.user_syncsubscription
    transaction = (
        session.query(
            Transaction,
            User.firstname,
            User.lastname,
            User.email,
            Plan.name.label("plan_name")
        )
        .join(User, Transaction.user_id == User.id)  # Join on user_id
        .outerjoin(Plan, Transaction.plan_id == Plan.id)  # Join on plan_id (if nullable)
        .filter(Transaction.id == id)  # Filter by Transaction ID
        .first()
    )

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    return TransactionResponse(
            id=transaction[0].id,  # Transaction is at index 0
            user=f"{transaction[1]} {transaction[2]}",  # User.firstname and User.lastname
            description=transaction[4],  # Plan.name (aliased as "plan_name")
            amount=transaction[0].amount,
            status=transaction[0].status,
            created_at=transaction[0].created_at
        )