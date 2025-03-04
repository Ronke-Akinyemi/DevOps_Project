
from loggers.logger import logger
from fastapi import Request

async def logging_middleware(request: Request, call_next):
    # log_dict = {
    #     'url': request.url.path,
    #     'method': request.method
    # }
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response