from fastapi import APIRouter, Depends, HTTPException, status
from db.database import AutomapBase, Session, get_session
from middlewares.auth import admin_role
from utils.pagination import CustomPagination, query_params
from subscription.serializers import PlanRequest, SinglePlanResponse, SinglePlanEditResponse
from fastapi.encoders import jsonable_encoder
from uuid import UUID
from datetime import datetime, timezone

subscription_router = APIRouter(
    prefix= "/api/v1/plans",
    tags = ["subscription"]
)




@subscription_router.get("/{id}/")
async def single_plan( id: int, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    SubscriptionPlans = AutomapBase.classes.user_syncsubscription
    plan = session.query(SubscriptionPlans).filter(SubscriptionPlans.id == id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    return SinglePlanResponse(
            id=plan.id,
            name=plan.name,
            monthly=plan.monthly,
            quarterly=plan.quarterly,
            biannually=plan.biannually,
            annually=plan.annually,
            no_of_users=plan.no_of_users,
            no_of_attendants = plan.no_of_attendants,
            no_of_business=plan.no_of_business
        )


@subscription_router.patch("/{id}/")
async def edit_plan( id: int, updated_data : SinglePlanEditResponse, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    SubscriptionPlans = AutomapBase.classes.user_syncsubscription
    plan = session.query(SubscriptionPlans).filter(SubscriptionPlans.id == id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    update_data = updated_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    session.commit()
    return SinglePlanResponse(
            id=plan.id,
            name=plan.name,
            monthly=plan.monthly,
            quarterly=plan.quarterly,
            biannually=plan.biannually,
            annually=plan.annually,
            no_of_users=plan.no_of_users,
            no_of_attendants = plan.no_of_attendants,
            no_of_business=plan.no_of_business
        )

@subscription_router.delete("/{id}/")
async def delete_plan( id: int, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    SubscriptionPlans = AutomapBase.classes.user_syncsubscription
    plan = session.query(SubscriptionPlans).filter(SubscriptionPlans.id == id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found")
    session.delete(plan)
    session.commit()
    return plan

@subscription_router.post("/")
async def new_plan(form_data: PlanRequest, session: Session = Depends(get_session), auth: Session = Depends(admin_role)):
    SubscriptionPlans = AutomapBase.classes.user_syncsubscription
    new_plan = SubscriptionPlans(
        name=form_data.name,
        monthly=form_data.monthly,
        quarterly=form_data.quarterly,
        biannually=form_data.biannually,
        annually=form_data.annually,
        no_of_users=form_data.no_of_users,
        no_of_attendants = form_data.no_of_attendants,
        no_of_business=form_data.no_of_business,
        created_at = datetime.now(timezone.utc),
        updated_at = datetime.now(timezone.utc)
    )
    session.add(new_plan)
    session.commit()
    session.refresh(new_plan)
    return SinglePlanResponse(
        id=new_plan.id,
        name=new_plan.name,
        monthly=new_plan.monthly,
        quarterly=new_plan.quarterly,
        biannually=new_plan.biannually,
        annually=new_plan.annually,
        no_of_users=new_plan.no_of_users,
        no_of_attendants = new_plan.no_of_attendants,
        no_of_business=new_plan.no_of_business
    )

@subscription_router.get("/")
async def all_plans(session: Session = Depends(get_session), auth: Session = Depends(admin_role), params: dict = Depends(query_params)):
    SubscriptionPlans = AutomapBase.classes.user_syncsubscription
    all_plans = session.query(SubscriptionPlans).order_by(SubscriptionPlans.created_at.desc()).all()
    response_data = [
        SinglePlanResponse(
            id=plan.id,
            name=plan.name,
            monthly=plan.monthly,
            quarterly=plan.quarterly,
            biannually=plan.biannually,
            annually=plan.annually,
            no_of_users=plan.no_of_users,
            no_of_attendants = plan.no_of_attendants,
            no_of_business=plan.no_of_business
        ) for plan in all_plans
    ]
    paginator = CustomPagination(params["page"] or 1, params["limit"] or 10)
    paginated_items = paginator.paginate(response_data)
    return paginator.get_paginated_response(jsonable_encoder(paginated_items), len(response_data))
