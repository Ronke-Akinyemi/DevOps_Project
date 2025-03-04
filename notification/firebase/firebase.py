import firebase_admin
from firebase_admin import credentials, messaging
from loggers.logger import logger
from typing import List, Optional, Dict


cred = credentials.Certificate("./firebase-credentials.json")
firebase_admin.initialize_app(cred)



def send_push_notification(token: str, title: str, body: str, data: Optional[Dict[str, str]] = None):
    """
    Send a push notification to a specific device.

    Args:
        token (str): FCM device token.
        title (str): Notification title.
        body (str): Notification body.
        data (dict): Additional data payload (optional).
    """
    # Create a message
    try:
        # Create a message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )
        # Send the message
        response = messaging.send(message)
        logger.info(f"Notification sent successfully: {response}")
        return {"success": True, "message_id": response}
    except messaging.FirebaseError as e:
        logger.error(f"Failed to send notification: {e}")
        return {"success": False, "error": str(e)}

def send_bulk_push_notification(
    tokens: List[str], title: str, body: str, data: Optional[Dict[str, str]] = None
):
    if not tokens:
        logger.error("No tokens provided for bulk push notification.")
        return {"error": "No device tokens provided"}

    # Define the notification payload
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},  # Include custom data if provided
        tokens=tokens,
    )

    try:
        # Send the notifications
        response = messaging.send_multicast(message)

        # Log the overall response
        logger.info(f"Send result: {response}")

        # Handle errors and successes
        failed_tokens = []
        for idx, resp in enumerate(response.responses):
            if not resp.success:
                failed_tokens.append(tokens[idx])
                logger.error(f"Failed to send to {tokens[idx]}: {resp.exception}")

        return {
            "success_count": response.success_count,
            "failure_count": response.failure_count,
            "failed_tokens": failed_tokens,
        }
    except Exception as e:
        logger.exception(f"Error sending bulk notifications: {e}")
        return {"error": str(e)}