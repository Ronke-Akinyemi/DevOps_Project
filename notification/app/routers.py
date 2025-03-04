from fastapi import APIRouter, BackgroundTasks
from models import SendSms, EmailRequest, NotificationRequest, BulkNotificationRequest
from background_tasks import *
from loggers.logger import logger
from firebase import send_push_notification, send_bulk_push_notification


router = APIRouter()

@router.post("/send-email/")
async def send_email_endpoint(request: EmailRequest, background_tasks: BackgroundTasks):
    """API endpoint to send email asynchronously."""
    # Add email sending to the background task
    background_tasks.add_task(send_email_task, request.email, request.title, request.message)

    # Respond to the client immediately
    logger.info(f"Email sending initiated to {request.email}")
    return {"status": "Email sending initiated"}

@router.post('/send-sms/')
async def send_sms_endpoint(request: SendSms, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_sms_task, request.to, request.body)
    logger.info(f"Notification initiated to {request.to}")
    return {"status": "Notification initiated"}

@router.post("/send-notification/")
async def send_notification(notification: NotificationRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_push_notification, notification.token, notification.title, notification.body, notification.data)
    return {"status": "Notification initiated"}

@router.post("/send-bulk-notification/")
async def send_bulk_notification(notification: BulkNotificationRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_bulk_push_notification, notification.tokens, notification.title, notification.body, notification.data)
    return {"status": "Notification initiated"}