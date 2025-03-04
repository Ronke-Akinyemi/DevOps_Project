
from utils.config import *
from email.message import EmailMessage
from loggers.logger import logger
import requests

async def send_sms_task(to:str, body:str):
    payload = {
                "to": to,
                "from": "N-Alert",
                "sms": body,
                "type": "plain",
                "channel": "dnd",
                "api_key": TERMII_API_KEY,
            }
    headers = {
    'Content-Type': 'application/json',
    }
    try:
        requests.request("POST", TERMII_BASE_URL, headers=headers, json=payload)
        logger.info(f"SMS sent to {to}")
    except BaseException:
        logger.info("Something went wrong while sending sms")