from fastapi import FastAPI, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from loggers.logging import logger
from middlewares.logging import logging_middleware
# from .routers import router
from contextlib import asynccontextmanager
from db.database import init_db, get_session, AutomapBase
from auth.router import auth_router
from merchant.router import merchant_router
from transaction.router import transaction_router
from subscription.router import subscription_router
from profile.router import profile_router
from partner.router import partners_router
from db.models import *
from sqlmodel import Session
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


origins = [
    "https://sink-web.netlify.app",
    "https://www.sink-web.netlify.app/",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://admin-api.sync360.africa/",
    "https://www.admin-api.sync360.africa/"
]

app = FastAPI(lifespan=lifespan)
# app.include_router(router)
app.include_router(auth_router)
app.include_router(merchant_router)
app.include_router(transaction_router)
app.include_router(subscription_router)
app.include_router(profile_router)
app.include_router(partners_router)

app.add_middleware(CORSMiddleware, allow_origins=origins,
    allow_credentials=True,
    allow_methods= ["*"],
    allow_headers=["*"]

)
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)



logger.info('Starting API')

# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the FastAPI Project!"}

# @app.get("/django-data/{table_name}")
# def get_django_table_data(table_name: str, session: Session = Depends(get_session)):
#     # Dynamically access the reflected table
#     ReflectedTable = AutomapBase.classes.get(table_name)
#     if not ReflectedTable:
#         return {"error": f"Table {table_name} not found"}
    
#     # Query the table
#     data = session.query(ReflectedTable).all()
#     return data