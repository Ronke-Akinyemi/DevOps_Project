from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from loggers.logger import logger
from middlewares.logging import logging_middleware
from .routers import router


app = FastAPI()
app.include_router(router)
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)
logger.info('Starting API')

