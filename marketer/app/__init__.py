from fastapi import FastAPI, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from loggers.logging import logger
from middlewares.logging import logging_middleware
from merchant.router  import merchant_router
# from .routers import router
from contextlib import asynccontextmanager
from db.database import init_db, get_session
from auth.router import auth_router
from db.models import *
from sqlmodel import Session
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


origins = [
    "https://sink-marketers.vercel.app",
    "https://www.sink-marketers.vercel.app",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://partners-api.sync360.africa",
    "https://www.partners-api.sync360.africa/",
    "https://sink-marketers.vercel.app/*",
]


app = FastAPI(lifespan=lifespan)
# app.include_router(router)
app.include_router(auth_router)
app.include_router(merchant_router)

app.add_middleware(CORSMiddleware, allow_origins=origins,
    allow_credentials=True,
    allow_methods= ["*"],
    allow_headers=["*"]

)
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)



logger.info('Starting API')
